from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User, Group


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
        response = self.client.post(reverse('lumat_app:login'), {
            'username': 'docente1',
            'password': 'testpass123'
        })
        self.assertRedirects(response, '/docente/')

    def test_login_alumno_redirige_a_alumno(self):
        response = self.client.post(reverse('lumat_app:login'), {
            'username': 'alumno1',
            'password': 'testpass123'
        })
        self.assertRedirects(response, '/alumno/')

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