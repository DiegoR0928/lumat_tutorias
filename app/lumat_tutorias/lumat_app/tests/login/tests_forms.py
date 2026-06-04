from django.test import TestCase, Client
from django.urls import reverse
from django.contrib import auth
from django.contrib.auth.models import User, Group
# Asegúrate de importar tu modelo Alumno aquí
from lumat_app.models import Alumno


class TestLoginForm(TestCase):

    def setUp(self):
        self.client = Client()

        self.user_sin_grupo = User.objects.create_user(
            username='sin_grupo',
            password='testpass123'
        )

        self.grupo_docente = Group.objects.create(name='Docente')
        self.user_docente = User.objects.create_user(
            username='docente1',
            password='testpass123'
        )
        self.user_docente.groups.add(self.grupo_docente)

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

    # --- Autenticación ---

    def test_login_docente_autentica_correctamente(self):
        self.client.post(reverse('lumat_app:login'), {
            'username': 'docente1',
            'password': 'testpass123'
        })
        user = auth.get_user(self.client)
        self.assertTrue(user.is_authenticated)

    def test_login_alumno_autentica_correctamente(self):
        self.client.post(reverse('lumat_app:login'), {
            'username': 'alumno1',
            'password': 'testpass123'
        })
        user = auth.get_user(self.client)
        self.assertTrue(user.is_authenticated)

    def test_login_sin_grupo_autentica_correctamente(self):
        self.client.post(reverse('lumat_app:login'), {
            'username': 'sin_grupo',
            'password': 'testpass123'
        })
        user = auth.get_user(self.client)
        self.assertTrue(user.is_authenticated)

    # --- Usuario correcto ---

    def test_login_docente_es_el_usuario_correcto(self):
        self.client.post(reverse('lumat_app:login'), {
            'username': 'docente1',
            'password': 'testpass123'
        })
        user = auth.get_user(self.client)
        self.assertEqual(user.username, 'docente1')

    def test_login_alumno_es_el_usuario_correcto(self):
        self.client.post(reverse('lumat_app:login'), {
            'username': 'alumno1',
            'password': 'testpass123'
        })
        user = auth.get_user(self.client)
        self.assertEqual(user.username, 'alumno1')

    # --- Grupos ---

    def test_usuario_docente_pertenece_a_grupo_docente(self):
        self.client.post(reverse('lumat_app:login'), {
            'username': 'docente1',
            'password': 'testpass123'
        })
        user = auth.get_user(self.client)
        self.assertTrue(user.groups.filter(name='Docente').exists())

    def test_usuario_alumno_pertenece_a_grupo_alumno(self):
        self.client.post(reverse('lumat_app:login'), {
            'username': 'alumno1',
            'password': 'testpass123'
        })
        user = auth.get_user(self.client)
        self.assertTrue(user.groups.filter(name='Alumno').exists())

    # Redirecciones por Rol (Nuevos tests basados en tu CustomLoginView)

    # def test_login_docente_redirige_a_dashboard_docente(self):
    #     response = self.client.post(reverse('lumat_app:login'), {
    #         'username': 'docente1',
    #         'password': 'testpass123'
    #     })
    #     self.assertRedirects(response, reverse('lumat_app:docente_dashboard'))

    # def test_login_alumno_redirige_a_seminario_detalle_con_su_semestre(self):
    #     response = self.client.post(reverse('lumat_app:login'), {
    #         'username': 'alumno1',
    #         'password': 'testpass123'
    #     })
    #     # El alumno tiene asignado semestre=5 en el setUp
    #     url_esperada = reverse(
    #         'lumat_app:seminario_detalle', kwargs={'num': 5})
    #     self.assertRedirects(response, url_esperada)

    def test_login_sin_grupo_redirige_a_raiz(self):
        response = self.client.post(reverse('lumat_app:login'), {
            'username': 'sin_grupo',
            'password': 'testpass123'
        })
        self.assertRedirects(response, '/', target_status_code=200)

    # --- Casos negativos ---

    def test_password_incorrecto_no_autentica(self):
        self.client.post(reverse('lumat_app:login'), {
            'username': 'alumno1',
            'password': 'wrongpass'
        })
        user = auth.get_user(self.client)
        self.assertFalse(user.is_authenticated)

    def test_usuario_inexistente_no_autentica(self):
        self.client.post(reverse('lumat_app:login'), {
            'username': 'noexiste',
            'password': 'testpass123'
        })
        user = auth.get_user(self.client)
        self.assertFalse(user.is_authenticated)

    def test_usuario_y_password_incorrectos_no_autentica(self):
        self.client.post(reverse('lumat_app:login'), {
            'username': 'noexiste',
            'password': 'wrongpass'
        })
        user = auth.get_user(self.client)
        self.assertFalse(user.is_authenticated)

    # --- Campos vacíos ---

    def test_usuario_vacio_no_autentica(self):
        self.client.post(reverse('lumat_app:login'), {
            'username': '',
            'password': 'testpass123'
        })
        user = auth.get_user(self.client)
        self.assertFalse(user.is_authenticated)

    def test_password_vacio_no_autentica(self):
        self.client.post(reverse('lumat_app:login'), {
            'username': 'alumno1',
            'password': ''
        })
        user = auth.get_user(self.client)
        self.assertFalse(user.is_authenticated)

    def test_ambos_campos_vacios_no_autentica(self):
        self.client.post(reverse('lumat_app:login'), {
            'username': '',
            'password': ''
        })
        user = auth.get_user(self.client)
        self.assertFalse(user.is_authenticated)

    def test_payload_vacio_no_autentica(self):
        self.client.post(reverse('lumat_app:login'), {})
        user = auth.get_user(self.client)
        self.assertFalse(user.is_authenticated)
