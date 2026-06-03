from django.test import TestCase
from django.urls import reverse, resolve
from lumat_app.views import generar_acta_view


class ActaAlumnoUrlsTest(TestCase):

    def test_url_generar_acta_resuelve_a_su_vista(self):
        """Verifica que el nombre de la URL y su ruta física apunten a generar_acta_view."""
        url_name = reverse('lumat_app:generar_acta', kwargs={'num': 3})
        # Reemplaza por tu patrón real si difiere
        self.assertEqual(url_name, '/alumno/seminario/3/acta/')

        match = resolve('/alumno/seminario/3/acta/')
        self.assertEqual(match.func, generar_acta_view)
