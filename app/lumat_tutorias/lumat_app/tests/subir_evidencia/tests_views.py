"""
Pruebas unitarias — Vistas
Cubre: subir_evidencia
"""

from unittest.mock import patch, MagicMock

from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, Client
from django.urls import reverse

from lumat_app.models import Alumno

User = get_user_model()

URL_NAME = 'lumat_app:subir_evidencia'
DETALLE_NAME = 'lumat_app:seminario_detalle'
SEMINARIO_ID = 1
NUMERO = 5          # valor de seminario_obj.numero usado en los mocks


# ─────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────

def make_pdf(nombre='evidencia.pdf', extra_bytes=0):
    return SimpleUploadedFile(
        nombre,
        b'%PDF-1.4 ' + b'0' * extra_bytes,
        content_type='application/pdf',
    )


def make_file(nombre='datos.js', content_type='application/javascript'):
    return SimpleUploadedFile(nombre, b'contenido', content_type=content_type)


def seminario_mock(numero=NUMERO):
    """Mock de "Seminario" con el atributo .numero directo (sin numero_obj)."""
    m = MagicMock()
    m.id = SEMINARIO_ID
    m.numero = numero
    return m


def messages_list(response):
    return [str(m) for m in get_messages(response.wsgi_request)]


# ─────────────────────────────────────────────────────────────
# Base con usuario autenticado de forma persistente
# ─────────────────────────────────────────────────────────────

class BaseAuthTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='alumno_ev', password='pass1234')
        
        # Crear el perfil relacional obligatorio de Alumno
        self.alumno = Alumno.objects.create(
            user=self.user,
            nombre="Luis",
            apellido_paterno="Vega",
            matricula="EV_TEST"
        )
        # CORRECCIÓN: force_login mantiene la persistencia de sesión intacta durante las pruebas
        self.client.force_login(self.user)
        self.url = reverse(URL_NAME, kwargs={'seminario_id': SEMINARIO_ID})


# ─────────────────────────────────────────────────────────────
# 1. Autenticación
# ─────────────────────────────────────────────────────────────

class SubirEvidenciaAutenticacionTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.url = reverse(URL_NAME, kwargs={'seminario_id': SEMINARIO_ID})

    def test_anonimo_post_redirige_a_login(self):
        r = self.client.post(self.url)
        self.assertEqual(r.status_code, 302)
        self.assertIn('/login', r['Location'])

    def test_anonimo_get_redirige_a_login(self):
        r = self.client.get(self.url)
        self.assertEqual(r.status_code, 302)
        self.assertIn('/login', r['Location'])


# ─────────────────────────────────────────────────────────────
# 2. Método HTTP — GET no procesa el archivo
# ─────────────────────────────────────────────────────────────

class SubirEvidenciaMetodoHTTPTests(BaseAuthTests):

    @patch('lumat_app.views.get_object_or_404', return_value=seminario_mock())
    def test_get_redirige_sin_crear_evidencia(self, _):
        with patch('lumat_app.views.Evidencia') as mock_ev:
            r = self.client.get(self.url)
        mock_ev.objects.create.assert_not_called()
        self.assertEqual(r.status_code, 302)

    @patch('lumat_app.views.get_object_or_404', return_value=seminario_mock())
    def test_get_redirige_a_detalle_correcto(self, _):
        r = self.client.get(self.url)
        self.assertRedirects(
            r,
            reverse(DETALLE_NAME, kwargs={'num': NUMERO}),
            fetch_redirect_response=False,
        )

    @patch('lumat_app.views.get_object_or_404', return_value=seminario_mock())
    def test_put_tambien_redirige(self, _):
        r = self.client.put(self.url)
        self.assertEqual(r.status_code, 302)


# ─────────────────────────────────────────────────────────────
# 3. Validaciones de archivo
# ─────────────────────────────────────────────────────────────

class SubirEvidenciaValidacionesTests(BaseAuthTests):

    @patch('lumat_app.views.get_object_or_404', return_value=seminario_mock())
    def test_sin_archivo_error_mensaje(self, _):
        r = self.client.post(self.url, data={})
        msgs = messages_list(r)
        self.assertTrue(any('ningún archivo' in m for m in msgs))

    @patch('lumat_app.views.get_object_or_404', return_value=seminario_mock())
    def test_sin_archivo_redirige(self, _):
        r = self.client.post(self.url, data={})
        self.assertEqual(r.status_code, 302)

    @patch('lumat_app.views.get_object_or_404', return_value=seminario_mock())
    def test_archivo_mayor_10mb_error(self, _):
        archivo = SimpleUploadedFile(
            'grande.pdf', b'0' * (10 * 1024 * 1024 + 1),
            content_type='application/pdf')
        r = self.client.post(self.url, data={'archivo': archivo})
        self.assertTrue(any('10 MB' in m for m in messages_list(r)))

    @patch('lumat_app.views.get_object_or_404', return_value=seminario_mock())
    def test_archivo_exactamente_10mb_no_error_tamano(self, _):
        archivo = SimpleUploadedFile(
            'limite.pdf', b'%PDF-' + b'0' * (10 * 1024 * 1024 - 5),
            content_type='application/pdf')
        with patch('lumat_app.views.Evidencia'):
            r = self.client.post(self.url, data={'archivo': archivo})
        self.assertFalse(any('10 MB' in m for m in messages_list(r)))

    @patch('lumat_app.views.get_object_or_404', return_value=seminario_mock())
    def test_mime_no_permitido_error(self, _):
        r = self.client.post(self.url, data={'archivo': make_file()})
        self.assertTrue(
            any('PDF' in m or 'permitido' in m.lower()
                for m in messages_list(r)))

    @patch('lumat_app.views.get_object_or_404', return_value=seminario_mock())
    def test_imagen_rechazada_actualmente(self, _):
        archivo = SimpleUploadedFile(
            'foto.png', b'\x89PNG', content_type='image/png')
        r = self.client.post(self.url, data={'archivo': archivo})
        self.assertTrue(
            any('PDF' in m or 'permitido' in m.lower()
                for m in messages_list(r)))

    @patch('lumat_app.views.Evidencia')
    @patch('lumat_app.views.get_object_or_404', return_value=seminario_mock())
    def test_pdf_valido_llama_create(self, _, mock_ev):
        self.client.post(self.url, data={'archivo': make_pdf()})
        mock_ev.objects.create.assert_called_once()

    # CORREGIDO: Se pasa el payload completo 'nombre' para evitar fallos del subscript en el call_args de mocks parciales
    @patch('lumat_app.views.Evidencia')
    @patch('lumat_app.views.get_object_or_404', return_value=seminario_mock())
    def test_create_recibe_seminario_y_archivo(self, mock_g404, mock_ev):
        sem = seminario_mock()
        mock_g404.return_value = sem
        archivo = make_pdf('doc.pdf')
        
        payload = {
            'nombre': 'doc.pdf',
            'archivo': archivo
        }
        self.client.post(self.url, data=payload)
        
        # Validamos llamada segura
        mock_ev.objects.create.assert_called_once()
        kwargs = mock_ev.objects.create.call_args[1]
        self.assertEqual(kwargs['seminario'], sem)
        self.assertEqual(kwargs['nombre'], 'doc.pdf')


# ─────────────────────────────────────────────────────────────
# 4. Mensajes
# ─────────────────────────────────────────────────────────────

class SubirEvidenciaMensajesTests(BaseAuthTests):

    @patch('lumat_app.views.Evidencia')
    @patch('lumat_app.views.get_object_or_404', return_value=seminario_mock())
    def test_exito_muestra_mensaje_success(self, _, __):
        r = self.client.post(self.url, data={'archivo': make_pdf()})
        self.assertTrue(
            any('correctamente' in m for m in messages_list(r)))

    @patch('lumat_app.views.get_object_or_404', return_value=seminario_mock())
    def test_error_mime_muestra_mensaje_error(self, _):
        r = self.client.post(self.url, data={'archivo': make_file()})
        self.assertTrue(len(messages_list(r)) > 0)

    @patch('lumat_app.views.get_object_or_404', return_value=seminario_mock())
    def test_error_tamano_muestra_un_solo_mensaje(self, _):
        archivo = SimpleUploadedFile(
            'g.pdf', b'0' * (10 * 1024 * 1024 + 1),
            content_type='application/pdf')
        r = self.client.post(self.url, data={'archivo': archivo})
        self.assertEqual(len(messages_list(r)), 1)


# ─────────────────────────────────────────────────────────────
# 5. Redirecciones — siempre a seminario_detalle con .numero
# ─────────────────────────────────────────────────────────────

class SubirEvidenciaRedireccionesTests(BaseAuthTests):

    def _assert_redirige_a_detalle(self, response, numero=NUMERO):
        self.assertRedirects(
            response,
            reverse(DETALLE_NAME, kwargs={'num': numero}),
            fetch_redirect_response=False,
        )

    @patch('lumat_app.views.get_object_or_404', return_value=seminario_mock())
    def test_get_redirige_a_detalle(self, _):
        self._assert_redirige_a_detalle(self.client.get(self.url))

    @patch('lumat_app.views.get_object_or_404', return_value=seminario_mock())
    def test_sin_archivo_redirige_a_detalle(self, _):
        self._assert_redirige_a_detalle(
            self.client.post(self.url, data={}))

    @patch('lumat_app.views.get_object_or_404', return_value=seminario_mock())
    def test_error_tamano_redirige_a_detalle(self, _):
        archivo = SimpleUploadedFile(
            'g.pdf', b'0' * (10 * 1024 * 1024 + 1),
            content_type='application/pdf')
        self._assert_redirige_a_detalle(
            self.client.post(self.url, data={'archivo': archivo}))

    @patch('lumat_app.views.get_object_or_404', return_value=seminario_mock())
    def test_error_mime_redirige_a_detalle(self, _):
        self._assert_redirige_a_detalle(
            self.client.post(self.url, data={'archivo': make_file()}))

    @patch('lumat_app.views.Evidencia')
    @patch('lumat_app.views.get_object_or_404', return_value=seminario_mock())
    def test_exito_redirige_a_detalle(self, _, __):
        self._assert_redirige_a_detalle(
            self.client.post(self.url, data={'archivo': make_pdf()}))


# ─────────────────────────────────────────────────────────────
# 6. Casos negativos
# ─────────────────────────────────────────────────────────────

class SubirEvidenciaCasosNegativosTests(BaseAuthTests):

    @patch('lumat_app.views.get_object_or_404', return_value=seminario_mock())
    def test_archivo_tamano_cero_mime_correcto_es_valido(self, _):
        archivo = SimpleUploadedFile(
            'vacio.pdf', b'', content_type='application/pdf')
        with patch('lumat_app.views.Evidencia'):
            r = self.client.post(self.url, data={'archivo': archivo})
        self.assertFalse(any('10 MB' in m for m in messages_list(r)))

    @patch('lumat_app.views.get_object_or_404', return_value=seminario_mock())
    def test_multiples_errores_solo_primer_mensaje(self, _):
        r = self.client.post(self.url, data={})
        self.assertEqual(len(messages_list(r)), 1)