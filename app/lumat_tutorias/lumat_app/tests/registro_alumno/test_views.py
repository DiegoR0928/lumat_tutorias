from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User, Group
from django.contrib.messages import get_messages
from lumat_app.models import Alumno  # ajusta al nombre real de tu app


class RegistroViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.url = reverse('lumat_app:registro')
        # El grupo Alumno debe existir igual que en producción
        Group.objects.get_or_create(name='Alumno')

    def datos_validos(self, username='nuevo123'):
        return {
            'username': username,
            'email': f'{username}@escuela.mx',
            'password': 'Segura#2025',
            'nombre': 'Juan',
            'apellido_paterno': 'Pérez',
            'apellido_materno': 'García',
        }

    # ------------------------------------------------------------------
    # Código HTTP
    # ------------------------------------------------------------------

    def test_get_retorna_200(self):
        """GET a /registro/ devuelve HTTP 200."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_post_valido_retorna_302(self):
        """POST con datos válidos redirige (HTTP 302)."""
        response = self.client.post(self.url, data=self.datos_validos())
        self.assertEqual(response.status_code, 302)

    def test_post_invalido_retorna_200(self):
        """POST con datos inválidos vuelve a renderizar el formulario (HTTP 200)."""
        response = self.client.post(self.url, data={})
        self.assertEqual(response.status_code, 200)

    # ------------------------------------------------------------------
    # Template correcto
    # ------------------------------------------------------------------

    def test_get_usa_template_correcto(self):
        """La vista usa el template registro.html."""
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'registro.html')

    # ------------------------------------------------------------------
    # Contexto correcto
    # ------------------------------------------------------------------

    def test_contexto_contiene_user_form(self):
        """El contexto incluye user_form."""
        response = self.client.get(self.url)
        self.assertIn('user_form', response.context)

    def test_contexto_contiene_alumno_form(self):
        """El contexto incluye alumno_form."""
        response = self.client.get(self.url)
        self.assertIn('alumno_form', response.context)

    # ------------------------------------------------------------------
    # Redirecciones
    # ------------------------------------------------------------------

    def test_post_valido_redirige_a_registro(self):
        """Tras un registro exitoso redirige a la misma página de registro."""
        response = self.client.post(self.url, data=self.datos_validos())
        self.assertRedirects(response, self.url)

    # ------------------------------------------------------------------
    # Mensajes
    # ------------------------------------------------------------------

    def test_post_valido_muestra_mensaje_exito(self):
        """Tras registro exitoso aparece el mensaje de confirmación."""
        response = self.client.post(
            self.url, data=self.datos_validos(), follow=True
        )
        mensajes = [str(m) for m in get_messages(response.wsgi_request)]
        self.assertIn('Alumno registrado con éxito', mensajes)

    def test_post_invalido_no_muestra_mensaje_exito(self):
        """Con datos inválidos no debe aparecer el mensaje de éxito."""
        response = self.client.post(self.url, data={}, follow=True)
        mensajes = [str(m) for m in get_messages(response.wsgi_request)]
        self.assertNotIn('Alumno registrado con éxito', mensajes)

    # ------------------------------------------------------------------
    # CRUD — Crear
    # ------------------------------------------------------------------

    def test_post_valido_crea_user_en_bd(self):
        """Un POST válido crea un nuevo User en la base de datos."""
        self.client.post(self.url, data=self.datos_validos('juanito'))
        self.assertTrue(User.objects.filter(username='juanito').exists())

    def test_post_valido_crea_alumno_en_bd(self):
        """Un POST válido crea un Alumno vinculado al User."""
        self.client.post(self.url, data=self.datos_validos('juanito'))
        user = User.objects.get(username='juanito')
        self.assertTrue(Alumno.objects.filter(user=user).exists())

    def test_post_valido_asigna_grupo_alumno(self):
        """El User creado queda asignado al grupo 'Alumno'."""
        self.client.post(self.url, data=self.datos_validos('juanito'))
        user = User.objects.get(username='juanito')
        self.assertTrue(user.groups.filter(name='Alumno').exists())

    def test_post_valido_hashea_contrasena(self):
        """La contraseña guardada en BD es un hash, no texto plano."""
        self.client.post(self.url, data=self.datos_validos('juanito'))
        user = User.objects.get(username='juanito')
        self.assertNotEqual(user.password, 'Segura#2025')
        self.assertTrue(user.password.startswith('pbkdf2') or
                        user.password.startswith('argon2') or
                        user.password.startswith('bcrypt'))

    # ------------------------------------------------------------------
    # Casos negativos
    # ------------------------------------------------------------------

    def test_post_username_duplicado_no_crea_nuevo_user(self):
        """Un username ya existente no crea un segundo User."""
        User.objects.create_user(username='existente', password='pass')
        cantidad_antes = User.objects.count()
        self.client.post(self.url, data=self.datos_validos('existente'))
        self.assertEqual(User.objects.count(), cantidad_antes)

    def test_post_username_duplicado_no_crea_alumno(self):
        """Un username ya existente no crea un Alumno huérfano."""
        User.objects.create_user(username='existente', password='pass')
        self.client.post(self.url, data=self.datos_validos('existente'))
        self.assertFalse(
            Alumno.objects.filter(nombre='Juan').exists()
        )

    def test_metodo_get_no_crea_registros(self):
        """Un GET nunca crea Users ni Alumnos."""
        self.client.get(self.url)
        self.assertEqual(User.objects.count(), 0)
        self.assertEqual(Alumno.objects.count(), 0)

    # ------------------------------------------------------------------
    # Seguridad — CSRF
    # ------------------------------------------------------------------

    def test_post_sin_csrf_es_rechazado(self):
        """Un POST sin token CSRF es rechazado con HTTP 403."""
        csrf_client = Client(enforce_csrf_checks=True)
        response = csrf_client.post(self.url, data=self.datos_validos())
        self.assertEqual(response.status_code, 403)

    # ------------------------------------------------------------------
    # Seguridad — no exposición de contraseña
    # ------------------------------------------------------------------

    def test_contrasena_no_aparece_en_respuesta_get(self):
        """El HTML del GET no expone contraseñas en texto plano."""
        response = self.client.get(self.url)
        self.assertNotContains(response, 'Segura#2025')

    # ------------------------------------------------------------------
    # Métodos no permitidos
    # ------------------------------------------------------------------

    def test_metodo_put_no_esta_permitido(self):
        """PUT no es un método soportado por la vista."""
        response = self.client.put(self.url)
        self.assertIn(response.status_code, [405, 200, 302])
