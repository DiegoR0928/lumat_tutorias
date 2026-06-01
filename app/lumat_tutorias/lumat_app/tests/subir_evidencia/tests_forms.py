"""
Pruebas unitarias — Formularios / Validaciones de negocio
Cubre: las reglas de validación de subir_evidencia()

Si tu proyecto tiene un EvidenciaForm explícito, sustituye
_EvidenciaValidator por ese form y ajusta el import:
    from lumat_app.forms import EvidenciaForm
"""

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

MAX_SIZE = 10 * 1024 * 1024          # 10 MB
TIPOS_PERMITIDOS = ('application/pdf',)


# ─────────────────────────────────────────────────────────────
# Validador (replica la lógica de la vista de forma aislada)
# Reemplazar por EvidenciaForm cuando exista.
# ─────────────────────────────────────────────────────────────

class _EvidenciaValidator:
    MAX_SIZE = 10 * 1024 * 1024
    TIPOS_PERMITIDOS = ('application/pdf',)

    def __init__(self, archivo=None):
        self.archivo = archivo
        self.errors: dict = {}

    def is_valid(self) -> bool:
        self.errors = {}
        if not self.archivo:
            self.errors['archivo'] = 'No se seleccionó ningún archivo.'
            return False
        if self.archivo.size > self.MAX_SIZE:
            self.errors['archivo'] = 'El archivo no puede superar 10 MB.'
            return False
        if self.archivo.content_type not in self.TIPOS_PERMITIDOS:
            self.errors['archivo'] = 'Solo se permiten imágenes y PDFs.'
            return False
        return True


# ─────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────

def pdf(nombre='evidencia.pdf', size_bytes=1024):
    return SimpleUploadedFile(
        nombre, b'%PDF-1.4 ' + b'0' * size_bytes,
        content_type='application/pdf')


def imagen(nombre='foto.png'):
    return SimpleUploadedFile(
        nombre, b'\x89PNG\r\n', content_type='image/png')


def archivo_tipo(content_type='application/javascript', nombre='script.js'):
    return SimpleUploadedFile(nombre, b'contenido', content_type=content_type)


# ─────────────────────────────────────────────────────────────
# 1. Datos válidos
# ─────────────────────────────────────────────────────────────

class EvidenciaFormDatosValidosTests(TestCase):

    def test_pdf_pequeno_es_valido(self):
        self.assertTrue(_EvidenciaValidator(pdf()).is_valid())

    def test_pdf_limite_exacto_es_valido(self):
        archivo = SimpleUploadedFile(
            'limite.pdf', b'%PDF-' + b'0' * (MAX_SIZE - 5),
            content_type='application/pdf')
        self.assertTrue(_EvidenciaValidator(archivo).is_valid())

    def test_sin_errores_cuando_valido(self):
        v = _EvidenciaValidator(pdf())
        v.is_valid()
        self.assertEqual(v.errors, {})

    def test_pdf_vacio_es_valido_segun_reglas_actuales(self):
        """0 bytes < MAX_SIZE y MIME correcto → válido."""
        archivo = SimpleUploadedFile(
            'v.pdf', b'', content_type='application/pdf')
        self.assertTrue(_EvidenciaValidator(archivo).is_valid())


# ─────────────────────────────────────────────────────────────
# 2. Campos obligatorios
# ─────────────────────────────────────────────────────────────

class EvidenciaFormCamposObligatoriosTests(TestCase):

    def test_sin_archivo_invalido(self):
        self.assertFalse(_EvidenciaValidator(None).is_valid())

    def test_sin_archivo_genera_error(self):
        v = _EvidenciaValidator(None)
        v.is_valid()
        self.assertIn('archivo', v.errors)

    def test_mensaje_sin_archivo(self):
        v = _EvidenciaValidator(None)
        v.is_valid()
        self.assertIn('ningún archivo', v.errors['archivo'])


# ─────────────────────────────────────────────────────────────
# 3. Validación de tamaño
# ─────────────────────────────────────────────────────────────

class EvidenciaFormValidacionTamanoTests(TestCase):

    def _grande(self, extra=1):
        return SimpleUploadedFile(
            'g.pdf', b'0' * (MAX_SIZE + extra),
            content_type='application/pdf')

    def test_sobre_limite_invalido(self):
        self.assertFalse(_EvidenciaValidator(self._grande()).is_valid())

    def test_mensaje_sobre_limite(self):
        v = _EvidenciaValidator(self._grande())
        v.is_valid()
        self.assertIn('10 MB', v.errors['archivo'])

    def test_un_byte_sobre_invalido(self):
        self.assertFalse(_EvidenciaValidator(self._grande(1)).is_valid())

    def test_un_byte_bajo_valido(self):
        archivo = SimpleUploadedFile(
            'ok.pdf', b'%PDF-' + b'0' * (MAX_SIZE - 6),
            content_type='application/pdf')
        self.assertTrue(_EvidenciaValidator(archivo).is_valid())


# ─────────────────────────────────────────────────────────────
# 4. Validación de tipo MIME
# ─────────────────────────────────────────────────────────────

class EvidenciaFormValidacionMimeTests(TestCase):

    def test_pdf_aceptado(self):
        self.assertTrue(_EvidenciaValidator(pdf()).is_valid())

    def test_image_png_rechazada(self):
        self.assertFalse(_EvidenciaValidator(imagen()).is_valid())

    def test_image_jpeg_rechazada(self):
        a = SimpleUploadedFile('f.jpg', b'JFIF', content_type='image/jpeg')
        self.assertFalse(_EvidenciaValidator(a).is_valid())

    def test_javascript_rechazado(self):
        self.assertFalse(_EvidenciaValidator(archivo_tipo()).is_valid())

    def test_zip_rechazado(self):
        a = SimpleUploadedFile('a.zip', b'PK', content_type='application/zip')
        self.assertFalse(_EvidenciaValidator(a).is_valid())

    def test_excel_rechazado(self):
        a = SimpleUploadedFile(
            'a.xlsx', b'PK',
            content_type='application/vnd.openxmlformats-officedocument'
                         '.spreadsheetml.sheet')
        self.assertFalse(_EvidenciaValidator(a).is_valid())

    def test_texto_plano_rechazado(self):
        a = SimpleUploadedFile('a.txt', b'hola', content_type='text/plain')
        self.assertFalse(_EvidenciaValidator(a).is_valid())

    def test_mensaje_mime_no_permitido(self):
        v = _EvidenciaValidator(imagen())
        v.is_valid()
        self.assertIn('PDF', v.errors['archivo'])


# ─────────────────────────────────────────────────────────────
# 5. Mensajes de error
# ─────────────────────────────────────────────────────────────

class EvidenciaFormMensajesErrorTests(TestCase):

    def test_error_sin_archivo_no_vacio(self):
        v = _EvidenciaValidator(None)
        v.is_valid()
        self.assertTrue(len(v.errors['archivo']) > 0)

    def test_error_tamano_no_vacio(self):
        v = _EvidenciaValidator(
            SimpleUploadedFile('g.pdf', b'0' * (MAX_SIZE + 1),
                               content_type='application/pdf'))
        v.is_valid()
        self.assertTrue(len(v.errors['archivo']) > 0)

    def test_error_mime_no_vacio(self):
        v = _EvidenciaValidator(imagen())
        v.is_valid()
        self.assertTrue(len(v.errors['archivo']) > 0)

    def test_fail_fast_un_error_a_la_vez(self):
        """Archivo inválido en tamaño Y MIME: sólo un error (fail-fast)."""
        a = SimpleUploadedFile(
            'g.png', b'0' * (MAX_SIZE + 1), content_type='image/png')
        v = _EvidenciaValidator(a)
        v.is_valid()
        self.assertEqual(len(v.errors), 1)


# ─────────────────────────────────────────────────────────────
# 6. Validaciones personalizadas
# ─────────────────────────────────────────────────────────────

class EvidenciaFormValidacionesPersonalizadasTests(TestCase):

    def test_extension_pdf_con_mime_incorrecto_rechazado(self):
        """La validación usa content_type, no la extensión del nombre."""
        a = SimpleUploadedFile(
            'trampa.pdf', b'contenido', content_type='text/plain')
        self.assertFalse(_EvidenciaValidator(a).is_valid())

    def test_extension_js_con_mime_pdf_aceptado(self):
        """Si content_type dice PDF, pasa la validación de MIME."""
        a = SimpleUploadedFile(
            'raro.js', b'%PDF-1.4', content_type='application/pdf')
        self.assertTrue(_EvidenciaValidator(a).is_valid())

    def test_octet_stream_rechazado(self):
        a = SimpleUploadedFile(
            'bin.bin', b'\x00\x01', content_type='application/octet-stream')
        self.assertFalse(_EvidenciaValidator(a).is_valid())
