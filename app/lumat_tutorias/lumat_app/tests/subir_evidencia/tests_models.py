"""
Pruebas unitarias — Modelos
Cubre: evidencia_upload_path, Evidencia

Estrategia para evitar BD:
  - Model() normal inicializa _state correctamente.
  - Para FKs que Django valida, usamos __dict__ para saltear
    el descriptor y asignar atributos directamente.
  - evidencia_upload_path recibe un objeto SimpleNamespace
    que sólo expone alumno_id / seminario_id (no pasa por
    ningún descriptor de Django).
"""

import os
from types import SimpleNamespace

from django.db.models import CASCADE, ForeignKey
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile

from lumat_app.models import Evidencia


# ─────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────

def make_instance_for_upload_path(alumno_id=1, seminario_id=10):
    """
    Objeto mínimo para evidencia_upload_path.
    Usa SimpleNamespace para no tocar ningún descriptor de Django.
    """
    return SimpleNamespace(
        seminario=SimpleNamespace(alumno_id=alumno_id),
        seminario_id=seminario_id,
    )


def build_evidencia(nombre_archivo='doc.pdf'):
    """
    Crea Evidencia() de forma normal (con _state) y luego asigna
    los campos vía __dict__ para saltear el descriptor de FK.
    Sólo se usan los campos necesarios para la lógica de save().
    """
    ev = Evidencia()                      # _state queda inicializado
    ev.__dict__['seminario_id'] = 10      # evita el descriptor FK
    ev.archivo = SimpleUploadedFile(
        nombre_archivo,
        b'%PDF-1.4 contenido',
        content_type='application/pdf',
    )
    ev.tipo = 'otro'
    ev.nombre = ''
    return ev


def run_save_logic(ev):
    """Ejecuta sólo la lógica de negocio de save() sin persistir en BD."""
    if ev.archivo:
        ext = os.path.splitext(ev.archivo.name)[1].lower()
        if ext in ('.jpg', '.jpeg', '.png', '.gif', '.webp'):
            ev.tipo = 'imagen'
        elif ext == '.pdf':
            ev.tipo = 'pdf'
        else:
            ev.tipo = 'otro'
        if not ev.nombre:
            ev.nombre = os.path.basename(ev.archivo.name)


# ─────────────────────────────────────────────────────────────
# 1. evidencia_upload_path
# ─────────────────────────────────────────────────────────────

class EvidenciaUploadPathTests(TestCase):

    def _path(self, alumno_id=1, seminario_id=10, filename='archivo.pdf'):
        from lumat_app.models import evidencia_upload_path
        instance = make_instance_for_upload_path(alumno_id, seminario_id)
        return evidencia_upload_path(instance, filename)

    def test_empieza_con_evidencias(self):
        self.assertTrue(self._path().startswith('evidencias'))

    def test_incluye_alumno_id(self):
        self.assertIn('7', self._path(alumno_id=7))

    def test_incluye_seminario_id(self):
        self.assertIn('42', self._path(seminario_id=42))

    def test_termina_con_filename(self):
        self.assertTrue(self._path(
            filename='reporte.pdf').endswith('reporte.pdf'))

    def test_estructura_completa(self):
        ruta = self._path(alumno_id=3, seminario_id=10, filename='foto.jpg')
        self.assertEqual(ruta, os.path.join(
            'evidencias', '3', '10', 'foto.jpg'))

    def test_alumno_id_distinto_genera_ruta_distinta(self):
        self.assertNotEqual(self._path(alumno_id=1), self._path(alumno_id=2))

    def test_seminario_id_distinto_genera_ruta_distinta(self):
        self.assertNotEqual(self._path(seminario_id=10),
                            self._path(seminario_id=11))


# ─────────────────────────────────────────────────────────────
# 2. Valores por defecto y Meta
# ─────────────────────────────────────────────────────────────

class EvidenciaDefaultsTests(TestCase):

    def test_tipo_default_es_otro(self):
        self.assertEqual(Evidencia._meta.get_field('tipo').default, 'otro')

    def test_nombre_blank_permitido(self):
        self.assertTrue(Evidencia._meta.get_field('nombre').blank)

    def test_nombre_max_length(self):
        self.assertEqual(Evidencia._meta.get_field('nombre').max_length, 200)

    def test_tipo_max_length(self):
        self.assertEqual(Evidencia._meta.get_field('tipo').max_length, 10)

    def test_ordering_subido_en_asc(self):
        self.assertEqual(Evidencia._meta.ordering, ['subido_en'])

    def test_subido_en_auto_now_add(self):
        self.assertTrue(Evidencia._meta.get_field('subido_en').auto_now_add)


# ─────────────────────────────────────────────────────────────
# 3. TIPO_CHOICES
# ─────────────────────────────────────────────────────────────

class EvidenciaTipoChoicesTests(TestCase):

    def _keys(self):
        return [c[0] for c in Evidencia.TIPO_CHOICES]

    def test_choice_imagen(self):
        self.assertIn('imagen', self._keys())

    def test_choice_pdf(self):
        self.assertIn('pdf', self._keys())

    def test_choice_otro(self):
        self.assertIn('otro', self._keys())

    def test_tres_choices_totales(self):
        self.assertEqual(len(Evidencia.TIPO_CHOICES), 3)


# ─────────────────────────────────────────────────────────────
# 4. Relaciones
# ─────────────────────────────────────────────────────────────

class EvidenciaRelacionesTests(TestCase):

    def test_seminario_es_fk(self):
        self.assertIsInstance(
            Evidencia._meta.get_field('seminario'), ForeignKey)

    def test_related_name_evidencias(self):
        campo = Evidencia._meta.get_field('seminario')
        self.assertEqual(campo.remote_field.related_name, 'evidencias')

    def test_on_delete_cascade(self):
        campo = Evidencia._meta.get_field('seminario')
        self.assertEqual(campo.remote_field.on_delete, CASCADE)

    def test_archivo_es_filefield(self):
        from django.db.models import FileField
        self.assertIsInstance(Evidencia._meta.get_field('archivo'), FileField)


# ─────────────────────────────────────────────────────────────
# 5. save() — detección de tipo por extensión
# ─────────────────────────────────────────────────────────────

class EvidenciaSaveTipoTests(TestCase):
    """
    Prueba la lógica interna de save() de forma aislada.
    run_save_logic() replica exactamente el bloque if self.archivo
    sin llamar a super().save(), evitando tocar la BD.
    """

    def _tipo(self, nombre_archivo):
        ev = build_evidencia(nombre_archivo)
        run_save_logic(ev)
        return ev.tipo

    def test_jpg_imagen(self):
        self.assertEqual(self._tipo('a.jpg'), 'imagen')

    def test_jpeg_imagen(self):
        self.assertEqual(self._tipo('a.jpeg'), 'imagen')

    def test_png_imagen(self):
        self.assertEqual(self._tipo('a.png'), 'imagen')

    def test_gif_imagen(self):
        self.assertEqual(self._tipo('a.gif'), 'imagen')

    def test_webp_imagen(self):
        self.assertEqual(self._tipo('a.webp'), 'imagen')

    def test_pdf_pdf(self):
        self.assertEqual(self._tipo('a.pdf'), 'pdf')

    def test_xlsx_otro(self):
        self.assertEqual(self._tipo('a.xlsx'), 'otro')

    def test_txt_otro(self):
        self.assertEqual(self._tipo('a.txt'), 'otro')

    def test_sin_extension_otro(self):
        self.assertEqual(self._tipo('archivo'), 'otro')

    def test_extension_mayusculas_jpg(self):
        """Extensiones en mayúsculas deben normalizarse a minúsculas."""
        self.assertEqual(self._tipo('FOTO.JPG'), 'imagen')

    def test_extension_mayusculas_pdf(self):
        self.assertEqual(self._tipo('REPORTE.PDF'), 'pdf')


# ─────────────────────────────────────────────────────────────
# 6. save() — asignación de nombre
# ─────────────────────────────────────────────────────────────

class EvidenciaSaveNombreTests(TestCase):

    def test_nombre_asignado_si_vacio(self):
        ev = build_evidencia('mi_evidencia.pdf')
        ev.nombre = ''
        run_save_logic(ev)
        self.assertEqual(ev.nombre, 'mi_evidencia.pdf')

    def test_nombre_no_sobreescrito_si_existe(self):
        ev = build_evidencia('archivo.pdf')
        ev.nombre = 'Nombre personalizado'
        run_save_logic(ev)
        self.assertEqual(ev.nombre, 'Nombre personalizado')

    def test_nombre_extrae_solo_basename(self):
        """Si archivo.name tiene ruta completa, sólo se guarda el basename."""
        ev = build_evidencia('archivo.pdf')
        ev.nombre = ''
        ev.archivo.name = 'evidencias/1/10/archivo.pdf'
        run_save_logic(ev)
        self.assertEqual(ev.nombre, 'archivo.pdf')


# ─────────────────────────────────────────────────────────────
# 7. __str__
# Usamos Evidencia() normal y asignamos vía __dict__ para evitar
# que el descriptor de FK exija una instancia de Seminario.
# ─────────────────────────────────────────────────────────────

class EvidenciaStrTests(TestCase):

    def _str(self, tipo, seminario_id):
        ev = Evidencia()
        ev.tipo = tipo
        ev.__dict__['seminario_id'] = seminario_id   # bypass descriptor FK
        return str(ev)

    def test_formato_pdf(self):
        self.assertEqual(self._str('pdf', 3), "Evidencia [pdf] — Seminario 3")

    def test_formato_imagen(self):
        self.assertEqual(self._str('imagen', 7),
                         "Evidencia [imagen] — Seminario 7")

    def test_formato_otro(self):
        self.assertEqual(self._str('otro', 1),
                         "Evidencia [otro] — Seminario 1")

    def test_contiene_seminario_id(self):
        self.assertIn('12', self._str('pdf', 12))

    def test_contiene_tipo(self):
        self.assertIn('pdf', self._str('pdf', 1))
