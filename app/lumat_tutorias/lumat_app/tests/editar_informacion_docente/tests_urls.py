from django.test import TestCase
from django.urls import reverse, resolve
from lumat_app.views_docente import editar_perfil_docente


class DocenteUrlsSimpleTest(TestCase):

    def test_resolucion_y_reversa_perfil_docente(self):
        """Verifica que el nombre de la ruta apunte directamente a la función de la vista."""
        url_calculada = reverse('lumat_app:perfil_docente')
        self.assertEqual(url_calculada, '/docente/perfil/')

        match = resolve('/docente/perfil/')
        self.assertEqual(match.func, editar_perfil_docente)
