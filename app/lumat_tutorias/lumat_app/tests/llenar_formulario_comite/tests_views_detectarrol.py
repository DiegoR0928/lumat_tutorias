import datetime
from django.test import TestCase
from django.contrib.auth.models import User
from lumat_app.models import Alumno, Docente, Comite, Seminario
from lumat_app.views_docente import _rol_en_seminario


class RolEnSeminarioRealTestCase(TestCase):

    def setUp(self):
        # 1. Crear los usuarios (User) base de Django requeridos por las relaciones OneToOne
        user_alumno = User.objects.create_user(
            username='alumno_test_rol', password='pwd')
        user_tutor = User.objects.create_user(
            username='tutor_test_rol', password='pwd')
        user_m1 = User.objects.create_user(
            username='m1_test_rol', password='pwd')
        user_m2 = User.objects.create_user(
            username='m2_test_rol', password='pwd')
        user_externo = User.objects.create_user(
            username='externo_test_rol', password='pwd')

        # 2. Instanciar los alumnos y docentes reales en la base de datos de pruebas
        self.alumno = Alumno.objects.create(
            user=user_alumno,
            matricula="123456",
            nombre="Juan",
            apellido_paterno="Perez",
            semestre="8"
        )

        self.docente_tutor = Docente.objects.create(
            user=user_tutor, nombre="Carlos", apellido_paterno="Lopez", correo="carlos@uaz.mx")
        self.docente_m1 = Docente.objects.create(
            user=user_m1, nombre="Maria", apellido_paterno="Martinez", correo="maria@uaz.mx")
        self.docente_m2 = Docente.objects.create(
            user=user_m2, nombre="Jose", apellido_paterno="Sanchez", correo="jose@uaz.mx")

        # Docente que no pertenece a este comité para probar el retorno None
        self.docente_externo = Docente.objects.create(
            user=user_externo, nombre="Luis", apellido_paterno="Gomez", correo="luis@uaz.mx")

        # 3. Crear el Comité asignando las tres figuras
        self.comite = Comite.objects.create(
            tutor=self.docente_tutor,
            miembro1=self.docente_m1,
            miembro2=self.docente_m2
        )

        # 4. Crear el Seminario enlazando el alumno y el comité
        self.seminario = Seminario.objects.create(
            alumno=self.alumno,
            comite=self.comite,
            numero=8,
            fecha=datetime.date.today(),
            hora=datetime.time(12, 0)
        )

    # ── PATH 1: VALIDAR ROL DE TUTOR PRINCIPAL ──
    def test_rol_en_seminario_es_tutor(self):
        """Verifica que identifique correctamente al Tutor Principal."""
        rol = _rol_en_seminario(self.docente_tutor, self.seminario)
        self.assertEqual(rol, 'tutor')

    # ── PATH 2: VALIDAR ROL DE MIEMBRO TUTOR 1 ──
    def test_rol_en_seminario_es_miembro1(self):
        """Verifica que identifique correctamente al Miembro Tutor 1."""
        rol = _rol_en_seminario(self.docente_m1, self.seminario)
        self.assertEqual(rol, 'miembro1')

    # ── PATH 3: VALIDAR ROL DE MIEMBRO TUTOR 2 (CUBRE LÍNEA 224 Y PARCIALES) ──
    def test_rol_en_seminario_es_miembro2(self):
        """Verifica que identifique correctamente al Miembro Tutor 2, limpiando la rama parcial."""
        rol = _rol_en_seminario(self.docente_m2, self.seminario)
        self.assertEqual(rol, 'miembro2')

    # ── PATH 4: VALIDAR DOCENTE SIN ROL ASIGNADO (RETORNA NONE) ──
    def test_rol_en_seminario_es_none(self):
        """Verifica que si el docente no pertenece al sínodo, retorne None limpiamente."""
        rol = _rol_en_seminario(self.docente_externo, self.seminario)
        self.assertIsNone(rol)
