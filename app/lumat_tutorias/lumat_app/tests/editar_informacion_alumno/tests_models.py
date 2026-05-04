from django.test import TestCase
from django.contrib.auth.models import User
from lumat_app.models import Alumno


class AlumnoModelTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='alumno1',
            password='testpass123',
            email='alumno@uaz.edu.mx'
        )
        self.alumno = Alumno.objects.create(
            user=self.user,
            matricula='12345678',
            nombre='Juan',
            apellido_paterno='Pérez',
            apellido_materno='López',
            semestre='3',
            correo='alumno@uaz.edu.mx'
        )

    # --- Creación ---

    def test_alumno_se_crea_correctamente(self):
        self.assertEqual(Alumno.objects.count(), 1)

    def test_alumno_campos_correctos(self):
        self.assertEqual(self.alumno.nombre, 'Juan')
        self.assertEqual(self.alumno.apellido_paterno, 'Pérez')
        self.assertEqual(self.alumno.matricula, '12345678')

    # --- __str__ ---

    def test_str_retorna_formato_correcto(self):
        self.assertEqual(str(self.alumno), 'Juan Pérez (12345678)')

    def test_str_con_matricula_none(self):
        self.alumno.matricula = None
        self.alumno.save()
        self.assertEqual(str(self.alumno), 'Juan Pérez (None)')

    # --- Valores por defecto ---

    def test_matricula_puede_ser_nula(self):
        alumno_sin_matricula = Alumno.objects.create(
            user=User.objects.create_user(username='otro', password='pass'),
            nombre='Ana',
            apellido_paterno='Gómez',
            apellido_materno='Ruiz',
            semestre='1',
            correo='ana@uaz.edu.mx'
        )
        self.assertIsNone(alumno_sin_matricula.matricula)

    # --- Relaciones ---

    def test_alumno_tiene_relacion_con_user(self):
        self.assertEqual(self.alumno.user, self.user)

    def test_eliminar_user_elimina_alumno(self):
        self.user.delete()
        self.assertEqual(Alumno.objects.count(), 0)

    # --- Restricciones únicas ---

    def test_matricula_unica(self):
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            Alumno.objects.create(
                user=User.objects.create_user(
                    username='otro2', password='pass'),
                matricula='12345678',
                nombre='Pedro',
                apellido_paterno='García',
                apellido_materno='Soto',
                semestre='2',
                correo='pedro@uaz.edu.mx'
            )

    def test_user_unico_por_alumno(self):
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            Alumno.objects.create(
                user=self.user,
                nombre='Copia',
                apellido_paterno='Test',
                apellido_materno='Test',
                semestre='1',
                correo='copia@uaz.edu.mx'
            )
