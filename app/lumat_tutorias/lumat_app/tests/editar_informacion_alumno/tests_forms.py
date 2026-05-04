from django.test import TestCase
# ajusta al nombre real
from lumat_app.forms import AlumnoEditForm, PasswordChangeCustomForm
from django.contrib.auth.models import User


class AlumnoEditFormTests(TestCase):

    def setUp(self):
        self.datos_validos = {
            'matricula': '87654321',
            'nombre': 'Juan',
            'apellido_paterno': 'Pérez',
            'apellido_materno': 'López',
            'semestre': '4',
            'correo': 'nuevo@uaz.edu.mx'
        }

    # --- Datos válidos ---

    def test_form_datos_validos_es_valido(self):
        form = AlumnoEditForm(data=self.datos_validos)
        self.assertTrue(form.is_valid())

    # --- Campos obligatorios ---

    def test_form_nombre_obligatorio(self):
        datos = {**self.datos_validos, 'nombre': ''}
        form = AlumnoEditForm(data=datos)
        self.assertFalse(form.is_valid())
        self.assertIn('nombre', form.errors)

    def test_form_apellido_paterno_obligatorio(self):
        datos = {**self.datos_validos, 'apellido_paterno': ''}
        form = AlumnoEditForm(data=datos)
        self.assertFalse(form.is_valid())
        self.assertIn('apellido_paterno', form.errors)

    def test_form_apellido_materno_obligatorio(self):
        datos = {**self.datos_validos, 'apellido_materno': ''}
        form = AlumnoEditForm(data=datos)
        self.assertFalse(form.is_valid())
        self.assertIn('apellido_materno', form.errors)

    def test_form_correo_obligatorio(self):
        datos = {**self.datos_validos, 'correo': ''}
        form = AlumnoEditForm(data=datos)
        self.assertFalse(form.is_valid())
        self.assertIn('correo', form.errors)

    # --- Datos inválidos ---

    def test_form_correo_invalido(self):
        datos = {**self.datos_validos, 'correo': 'correo_invalido'}
        form = AlumnoEditForm(data=datos)
        self.assertFalse(form.is_valid())
        self.assertIn('correo', form.errors)

    def test_form_matricula_excede_longitud(self):
        datos = {**self.datos_validos,
                 'matricula': '123456789'}  # 9 chars, máx 8
        form = AlumnoEditForm(data=datos)
        self.assertFalse(form.is_valid())
        self.assertIn('matricula', form.errors)


class PasswordChangeFormTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='alumno1', password='testpass123'
        )

    def test_password_form_valido(self):
        form = PasswordChangeCustomForm(user=self.user, data={
            'old_password': 'testpass123',
            'new_password1': 'NuevoPass456!',
            'new_password2': 'NuevoPass456!'
        })
        self.assertTrue(form.is_valid())

    def test_password_actual_incorrecto(self):
        form = PasswordChangeCustomForm(user=self.user, data={
            'old_password': 'incorrecta',
            'new_password1': 'NuevoPass456!',
            'new_password2': 'NuevoPass456!'
        })
        self.assertFalse(form.is_valid())
        self.assertIn('old_password', form.errors)

    def test_passwords_nuevos_no_coinciden(self):
        form = PasswordChangeCustomForm(user=self.user, data={
            'old_password': 'testpass123',
            'new_password1': 'NuevoPass456!',
            'new_password2': 'OtroPass789!'
        })
        self.assertFalse(form.is_valid())
        self.assertIn('new_password2', form.errors)

    def test_password_nuevo_muy_corto(self):
        form = PasswordChangeCustomForm(user=self.user, data={
            'old_password': 'testpass123',
            'new_password1': '123',
            'new_password2': '123'
        })
        self.assertFalse(form.is_valid())
