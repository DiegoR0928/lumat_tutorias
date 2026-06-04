from django.test import TestCase
from django.contrib.auth.models import User, Group
from lumat_app.models import Alumno


class TestViewsPerfilAlumno(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='prueba',
            password='amer1234',
            email='juan@test.com'
        )

        self.group = Group.objects.create(name='Alumno')
        self.user.groups.add(self.group)

        # Crear alumno asociado con el mismo correo inicial
        self.alumno = Alumno.objects.create(
            user=self.user,
            nombre='Juan',
            apellido_paterno='Perez',
            apellido_materno='Lopez',
            matricula='123',
            correo='juan@test.com'  # Mismo correo
        )

    def test_perfil_alumno_get(self):
        self.client.login(username='prueba', password='amer1234')

        response = self.client.get('/alumno/perfil/')
        self.assertEqual(response.status_code, 200)

    def test_perfil_modo_edicion(self):
        self.client.login(username='prueba', password='amer1234')

        response = self.client.get('/alumno/perfil/?modo=perfil')
        self.assertEqual(response.status_code, 200)

    def test_actualizar_perfil(self):
        self.client.login(username='prueba', password='amer1234')

        data = {
            'accion': 'perfil',
            'nombre': 'Carlos',
            'apellido_paterno': 'Perez',
            'apellido_materno': 'Lopez',
            'matricula': '999',
            'correo': 'carlos@test.com'
        }

        self.client.post('/alumno/perfil/', data=data)

        self.alumno.refresh_from_db()
        self.assertEqual(self.alumno.nombre, 'Carlos')
        self.assertEqual(self.alumno.matricula, '999')

        # El User de Django debió sincronizarse con el nuevo correo
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, 'carlos@test.com')

    def test_actualizar_perfil_mismo_correo(self):
        self.client.login(username='prueba', password='amer1234')

        data = {
            'accion': 'perfil',
            'nombre': 'Juan Modificado',
            'apellido_paterno': 'Perez',
            'apellido_materno': 'Lopez',
            'matricula': '123',
            'correo': 'juan@test.com'
        }

        response = self.client.post('/alumno/perfil/', data=data)

        # Al ser un envío válido, debe redirigir (HTTP 302)
        self.assertEqual(response.status_code, 302)

        self.alumno.refresh_from_db()
        self.assertEqual(self.alumno.nombre, 'Juan Modificado')

    def test_actualizar_perfil_invalido(self):
        self.client.login(username='prueba', password='amer1234')

        data = {
            'accion': 'perfil',
            'nombre': '',
            'apellido_paterno': 'Perez',
            'apellido_materno': 'Lopez',
            'matricula': '999'
        }

        response = self.client.post('/alumno/perfil/', data=data)

        self.assertEqual(response.status_code, 200)

    def test_cambiar_password(self):
        self.client.login(username='prueba', password='amer1234')

        data = {
            'accion': 'password',
            'old_password': 'amer1234',
            'new_password1': 'Nueva1234!',
            'new_password2': 'Nueva1234!'
        }

        self.client.post('/alumno/perfil/', data=data)

        # Verificar que la contraseña cambió
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('Nueva1234!'))

    def test_cambiar_password_incorrecta(self):
        self.client.login(username='prueba', password='amer1234')

        data = {
            'accion': 'password',
            'old_password': 'incorrecta',
            'new_password1': 'Nueva1234!',
            'new_password2': 'Nueva1234!'
        }

        self.client.post('/alumno/perfil/', data=data)

        # No debe cambiar contraseña
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('amer1234'))
