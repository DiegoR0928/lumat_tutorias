from django.test import TestCase
from django.contrib.auth.models import User
from lumat_app.forms import DocenteForm, PasswordChangeCustomForm
from django.core.files.uploadedfile import SimpleUploadedFile


class DocenteFormSimpleTest(TestCase):

    def test_formulario_docente_datos_validos(self):
        """El formulario es válido si cuenta con datos correctos y archivo simulado."""
        # Creamos un archivo de imagen falso en bytes transparentes
        imagen_falsa = SimpleUploadedFile(
            name="firma_test.png",
            content=(
                b"\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00"
                b"\x00\x00\x00\xff\xff\xff\x21\xf9\x04\x01\x00\x00\x00"
                b"\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02"
                b"\x4c\x01\x00\x3b"
            ),
            content_type="image/png",
        )

        datos = {
            'nombre': 'María',
            'apellido_paterno': 'Espinoza',
            'apellido_materno': 'Sanz',
            'correo': 'maria@lumat.edu'
        }

        # Le pasamos la data y los archivos simulados por separado al constructor
        form = DocenteForm(data=datos, files={'firma': imagen_falsa})
        self.assertTrue(form.is_valid())


class PasswordChangeCustomFormSimpleTest(TestCase):

    def test_inyeccion_clase_css_campos_password(self):
        """El constructor personalizado debe agregar 'alumno-input' a todos los widgets."""
        user = User.objects.create_user(
            username='usuario_cambio', password='old_password123')
        form = PasswordChangeCustomForm(user=user)

        for field in form.fields.values():
            self.assertEqual(field.widget.attrs.get('class'), 'alumno-input')
