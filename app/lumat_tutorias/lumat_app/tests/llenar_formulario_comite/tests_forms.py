from unittest.mock import MagicMock
from django.test import TestCase, RequestFactory
from django.contrib.messages import get_messages
from django.contrib.messages.storage.cookie import CookieStorage
from lumat_app.models import Alumno, Comite, Seminario, FormularioComite
# Asegúrate de que apunte al módulo real donde reside la función de 4 parámetros
from lumat_app.views_docente import text_form_valido, _verificar_y_generar_pdf_comite


class HelpersDocenteTestCase(TestCase):

    def setUp(self):
        self.factory = RequestFactory()

        self.request = self.factory.get('/')
        setattr(self.request, '_messages', CookieStorage(self.request))

        self.alumno = MagicMock(spec=Alumno, id=1, matricula="20220001")
        self.comite = MagicMock(spec=Comite, id=1)

        self.seminario = MagicMock(spec=Seminario)
        self.seminario.id = 1
        self.seminario.numero = 5
        self.seminario.alumno = self.alumno
        self.seminario.calificacion = None

        self.formulario = MagicMock(spec=FormularioComite)
        self.formulario.estado_general = 'pendiente'
        self.formulario.calificacion_final = 8.5

    # ═══ PRUEBAS PARA text_form_valido (Versión Real de 4 parámetros) ═══

    def test_text_form_valido_cuatro_parametros_exito(self):
        mock_form = MagicMock()
        mock_form.is_valid.return_value = True

        resultado = text_form_valido(
            mock_form, self.request, self.formulario, 'miembro1')

        self.assertTrue(resultado)
        mensajes = list(get_messages(self.request))
        self.assertEqual(len(mensajes), 0)

    def test_text_form_valido_cuatro_parametros_invalido(self):
        mock_form = MagicMock()
        mock_form.is_valid.return_value = False

        resultado = text_form_valido(
            mock_form, self.request, self.formulario, 'miembro1')

        self.assertFalse(resultado)
        mensajes = list(get_messages(self.request))
        self.assertEqual(len(mensajes), 1)
        self.assertEqual(
            str(mensajes[0]), "La calificación debe ser un número entre 0 y 10.")

    # ═══ PRUEBAS PARA _verificar_y_generar_pdf_comite ═══

    def test_verificar_pdf_comite_ignora_flujo_si_esta_pendiente(self):

        self.formulario.estado_general = 'pendiente'

        _verificar_y_generar_pdf_comite(
            self.request, self.seminario, self.formulario)

        self.seminario.save.assert_not_called()
        mensajes = list(get_messages(self.request))
        self.assertEqual(len(mensajes), 0)

    def test_verificar_pdf_comite_exito_cuando_esta_completo(self):
        self.formulario.estado_general = 'completo'
        self.formulario.calificacion_final = 9.35

        _verificar_y_generar_pdf_comite(
            self.request, self.seminario, self.formulario)

        self.assertEqual(self.seminario.calificacion, 9.35)
        self.seminario.save.assert_called_once()

        mensajes = list(get_messages(self.request))
        self.assertEqual(len(mensajes), 1)
        self.assertEqual(
            str(mensajes[0]),
            "El sínodo se ha completado. Se ha emitido y archivado el Acta del Comité PDF."
        )

    def test_verificar_pdf_comite_atrapa_excepciones_y_muestra_error(self):
        self.formulario.estado_general = 'completo'
        self.seminario.save.side_effect = Exception(
            "Fallo de escritura en el storage de medios")

        _verificar_y_generar_pdf_comite(
            self.request, self.seminario, self.formulario)

        mensajes = list(get_messages(self.request))
        self.assertEqual(len(mensajes), 1)
        self.assertIn(
            "Las firmas son válidas pero ocurrió un error al construir el archivo PDF",
            str(mensajes[0])
        )
        self.assertIn("Fallo de escritura", str(mensajes[0]))
