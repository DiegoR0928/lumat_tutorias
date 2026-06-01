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
