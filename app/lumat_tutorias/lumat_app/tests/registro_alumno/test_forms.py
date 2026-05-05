from django.test import TestCase
from django.contrib.auth.models import User
from lumat_app.forms import UserForm, AlumnoForm  # ajusta al nombre real de tu app


class UserFormTest(TestCase):

    # ------------------------------------------------------------------
    # Datos válidos
    # ------------------------------------------------------------------

    def test_user_form_valido_con_datos_correctos(self):
        """UserForm es válido cuando todos los campos son correctos."""
        form = UserForm(data={
            'username': 'nuevouser',
            'email': 'nuevo@escuela.mx',
            'password': 'Segura#2025',
        })
        self.assertTrue(form.is_valid())

    def test_user_form_valido_sin_email(self):
        """UserForm acepta envíos sin email porque el campo no es obligatorio."""
        form = UserForm(data={
            'username': 'nuevouser',
            'email': '',
            'password': 'Segura#2025',
        })
        self.assertTrue(form.is_valid())

    # ------------------------------------------------------------------
    # Campos obligatorios
    # ------------------------------------------------------------------

    def test_user_form_invalido_sin_username(self):
        """UserForm rechaza el envío si falta el username."""
        form = UserForm(data={
            'username': '',
            'email': 'nuevo@escuela.mx',
            'password': 'Segura#2025',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('username', form.errors)

    def test_user_form_invalido_sin_password(self):
        """UserForm rechaza el envío si falta la contraseña."""
        form = UserForm(data={
            'username': 'nuevouser',
            'email': 'nuevo@escuela.mx',
            'password': '',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('password', form.errors)

    # ------------------------------------------------------------------
    # Datos inválidos
    # ------------------------------------------------------------------

    def test_user_form_invalido_con_email_mal_formado(self):
        """UserForm rechaza emails que no tienen formato válido."""
        form = UserForm(data={
            'username': 'nuevouser',
            'email': 'esto-no-es-un-email',
            'password': 'Segura#2025',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

    def test_user_form_invalido_con_username_duplicado(self):
        """UserForm rechaza un username que ya existe en la base de datos."""
        User.objects.create_user(username='existente', password='pass')
        form = UserForm(data={
            'username': 'existente',
            'email': 'otro@escuela.mx',
            'password': 'Segura#2025',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('username', form.errors)

    # ------------------------------------------------------------------
    # Mensajes de error
    # ------------------------------------------------------------------

    def test_user_form_mensaje_error_username_duplicado(self):
        """El error de username duplicado contiene un mensaje descriptivo."""
        User.objects.create_user(username='existente', password='pass')
        form = UserForm(data={
            'username': 'existente',
            'email': 'otro@escuela.mx',
            'password': 'Segura#2025',
        })
        form.is_valid()
        errores = form.errors['username']
        self.assertTrue(any(len(e) > 0 for e in errores))


class AlumnoFormTest(TestCase):

    # ------------------------------------------------------------------
    # Datos válidos
    # ------------------------------------------------------------------

    def test_alumno_form_valido_con_datos_correctos(self):
        """AlumnoForm es válido cuando todos los campos están completos."""
        form = AlumnoForm(data={
            'nombre': 'Juan',
            'apellido_paterno': 'Pérez',
            'apellido_materno': 'García',
        })
        self.assertTrue(form.is_valid())

    # ------------------------------------------------------------------
    # Campos obligatorios
    # ------------------------------------------------------------------

    def test_alumno_form_invalido_sin_nombre(self):
        """AlumnoForm rechaza el envío si falta el nombre."""
        form = AlumnoForm(data={
            'nombre': '',
            'apellido_paterno': 'Pérez',
            'apellido_materno': 'García',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('nombre', form.errors)

    def test_alumno_form_invalido_sin_apellido_paterno(self):
        """AlumnoForm rechaza el envío si falta el apellido paterno."""
        form = AlumnoForm(data={
            'nombre': 'Juan',
            'apellido_paterno': '',
            'apellido_materno': 'García',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('apellido_paterno', form.errors)

    def test_alumno_form_invalido_sin_apellido_materno(self):
        """AlumnoForm rechaza el envío si falta el apellido materno."""
        form = AlumnoForm(data={
            'nombre': 'Juan',
            'apellido_paterno': 'Pérez',
            'apellido_materno': '',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('apellido_materno', form.errors)

    # ------------------------------------------------------------------
    # Datos inválidos
    # ------------------------------------------------------------------

    def test_alumno_form_invalido_sin_datos(self):
        """AlumnoForm es inválido si se envía completamente vacío."""
        form = AlumnoForm(data={})
        self.assertFalse(form.is_valid())
        self.assertEqual(len(form.errors), 3)