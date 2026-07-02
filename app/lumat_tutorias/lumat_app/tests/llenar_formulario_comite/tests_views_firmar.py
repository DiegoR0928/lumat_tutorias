import datetime
from unittest.mock import patch

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User, Group
from django.contrib.messages import get_messages

from lumat_app.models import Alumno, Docente, Comite, Seminario, FormularioComite


class DocenteFirmarSeminarioTestCase(TestCase):

    def setUp(self):
        self.client = Client()

        # 1. Configurar el grupo y rol requeridos por @user_passes_test(es_docente)
        self.grupo_docente, _ = Group.objects.get_or_create(name='Docente')

        self.user_tutor = User.objects.create_user(
            username='tutor_u', password='pwd')
        self.user_tutor.groups.add(self.grupo_docente)
        self.tutor = Docente.objects.create(
            user=self.user_tutor, nombre="Carlos", apellido_paterno="Lopez", correo="t@uaz.mx")

        self.user_m1 = User.objects.create_user(
            username='m1_u', password='pwd')
        self.user_m1.groups.add(self.grupo_docente)
        self.m1 = Docente.objects.create(
            user=self.user_m1, nombre="Maria", apellido_paterno="Gomez", correo="m1@uaz.mx")

        self.user_m2 = User.objects.create_user(
            username='m2_u', password='pwd')
        self.user_m2.groups.add(self.grupo_docente)
        self.m2 = Docente.objects.create(
            user=self.user_m2, nombre="Jose", apellido_paterno="Sanchez", correo="m2@uaz.mx")

        # 2. Configurar Alumno e infraestructura del Comité/Seminario
        self.user_alumno = User.objects.create_user(
            username='alumno_u', password='pwd')
        self.alumno = Alumno.objects.create(
            user=self.user_alumno, matricula="20220001", nombre="Luis")

        self.comite = Comite.objects.create(
            tutor=self.tutor, miembro1=self.m1, miembro2=self.m2)
        self.seminario = Seminario.objects.create(
            alumno=self.alumno, comite=self.comite, numero=5, 
            fecha=datetime.date.today(), hora=datetime.time(10, 0)
        )

        # Mockear el save conflictivo para crear la instancia inicial del formulario sin errores
        with patch.object(FormularioComite, 'save', return_value=None):
            self.formulario = FormularioComite(
                seminario=self.seminario,
                firma_tutor=False,
                firma_miembro1=False,
                firma_miembro2=False
            )
            super(FormularioComite, self.formulario).save()

        # URLs de la vista bajo prueba y su destino de redirección
        self.url_firmar = reverse('lumat_app:docente_firmar_seminario', kwargs={
                                  'seminario_id': self.seminario.id})
        self.url_detalle = reverse('lumat_app:docente_seminario_detalle', kwargs={
                                   'seminario_id': self.seminario.id})

    # ── PATH 1: RECHAZAR PETICIONES QUE NO SEAN POST (MÉTODO GET) ──
    def test_peticion_get_redirige_a_detalle_con_exito_200(self):
        """Si se accede a la URL mediante método GET, se rechaza y redirige a la vista detalle."""
        self.client.force_login(self.user_tutor)

        with patch.object(FormularioComite, 'save', return_value=None):
            response = self.client.get(self.url_firmar, follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, self.url_detalle,
                             status_code=302, target_status_code=200)

    # ── PATH 2: CONTROL CUANDO EL DOCENTE YA HABÍA FIRMADO EL SEMINARIO ──
    def test_docente_ya_firmado_bloquea_post_y_redirige(self):
        """Si el docente ya firmó previamente, añade un warning en los mensajes y redirige."""
        self.client.force_login(self.user_tutor)

        # Marcamos la firma del tutor como True de manera directa en la BD simulada
        self.formulario.firma_tutor = True
        with patch.object(FormularioComite, 'save', return_value=None):
            super(FormularioComite, self.formulario).save()

        payload = {'calificacion': 9.0, 'confirmar_firma': True}
        with patch.object(FormularioComite, 'save', return_value=None):
            response = self.client.post(
                self.url_firmar, data=payload, follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, self.url_detalle,
                             status_code=302, target_status_code=200)

        mensajes = list(get_messages(response.wsgi_request))
        self.assertEqual(str(mensajes[0]), 'Ya habías firmado este seminario.')

    def test_formulario_firma_invalido_agrega_mensaje_error(self):
        self.client.force_login(self.user_tutor)

        # 15.0 está fuera del rango [0, 10]
        payload = {'calificacion': 15.0, 'confirmar_firma': True}
        with patch.object(FormularioComite, 'save', return_value=None):
            response = self.client.post(
                self.url_firmar, data=payload, follow=True)

        self.assertEqual(response.status_code, 200)
        mensajes = list(get_messages(response.wsgi_request))
        self.assertEqual(
            str(mensajes[0]), 'Datos inválidos. Verifica la calificación.')

    def test_firma_exitosa_como_tutor_persiste_y_redirige(self):
        self.client.force_login(self.user_tutor)

        payload = {'calificacion': 9.5, 'confirmar_firma': True}

        with patch.object(FormularioComite, 'save', autospec=True) as mock_save:
            response = self.client.post(
                self.url_firmar, data=payload, follow=True)

            # Recuperamos el objeto sobre el que la vista llamó al .save()
            instancia_guardada = mock_save.call_args[0][0]
            self.assertTrue(instancia_guardada.firma_tutor)
            self.assertEqual(instancia_guardada.calificacion_tutor, 9.5)

        self.assertEqual(response.status_code, 200)
        mensajes = list(get_messages(response.wsgi_request))
        self.assertEqual(str(mensajes[0]), 'Firma y calificación registradas.')

    # ── PATH 5: FLUJO EXITOSO — ROL MIEMBRO SINODAL 1 ──
    def test_firma_exitosa_como_miembro1_persiste_y_redirige(self):
        """El miembro sinodal 1 registra su evaluación, modificando sus campos correspondientes."""
        self.client.force_login(self.user_m1)

        payload = {'calificacion': 8.0, 'confirmar_firma': True}

        with patch.object(FormularioComite, 'save', autospec=True) as mock_save:
            response = self.client.post(
                self.url_firmar, data=payload, follow=True)

            instancia_guardada = mock_save.call_args[0][0]
            self.assertTrue(instancia_guardada.firma_miembro1)
            self.assertEqual(instancia_guardada.calificacion_miembro1, 8.0)

        self.assertEqual(response.status_code, 200)
        mensajes = list(get_messages(response.wsgi_request))
        self.assertEqual(str(mensajes[0]), 'Firma y calificación registradas.')
