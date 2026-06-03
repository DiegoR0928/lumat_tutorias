from django.test import TestCase
from django.urls import reverse, resolve
from lumat_app.views_docente import docente_descargar_acta


class DocenteDescargarActaUrlsTest(TestCase):

    def test_resolucion_url_descargar_acta(self):
        """Verifica que el nombre de la ruta resuelva a la vista correcta con su ID."""
        url_calculada = reverse(
            'lumat_app:docente_descargar_acta', kwargs={'seminario_id': 5})
        self.assertEqual(url_calculada, '/docente/seminarios/5/acta/')

        match = resolve('/docente/seminarios/5/acta/')
        self.assertEqual(match.func, docente_descargar_acta)
