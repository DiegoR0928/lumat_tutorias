from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User, Group

from lumat_app.models import Alumno, Docente


class TestLoginView(TestCase):

    def setUp(self):
        self.client = Client()

        # Usuario docente
        self.grupo_docente = Group.objects.create(name='Docente')
        self.user_docente = User.objects.create_user(
            username='docente1',
            password='testpass123'
        )
        self.user_docente.groups.add(self.grupo_docente)

        # Usuario alumno
        self.grupo_alumno = Group.objects.create(name='Alumno')
        self.user_alumno = User.objects.create_user(
            username='alumno1',
            password='testpass123'
        )
        self.user_alumno.groups.add(self.grupo_alumno)
        self.alumno_perfil = Alumno.objects.create(
            user=self.user_alumno,
            semestre=5
        )

    # --- Vista GET ---

    def test_login_get_retorna_200(self):
        response = self.client.get(reverse('lumat_app:login'))
        self.assertEqual(response.status_code, 200)

    def test_login_usa_template_correcto(self):
        response = self.client.get(reverse('lumat_app:login'))
        self.assertTemplateUsed(response, 'login.html')

    def test_login_contexto_contiene_form(self):
        response = self.client.get(reverse('lumat_app:login'))
        self.assertIn('form', response.context)

    # --- Redirecciones ---

    def test_login_docente_redirige_a_docente(self):
        # 1. Usamos get_or_create para evitar el error UNIQUE si ya existía en el setUp
        usuario_django, created = User.objects.get_or_create(
            username='docente1')

        # Si se acaba de crear o si ya existía, asegúrate de que tenga la contraseña correcta
        usuario_django.set_password('testpass123')
        usuario_django.save()

        # 2. Asegurar que el grupo 'Docente' exista y el usuario pertenezca a él
        # (Vital para tu CustomLoginView)
        grupo_docente, _ = Group.objects.get_or_create(name='Docente')
        usuario_django.groups.add(grupo_docente)

        # 3. Crear el perfil Docente (usando get_or_create por si acaso)
        Docente.objects.get_or_create(
            user=usuario_django,
            defaults={
                'nombre': "Juan",
                'apellido_paterno': "Pérez",
                'apellido_materno': "López",
                'correo': "juan.perez@lumat.com",
                'firma': "firmas/firma_test.png"
            }
        )

        # 4. Ejecutar la petición POST al Login
        response = self.client.post(reverse('lumat_app:login'), {
            'username': 'docente1',
            'password': 'testpass123'
        })

        # 5. Verificar la redirección esperada por grupo
        url_esperada = reverse('lumat_app:docente_seminarios')
        self.assertRedirects(response, url_esperada)

    def test_login_alumno_redirige_a_alumno(self):
        response = self.client.post(reverse('lumat_app:login'), {
            'username': 'alumno1',
            'password': 'testpass123'
        })
        # Corregido: Usa la URL dinámica con el semestre ('num': 5)
        # definido en el setUp
        url_esperada = reverse(
            'lumat_app:seminario_detalle', kwargs={'num': 5})
        self.assertRedirects(response, url_esperada)

    # --- Código HTTP ---

    def test_login_exitoso_retorna_302(self):
        response = self.client.post(reverse('lumat_app:login'), {
            'username': 'docente1',
            'password': 'testpass123'
        })
        self.assertEqual(response.status_code, 302)

    def test_credenciales_invalidas_retorna_200(self):
        response = self.client.post(reverse('lumat_app:login'), {
            'username': 'alumno1',
            'password': 'wrongpass'
        })
        self.assertEqual(response.status_code, 200)

    # --- Mensajes ---

    def test_credenciales_invalidas_muestra_mensaje_error(self):
        response = self.client.post(reverse('lumat_app:login'), {
            'username': 'alumno1',
            'password': 'wrongpass'
        })
        self.assertContains(response, 'Credenciales inválidas')

    def test_usuario_inexistente_muestra_mensaje_error(self):
        response = self.client.post(reverse('lumat_app:login'), {
            'username': 'noexiste',
            'password': 'wrongpass'
        })
        self.assertContains(response, 'Credenciales inválidas')

    def test_campos_vacios_muestra_mensaje_error(self):
        response = self.client.post(reverse('lumat_app:login'), {
            'username': '',
            'password': ''
        })
        self.assertContains(response, 'Credenciales inválidas')
