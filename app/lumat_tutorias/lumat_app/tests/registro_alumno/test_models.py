from django.test import TestCase
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from lumat_app.models import Alumno  # ajusta al nombre real de tu app


class AlumnoModelTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='alumno1',
            email='alumno1@escuela.mx',
            password='Test#1234'
        )

    # ------------------------------------------------------------------
    # Creación de objetos
    # ------------------------------------------------------------------

    def test_creacion_alumno_exitosa(self):
        """Un alumno se crea correctamente con todos sus campos."""
        alumno = Alumno.objects.create(
            user=self.user,
            nombre='Juan',
            apellido_paterno='Pérez',
            apellido_materno='García',
        )
        self.assertIsNotNone(alumno.pk)

    # ------------------------------------------------------------------
    # Método __str__
    # ------------------------------------------------------------------

    def test_str_retorna_representacion_legible(self):
        """__str__ devuelve una cadena no vacía."""
        alumno = Alumno.objects.create(
            user=self.user,
            nombre='Juan',
            apellido_paterno='Pérez',
            apellido_materno='García',
        )
        self.assertIsInstance(str(alumno), str)
        self.assertGreater(len(str(alumno)), 0)

    # ------------------------------------------------------------------
    # Relaciones
    # ------------------------------------------------------------------

    def test_alumno_tiene_relacion_con_user(self):
        """El alumno está correctamente vinculado a un User."""
        alumno = Alumno.objects.create(
            user=self.user,
            nombre='Juan',
            apellido_paterno='Pérez',
            apellido_materno='García',
        )
        self.assertEqual(alumno.user, self.user)

    def test_relacion_inversa_user_alumno(self):
        """Desde el User se puede acceder al Alumno relacionado."""
        alumno = Alumno.objects.create(
            user=self.user,
            nombre='Juan',
            apellido_paterno='Pérez',
            apellido_materno='García',
        )
        self.assertEqual(self.user.alumno, alumno)

    # ------------------------------------------------------------------
    # Restricciones únicas
    # ------------------------------------------------------------------

    def test_un_user_no_puede_tener_dos_alumnos(self):
        """No se puede crear un segundo Alumno con el mismo User (OneToOne)."""
        Alumno.objects.create(
            user=self.user,
            nombre='Juan',
            apellido_paterno='Pérez',
            apellido_materno='García',
        )
        with self.assertRaises(Exception):
            Alumno.objects.create(
                user=self.user,
                nombre='Otro',
                apellido_paterno='Apellido',
                apellido_materno='Materno',
            )

    # ------------------------------------------------------------------
    # Validaciones
    # ------------------------------------------------------------------

    def test_nombre_no_puede_ser_vacio(self):
        """El campo nombre es obligatorio."""
        alumno = Alumno(
            user=self.user,
            nombre='',
            apellido_paterno='Pérez',
            apellido_materno='García',
        )
        with self.assertRaises(ValidationError):
            alumno.full_clean()

    def test_apellido_paterno_no_puede_ser_vacio(self):
        """El campo apellido_paterno es obligatorio."""
        alumno = Alumno(
            user=self.user,
            nombre='Juan',
            apellido_paterno='',
            apellido_materno='García',
        )
        with self.assertRaises(ValidationError):
            alumno.full_clean()

    def test_apellido_materno_no_puede_ser_vacio(self):
        """El campo apellido_materno es obligatorio."""
        alumno = Alumno(
            user=self.user,
            nombre='Juan',
            apellido_paterno='Pérez',
            apellido_materno='',
        )
        with self.assertRaises(ValidationError):
            alumno.full_clean()
