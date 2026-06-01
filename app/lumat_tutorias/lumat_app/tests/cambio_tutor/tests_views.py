from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User, Group

from lumat_app.models import (
    Alumno,
    SolicitudCambioTutor
)


class CambioTutorViewTest(TestCase):

    def setUp(self):

        self.user = User.objects.create_user(
            username="alumno1",
            password="12345"
        )

        grupo_alumno, _ = Group.objects.get_or_create(
            name="Alumno"
        )

        self.user.groups.add(grupo_alumno)

        self.alumno = Alumno.objects.create(
            user=self.user,
            matricula="20240001",
            nombre="Juan",
            apellido_paterno="Perez",
            apellido_materno="Lopez",
            semestre="1",
            correo="juan@test.com"
        )

        self.url = reverse("lumat_app:cambio_tutor")

    def test_usuario_no_autenticado_redirige_login(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 302)

    def test_get_muestra_template(self):
        self.assertTrue(
            self.client.login(
                username="alumno1",
                password="12345"
            )
        )

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)

        self.assertTemplateUsed(
            response,
            "alumno_cambio_tutor.html"
        )

    def test_contexto_contiene_alumno(self):
        self.client.login(
            username="alumno1",
            password="12345"
        )

        response = self.client.get(self.url)

        self.assertEqual(
            response.context["alumno"],
            self.alumno
        )

    def test_post_crea_solicitud(self):
        self.client.login(
            username="alumno1",
            password="12345"
        )

        response = self.client.post(
            self.url,
            {
                "motivo": "No hay buena comunicación"
            }
        )

        self.assertEqual(
            SolicitudCambioTutor.objects.count(),
            1
        )

        solicitud = SolicitudCambioTutor.objects.first()

        self.assertEqual(
            solicitud.motivo,
            "No hay buena comunicación"
        )

        self.assertEqual(
            response.status_code,
            302
        )

    def test_post_sin_motivo_no_crea_solicitud(self):
        self.client.login(
            username="alumno1",
            password="12345"
        )

        self.client.post(
            self.url,
            {
                "motivo": ""
            }
        )

        self.assertEqual(
            SolicitudCambioTutor.objects.count(),
            0
        )

    def test_no_permite_dos_solicitudes_pendientes(self):

        SolicitudCambioTutor.objects.create(
            alumno=self.alumno,
            motivo="Primera solicitud"
        )

        self.client.login(
            username="alumno1",
            password="12345"
        )

        self.client.post(
            self.url,
            {
                "motivo": "Segunda solicitud"
            }
        )

        self.assertEqual(
            SolicitudCambioTutor.objects.count(),
            1
        )

    def test_usuario_sin_grupo_alumno_no_puede_acceder(self):

        self.client.login(
            username="otro",
            password="12345"
        )

        response = self.client.get(self.url)

        self.assertEqual(
            response.status_code,
            302
        )
