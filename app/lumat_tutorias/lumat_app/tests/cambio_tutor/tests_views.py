from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User, Group

from lumat_app.models import (
    Alumno,
    SolicitudCambioTutor,
    Docente,
    Comite,
    Seminario
)

from datetime import date, time


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


class TestCambioTutorViews(TestCase):

    def setUp(self):
        self.client = Client()
        self.admin = User.objects.create_superuser(
            username='admin', password='123'
        )

        u_d1 = User.objects.create_user(username='d1', password='123')
        u_d2 = User.objects.create_user(username='d2', password='123')
        u_d3 = User.objects.create_user(username='d3', password='123')
        u_d4 = User.objects.create_user(username='d4', password='123')

        self.doc1 = Docente.objects.create(user=u_d1)
        self.doc2 = Docente.objects.create(user=u_d2)
        self.doc3 = Docente.objects.create(user=u_d3)
        self.doc4 = Docente.objects.create(user=u_d4)

        self.comite = Comite.objects.create(
            tutor=self.doc1, miembro1=self.doc2, miembro2=self.doc3
        )

        u_a = User.objects.create_user(username='a1', password='123')
        self.alumno = Alumno.objects.create(matricula="20260001", user=u_a)

        self.seminario = Seminario.objects.create(
            alumno=self.alumno,
            comite=self.comite,
            fecha=date(2026, 6, 1),
            hora=time(9, 0),
            numero=1
        )

        self.solicitud = SolicitudCambioTutor.objects.create(
            alumno=self.alumno,
            motivo="Cambio por incompatibilidad de agenda."
        )

        self.url = '/admin/cambio-tutor/'

    def test_get_cambio_tutor_view_autenticado(self):
        self.client.login(username='admin', password='123')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "admin/cambio_tutor.html")
        self.assertIn("solicitudes", response.context)
        self.assertIn("docentes", response.context)

    def test_rechazar_solicitud_exitoso_sin_docente(self):
        self.client.login(username='admin', password='123')
        datos = {
            "solicitud_id": self.solicitud.id,
            "docente_id": "",
            "accion": "rechazar"
        }
        response = self.client.post(self.url, datos)
        self.assertRedirects(response, self.url)

        self.solicitud.refresh_from_db()
        self.assertEqual(self.solicitud.estado, "rechazada")
        self.assertIsNotNone(self.solicitud.resuelta_en)

    def test_aprobar_solicitud_error_sin_docente_seleccionado(self):
        self.client.login(username='admin', password='123')
        datos = {
            "solicitud_id": self.solicitud.id,
            "docente_id": "",
            "accion": "aprobar"
        }
        response = self.client.post(self.url, datos)
        self.assertRedirects(response, self.url)

        self.solicitud.refresh_from_db()
        self.assertEqual(self.solicitud.estado, "pendiente")

    def test_aprobar_solicitud_error_docente_ya_en_comite(self):
        self.client.login(username='admin', password='123')
        datos = {
            "solicitud_id": self.solicitud.id,
            "docente_id": self.doc2.id,
            "accion": "aprobar"
        }
        response = self.client.post(self.url, datos)
        self.assertRedirects(response, self.url)

        self.solicitud.refresh_from_db()
        self.comite.refresh_from_db()
        self.assertEqual(self.solicitud.estado, "pendiente")
        self.assertEqual(self.comite.tutor, self.doc1)

    def test_aprobar_solicitud_exitoso_y_cambia_tutor(self):
        self.client.login(username='admin', password='123')
        datos = {
            "solicitud_id": self.solicitud.id,
            "docente_id": self.doc4.id,
            "accion": "aprobar"
        }
        response = self.client.post(self.url, datos)
        self.assertRedirects(response, self.url)

        self.solicitud.refresh_from_db()
        self.comite.refresh_from_db()
        self.assertEqual(self.solicitud.estado, "aprobada")
        self.assertEqual(self.comite.tutor, self.doc4)
