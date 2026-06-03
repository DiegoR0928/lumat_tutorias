from django.test import TestCase
from django.contrib.auth.models import User
from lumat_app.models import Docente


class DocenteModelSimpleTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='profesor1', password='password123')
        self.docente = Docente.objects.create(
            user=self.user,
            nombre="Roberto",
            apellido_paterno="Gómez",
            apellido_materno="Bolaños",
            correo="roberto@lumat.edu"
        )

    def test_creacion_y_valores_docente(self):
        """Verifica que los datos del modelo se guarden correctamente en la BD."""
        self.assertEqual(Docente.objects.count(), 1)
        self.assertEqual(self.docente.nombre, "Roberto")
        self.assertEqual(self.docente.user.username, "profesor1")

    def test_metodo_str_docente(self):
        """Verifica que el método __str__ retorne el formato esperado."""
        self.assertEqual(str(self.docente), "Roberto Gómez")
