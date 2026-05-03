from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from lumat_app.models import Docente, Comite


class TestCrearComiteAdminView(TestCase):

    def setUp(self):
        self.client = Client()

        # Usuario Administrador
        self.user_admin = User.objects.create_superuser(
            username='admin',
            password='testpass123'
        )

        # Usuario Normal
        self.user_normal = User.objects.create_user(
            username='alumno1',
            password='testpass123'
        )

        # NUEVO: Creamos 3 usuarios base para los docentes
        user_d1 = User.objects.create_user(
            username='docente_test1', password='123')
        user_d2 = User.objects.create_user(
            username='docente_test2', password='123')
        user_d3 = User.objects.create_user(
            username='docente_test3', password='123')

        # Asignamos esos usuarios al crear los Docentes
        self.docente1 = Docente.objects.create(user=user_d1)
        self.docente2 = Docente.objects.create(user=user_d2)
        self.docente3 = Docente.objects.create(user=user_d3)

        self.url_crear_comite = reverse('admin:lumat_app_comite_add')

    # --- Vista GET ---

    def test_get_crear_comite_admin_retorna_200(self):
        """Un superusuario debería poder cargar el formulario del admin."""
        self.client.login(username='admin', password='testpass123')
        response = self.client.get(self.url_crear_comite)
        self.assertEqual(response.status_code, 200)

    def test_crear_comite_usa_template_correcto(self):
        """Verifica que se use el template de creación del panel de
        administración."""
        self.client.login(username='admin', password='testpass123')
        response = self.client.get(self.url_crear_comite)
        # El admin de Django usa 'admin/change_form.html' para las
        # vistas de "add"
        self.assertTemplateUsed(response, 'admin/change_form.html')

    # --- Redirecciones ---

    def test_usuario_normal_redirige_a_admin_login(self):
        """Un usuario sin permisos debe ser redirigido a la página de
        login del admin."""
        self.client.login(username='alumno1', password='testpass123')
        response = self.client.get(self.url_crear_comite)

        # El admin redirige usando el parámetro '?next='
        expected_url = f'/admin/login/?next={self.url_crear_comite}'
        self.assertRedirects(response, expected_url)

    # --- Código HTTP y Creación Exitosa ---

    def test_creacion_exitosa_retorna_302(self):
        """Al crear un comité correctamente, el admin hace un redirect
        (302) al listado."""
        self.client.login(username='admin', password='testpass123')

        datos = {
            'tutor': self.docente1.id,
            'miembro1': self.docente2.id,
            'miembro2': self.docente3.id,
        }
        response = self.client.post(self.url_crear_comite, datos)

        # Verifica redirección exitosa
        self.assertEqual(response.status_code, 302)
        # Verifica que se guardó en la base de datos
        self.assertEqual(Comite.objects.count(), 1)

    # --- Mensajes (Validaciones del modelo) ---

    def test_docentes_repetidos_muestra_mensaje_error(self):
        """Si se envía el mismo docente, la vista no redirige (200) y
        muestra el error de validación."""
        self.client.login(username='admin', password='testpass123')

        datos = {
            'tutor': self.docente1.id,
            'miembro1': self.docente1.id,  # Duplicado intencionalmente
            'miembro2': self.docente2.id,
        }
        response = self.client.post(self.url_crear_comite, datos)

        # Al fallar la validación, Django vuelve a renderizar el formulario
        self.assertEqual(response.status_code, 200)

        # Verifica el mensaje de error que definimos en el clean() del modelo
        self.assertContains(
            response, 'Los tres docentes del comité deben ser distintos.')

        # Verifica que no se haya guardado nada
        self.assertEqual(Comite.objects.count(), 0)
