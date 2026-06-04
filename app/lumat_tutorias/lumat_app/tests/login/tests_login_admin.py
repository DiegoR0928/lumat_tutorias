from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User, Group
from django.urls import reverse

from lumat_app.models import Alumno
from lumat_app.views import CustomLoginView


class CustomLoginViewSuccessUrlTestCase(TestCase):

    def setUp(self):
        self.factory = RequestFactory()

        self.grupo_docente, _ = Group.objects.get_or_create(name='Docente')
        self.grupo_alumno, _ = Group.objects.get_or_create(name='Alumno')

        self.user_alumno = User.objects.create_user(
            username='alumno_normal',
            password='password123',
            is_superuser=False,  # Explícito
            is_staff=False      # Explícito
        )
        self.user_alumno.groups.add(self.grupo_alumno)

        self.alumno = Alumno.objects.create(
            user=self.user_alumno,
            nombre="Alan",
            apellido_paterno="Brito",
            matricula="AL999",
            semestre="5"
        )

        self.user_admin = User.objects.create_superuser(
            username='admin_test',
            password='password123'
        )

    def test_get_success_url_usuario_normal_evalua_false_en_staff(self):
        view = CustomLoginView()

        request = self.factory.get(reverse('lumat_app:login'))
        request.user = self.user_alumno
        view.request = request
        # Ejecución del método
        url_resultado = view.get_success_url()

        url_esperada = reverse(
            'lumat_app:seminario_detalle', kwargs={'num': 5})
        self.assertEqual(url_resultado, url_esperada)

    def test_get_success_url_admin_redirige_a_unfold_admin(self):
        view = CustomLoginView()

        request = self.factory.get(reverse('lumat_app:login'))
        request.user = self.user_admin
        view.request = request

        url_resultado = view.get_success_url()
        self.assertEqual(url_resultado, '/admin/')
