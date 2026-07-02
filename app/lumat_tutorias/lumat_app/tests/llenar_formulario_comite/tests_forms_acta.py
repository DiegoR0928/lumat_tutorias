import datetime
from unittest.mock import patch, MagicMock
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User, Group
from django.contrib.messages import get_messages
from lumat_app.models import Alumno, Docente, Comite, Seminario, FormularioComite


class DocenteGuardarInformePostTestCase(TestCase):

    def setUp(self):
        self.client = Client()

        # 1. Configurar el grupo y rol de Docente requerido por el decorador
        self.grupo_docente, _ = Group.objects.get_or_create(name='Docente')

        self.user_tutor = User.objects.create_user(
            username='tutor_informe', password='password123')
        self.user_tutor.groups.add(self.grupo_docente)
        self.tutor = Docente.objects.create(
            user=self.user_tutor, nombre="Carlos", apellido_paterno="Lopez", correo="tutor@uaz.mx")

        # Docentes dummy para la correcta instanciación del Comité
        u_m1 = User.objects.create_user(username='m1_dummy', password='pwd')
        u_m2 = User.objects.create_user(username='m2_dummy', password='pwd')
        doc_m1 = Docente.objects.create(
            user=u_m1, nombre="M1", apellido_paterno="A", correo="m1@uaz.mx")
        doc_m2 = Docente.objects.create(
            user=u_m2, nombre="M2", apellido_paterno="B", correo="m2@uaz.mx")

        # 2. Configurar Alumno, Comité y Seminario
        self.user_alumno = User.objects.create_user(
            username='alumno_informe', password='pwd')
        self.alumno = Alumno.objects.create(
            user=self.user_alumno, matricula="20220001", nombre="Luis")

        self.comite = Comite.objects.create(
            tutor=self.tutor, miembro1=doc_m1, miembro2=doc_m2)
        self.seminario = Seminario.objects.create(
            alumno=self.alumno, comite=self.comite, numero=5,
            fecha=datetime.date.today(), hora=datetime.time(10, 0)
        )

        with patch.object(FormularioComite, 'save', return_value=None):
            self.formulario = FormularioComite(
                seminario=self.seminario,
                firma_tutor=False,
                firma_miembro1=False,
                firma_miembro2=False
            )
            super(FormularioComite, self.formulario).save()

        # URL bajo prueba
        self.url_detalle = reverse('lumat_app:docente_seminario_detalle', kwargs={
                                   'seminario_id': self.seminario.id})

        # Forzar inicio de sesión del tutor
        self.client.force_login(self.user_tutor)

    # ── PATH A: POST EXITOSO (CUBRE LÍNEAS 253 A 258 COMPLEMENTARIAMENTE) ──
    @patch('lumat_app.views_docente.FormularioComiteForm')
    def test_tutor_guarda_informe_valido_post_exito_y_redirige_200(self, mock_form_class):
        """
        Si el tutor envía un POST con datos válidos, procesa el guardado,
        genera el mensaje de éxito, genera un redirect (302) y el destino final responde 200 OK.
        """
        # Mockear la instancia del formulario para forzar que sea válido
        mock_form_instance = MagicMock()
        mock_form_instance.is_valid.return_value = True
        mock_form_class.return_value = mock_form_instance

        payload = {
            'el_comite_encuentra': 'Satisfactorio',
            'observaciones': 'Buen avance en el desarrollo del sistema web.',
            'dictamen': 'Aprobado',
            'propuestas': 'Continuar con las pruebas unitarias en Docker.'
        }

        with patch.object(FormularioComite, 'save', return_value=None):
            response = self.client.post(
                self.url_detalle, data=payload, follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, self.url_detalle,
                             status_code=302, target_status_code=200)

        # 2. Comprobar que el método .save() del formulario de Django efectivamente se ejecutó
        mock_form_instance.save.assert_called_once()

        # 3. Validar la inserción de la alerta flash de éxito
        mensajes = list(get_messages(response.wsgi_request))
        self.assertEqual(len(mensajes), 1)
        self.assertEqual(str(mensajes[0]), 'Informe guardado correctamente.')

    # ── PATH B: POST ENTRADA PERO FORMULARIO INVÁLIDO (CIERRA LA COBERTURA DE LA BIFURCACIÓN) ──
    @patch('lumat_app.views_docente.FormularioComiteForm')
    def test_tutor_envia_informe_invalido_post_no_guarda_y_renderiza(self, mock_form_class):
        """
        Si el tutor envía un POST pero los datos no superan las validaciones del formulario,
        no ejecuta el método save(), no redirige (retorna un 200 directo) y vuelve a pintar
        la página mostrando los errores.
        """
        mock_form_instance = MagicMock()
        mock_form_instance.is_valid.return_value = False
        mock_form_class.return_value = mock_form_instance

        payload = {
            'el_comite_encuentra': '',  # Campo requerido vacío para forzar el fallo
        }

        with patch.object(FormularioComite, 'save', return_value=None):
            response = self.client.post(self.url_detalle, data=payload)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'docente_seminario_detalle.html')

        # 2. Garantizar que NUNCA se llamó al guardado de la información inválida
        mock_form_instance.save.assert_not_called()
