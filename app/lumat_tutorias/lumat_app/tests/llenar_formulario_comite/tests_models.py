from decimal import Decimal
from datetime import date
from django.test import TestCase
from django.contrib.auth.models import User
from lumat_app.models import Seminario, Alumno, Comite, FormularioComite, Docente


class FormularioComiteModelTest(TestCase):
    """Pruebas para el modelo FormularioComite"""

    def setUp(self):
        # Usuario y alumno
        self.user_alumno = User.objects.create_user(
            username='alumno_test',
            password='testpass123',
            email='alumno@test.com'
        )
        self.alumno = Alumno.objects.create(
            user=self.user_alumno,
            nombre="Juan",
            apellido_paterno="Perez",
            apellido_materno="Lopez",
            matricula="20220001",
            semestre="5",
            correo="juan@test.com"
        )

        # Usuarios y docentes (3)
        users_data = [
            ('tutor_test', 'tutor@test.com', 'Carlos', 'Lopez', 'Garcia'),
            ('miembro1_test', 'miembro1@test.com',
             'Maria', 'Martinez', 'Rodriguez'),
            ('miembro2_test', 'miembro2@test.com', 'Jose', 'Sanchez', 'Perez')
        ]

        users = {}
        for username, email, nombre, apellido_p, apellido_m in users_data:
            user = User.objects.create_user(
                username=username,
                password='testpass123',
                email=email
            )
            users[username] = user

        self.tutor = Docente.objects.create(
            user=users['tutor_test'],
            nombre="Carlos",
            apellido_paterno="Lopez",
            apellido_materno="Garcia",
            correo="tutor@test.com"
        )
        self.miembro1 = Docente.objects.create(
            user=users['miembro1_test'],
            nombre="Maria",
            apellido_paterno="Martinez",
            apellido_materno="Rodriguez",
            correo="miembro1@test.com"
        )
        self.miembro2 = Docente.objects.create(
            user=users['miembro2_test'],
            nombre="Jose",
            apellido_paterno="Sanchez",
            apellido_materno="Perez",
            correo="miembro2@test.com"
        )

        # Comité y seminario
        self.comite = Comite.objects.create(
            tutor=self.tutor,
            miembro1=self.miembro1,
            miembro2=self.miembro2
        )
        self.seminario = Seminario.objects.create(
            numero=5,
            periodo=1,
            fecha=date(2024, 3, 15),
            hora="10:00",
            alumno=self.alumno,
            comite=self.comite
        )

        # Formulario
        self.formulario = FormularioComite.objects.create(
            seminario=self.seminario,
            el_comite_encuentra="El alumno demostró buen conocimiento",
            observaciones="Excelente presentación",
            dictamen="Aprobado",
            propuestas="Continuar con investigación"
        )

    def _firmar_todos(self, formulario=None):
        """Helper para firmar todos los miembros del comité"""
        f = formulario or self.formulario
        f.firma_tutor = True
        f.firma_miembro1 = True
        f.firma_miembro2 = True

    def _asignar_calificaciones(self, calificacion, formulario=None):
        """Helper para asignar misma calificación a todos los miembros"""
        f = formulario or self.formulario
        cal = Decimal(str(calificacion))
        f.calificacion_tutor = cal
        f.calificacion_miembro1 = cal
        f.calificacion_miembro2 = cal

    def test_creacion_formulario(self):
        self.assertEqual(self.formulario.seminario, self.seminario)
        self.assertEqual(self.formulario.el_comite_encuentra,
                         "El alumno demostró buen conocimiento")
        self.assertEqual(self.formulario.estado_general, "pendiente")

    def test_str_method(self):
        expected = f"Formulario Comité — Seminario {self.seminario.id} (pendiente)"
        self.assertEqual(str(self.formulario), expected)

    def test_valores_por_defecto(self):
        otro_seminario = Seminario.objects.create(
            numero=6,
            periodo=1,
            fecha=date(2024, 4, 15),
            hora="11:00",
            alumno=self.alumno,
            comite=self.comite
        )
        nuevo_form = FormularioComite.objects.create(seminario=otro_seminario)
        self.assertFalse(nuevo_form.firma_tutor)
        self.assertFalse(nuevo_form.firma_miembro1)
        self.assertFalse(nuevo_form.firma_miembro2)
        self.assertEqual(nuevo_form.estado_general, "pendiente")
        self.assertIsNone(nuevo_form.calificacion_final)

    def test_todos_firmaron_property(self):
        self.assertFalse(self.formulario.todos_firmaron)

        self.formulario.firma_tutor = True
        self.assertFalse(self.formulario.todos_firmaron)

        self.formulario.firma_miembro1 = True
        self.assertFalse(self.formulario.todos_firmaron)

        self.formulario.firma_miembro2 = True
        self.assertTrue(self.formulario.todos_firmaron)

    def test_calcular_calificacion_final(self):
        self.formulario.calificacion_tutor = Decimal("8.5")
        self.formulario.calificacion_miembro1 = Decimal("9.0")
        self.formulario.calificacion_miembro2 = Decimal("7.5")
        self.assertEqual(
            self.formulario.calcular_calificacion_final(), Decimal("8.33"))

    def test_calcular_calificacion_sin_datos(self):
        self.assertIsNone(self.formulario.calcular_calificacion_final())

    def test_calcular_con_una_calificacion(self):
        self.formulario.calificacion_tutor = Decimal("9.5")
        self.assertEqual(
            self.formulario.calcular_calificacion_final(), Decimal("9.50"))

    def test_save_actualiza_estado_completo(self):
        self._firmar_todos()
        self.formulario.save()
        self.assertEqual(self.formulario.estado_general, "completo")

    def test_save_actualiza_calificacion_seminario(self):
        self.formulario.calificacion_tutor = Decimal("9.0")
        self.formulario.calificacion_miembro1 = Decimal("8.5")
        self.formulario.calificacion_miembro2 = Decimal("9.5")
        self.formulario.save()

        self.seminario.refresh_from_db()
        self.assertEqual(self.seminario.calificacion, Decimal("9.00"))

    def test_restriccion_one_to_one(self):
        with self.assertRaises(Exception):
            FormularioComite.objects.create(seminario=self.seminario)

    # def test_promocion_semestre_al_aprobar(self):
    #     semestre_original = int(self.alumno.semestre)
    #     self.seminario.numero = semestre_original
    #     self.seminario.save()

    #     self._firmar_todos()
    #     self._asignar_calificaciones(8.0)
    #     self.formulario.save()

    #     self.formulario.refresh_from_db()
    #     self.assertEqual(self.formulario.estado_general, 'completo')
    #     self.assertIsNotNone(self.formulario.calificacion_final)
    #     self.assertGreaterEqual(self.formulario.calificacion_final, Decimal("6.0"))

    #     self.alumno.refresh_from_db()
    #     if semestre_original < 8:
    #         self.assertEqual(int(self.alumno.semestre), semestre_original + 1)

    # Pruebas de calificaciones y firmas
    def test_save_con_calificaciones_parciales(self):
        self.formulario.calificacion_tutor = Decimal("8.5")
        self.formulario.calificacion_miembro1 = Decimal("9.0")
        self.formulario.save()

        self.formulario.refresh_from_db()
        self.assertEqual(self.formulario.calificacion_final, Decimal("8.75"))

    def test_save_sin_calificaciones(self):
        self.formulario.save()
        self.assertIsNone(self.formulario.calificacion_final)
        self.assertEqual(self.formulario.estado_general, "pendiente")

    def test_save_con_firmas_incompletas(self):
        self.formulario.firma_tutor = True
        self.formulario.firma_miembro1 = True
        self.formulario.save()
        self.assertEqual(self.formulario.estado_general, "pendiente")

    def test_save_con_todas_las_firmas(self):
        self._firmar_todos()
        self.formulario.save()
        self.assertEqual(self.formulario.estado_general, "completo")

    # Pruebas de promoción (condensadas)
    def _verificar_no_promocion(self, semestre_original):
        """Helper para verificar que no hay promoción"""
        self.alumno.refresh_from_db()
        self.assertEqual(self.alumno.semestre, semestre_original)

    def test_no_promocion_si_nota_menor_6(self):
        semestre_original = self.alumno.semestre
        self._firmar_todos()
        self._asignar_calificaciones(5.5)
        self.formulario.save()
        self._verificar_no_promocion(semestre_original)

    def test_no_promocion_si_no_firmas_completas(self):
        semestre_original = self.alumno.semestre
        self._asignar_calificaciones(9.0)
        self.formulario.firma_tutor = True
        self.formulario.save()
        self._verificar_no_promocion(semestre_original)

    def test_no_promocion_cuando_no_coincide_numero(self):
        self.seminario.numero = 5
        self.seminario.save()
        semestre_original = self.alumno.semestre

        self._firmar_todos()
        self._asignar_calificaciones(8.0)
        self.formulario.save()
        self._verificar_no_promocion(semestre_original)

    def test_no_promocion_cuando_semestre_es_8(self):
        self.alumno.semestre = "8"
        self.alumno.save()
        self.seminario.numero = 8
        self.seminario.save()
        semestre_original = self.alumno.semestre

        self._firmar_todos()
        self._asignar_calificaciones(8.0)
        self.formulario.save()
        self._verificar_no_promocion(semestre_original)

    def test_no_promocion_con_calificacion_menor_6(self):
        semestre_original = self.alumno.semestre
        self._firmar_todos()
        self._asignar_calificaciones(5.5)
        self.formulario.save()
        self._verificar_no_promocion(semestre_original)

    def test_no_promocion_con_calificacion_none(self):
        semestre_original = self.alumno.semestre
        self._firmar_todos()
        self.formulario.calificacion_tutor = None
        self.formulario.calificacion_miembro1 = None
        self.formulario.calificacion_miembro2 = None
        self.formulario.save()
        self._verificar_no_promocion(semestre_original)

    def test_no_promocion_sin_firmas_completas(self):
        semestre_original = self.alumno.semestre
        self._asignar_calificaciones(9.0)
        self.formulario.firma_tutor = True
        self.formulario.save()
        self._verificar_no_promocion(semestre_original)

    def test_semestre_con_valor_invalido(self):
        self.alumno.semestre = "inválido"
        self.alumno.save()
        self.seminario.numero = 3
        self.seminario.save()
        semestre_original = self.alumno.semestre

        self._firmar_todos()
        self._asignar_calificaciones(9.0)
        self.formulario.save()
        self._verificar_no_promocion(semestre_original)

    def test_str_method_con_diferentes_estados(self):
        estados = ['pendiente', 'completo', 'rechazado']
        for estado in estados:
            self.formulario.estado_general = estado
            expected = f"Formulario Comité — Seminario {self.seminario.id} ({estado})"
            self.assertEqual(str(self.formulario), expected)

    def test_save_con_redondeo_calificacion(self):
        self._asignar_calificaciones(8.666)
        self.formulario.save()
        self.assertEqual(self.formulario.calificacion_final, Decimal("8.67"))

    # def test_promocion_cuando_coincide_numero(self):
    #     semestre_original = int(self.alumno.semestre)
    #     self._firmar_todos()
    #     self._asignar_calificaciones(8.0)
    #     self.formulario.save()

    #     self.alumno.refresh_from_db()
    #     self.assertEqual(int(self.alumno.semestre), semestre_original + 1)
