from django.test import SimpleTestCase
from django.urls import reverse, resolve
from lumat_app import views_docente


class DocenteUrlsTest(SimpleTestCase):
    """Pruebas simples para las URLs de docente"""

    def test_docente_seminarios_url_resolve(self):
        """Probar que la URL de lista de seminarios resuelve correctamente"""
        resolver = resolve('/docente/seminarios/')
        self.assertEqual(resolver.func, views_docente.docente_seminarios)

    def test_docente_seminario_detalle_url_resolve(self):
        """Probar que la URL de detalle resuelve correctamente"""
        resolver = resolve('/docente/seminarios/123/')
        self.assertEqual(
            resolver.func, views_docente.docente_seminario_detalle)

    def test_docente_firmar_url_resolve(self):
        """Probar que la URL de firmar resuelve correctamente"""
        resolver = resolve('/docente/seminarios/456/firmar/')
        self.assertEqual(resolver.func, views_docente.docente_firmar_seminario)

    def test_descargar_acta_url_resolve(self):
        """Probar que la URL de descargar acta resuelve correctamente"""
        resolver = resolve('/docente/seminarios/789/acta/')
        self.assertEqual(resolver.func, views_docente.docente_descargar_acta)

    def test_reverse_nombres_urls(self):
        """Probar que reverse funciona con los nombres de las URLs"""
        url = reverse('lumat_app:docente_seminarios')
        self.assertEqual(url, '/docente/seminarios/')

        url = reverse('lumat_app:docente_seminario_detalle', args=[1])
        self.assertEqual(url, '/docente/seminarios/1/')

        url = reverse('lumat_app:docente_firmar_seminario', args=[1])
        self.assertEqual(url, '/docente/seminarios/1/firmar/')

        url = reverse('lumat_app:docente_descargar_acta', args=[1])
        self.assertEqual(url, '/docente/seminarios/1/acta/')
