from django.test import TestCase
from django.contrib.auth.models import User

from lumat_app.models import Alumno, SolicitudCambioTutor


class SolicitudCambioTutorModelTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="alumno1",
            password="12345"
        )

        self.alumno = Alumno.objects.create(
            user=self.user,
            matricula="20240001",
            nombre="Juan",
            apellido_paterno="Perez",
            apellido_materno="Lopez",
            semestre="1",
            correo="juan@test.com"
        )

    def test_creacion_solicitud(self):
        solicitud = SolicitudCambioTutor.objects.create(
            alumno=self.alumno,
            motivo="Quiero cambiar de tutor"
        )

        self.assertEqual(solicitud.alumno, self.alumno)
        self.assertEqual(
            solicitud.motivo,
            "Quiero cambiar de tutor"
        )

    def test_estado_por_defecto_es_pendiente(self):
        solicitud = SolicitudCambioTutor.objects.create(
            alumno=self.alumno,
            motivo="Motivo"
        )

        self.assertEqual(
            solicitud.estado,
            "pendiente"
        )

    def test_str(self):
        solicitud = SolicitudCambioTutor.objects.create(
            alumno=self.alumno,
            motivo="Motivo"
        )

        esperado = (
            f"Solicitud cambio tutor — "
            f"{self.alumno} (pendiente)"
        )

        self.assertEqual(
            str(solicitud),
            esperado
        )


class TestSolicitudCambioTutorModel(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='alumno1', password='123')
        self.alumno = Alumno.objects.create(
            matricula="20260001", user=self.user)

    def test_creacion_solicitud_valores_por_defecto(self):
        solicitud = SolicitudCambioTutor.objects.create(
            alumno=self.alumno,
            motivo="Falta de coincidencia en líneas de investigación."
        )
        self.assertEqual(solicitud.estado, 'pendiente')
        self.assertIsNotNone(solicitud.creada_en)
        self.assertIsNone(solicitud.resuelta_en)

    def test_string_representation(self):
        solicitud = SolicitudCambioTutor.objects.create(
            alumno=self.alumno,
            motivo="Motivo de prueba"
        )
        expected_str = f"Solicitud cambio tutor — {self.alumno} (pendiente)"
        self.assertEqual(str(solicitud), expected_str)

    def test_ordenamiento_por_defecto_mas_reciente_primero(self):
        sol1 = SolicitudCambioTutor.objects.create(
            alumno=self.alumno, motivo="Motivo 1"
        )
        sol2 = SolicitudCambioTutor.objects.create(
            alumno=self.alumno, motivo="Motivo 2"
        )
        solicitudes = SolicitudCambioTutor.objects.all()
        self.assertEqual(solicitudes[0], sol2)
        self.assertEqual(solicitudes[1], sol1)
