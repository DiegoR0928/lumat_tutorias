from django.test import TestCase
from django.urls import reverse, resolve
from lumat_app import views  # ajusta al nombre real de tu app


class RegistroURLTest(TestCase):

    # ------------------------------------------------------------------
    # reverse()
    # ------------------------------------------------------------------

    def test_reverse_registro_genera_url_correcta(self):
        """reverse() para 'registro' genera la URL /registro/."""
        url = reverse('lumat_app:registro')
        self.assertEqual(url, '/registro/')

    # ------------------------------------------------------------------
    # resolve()
    # ------------------------------------------------------------------

    def test_resolve_registro_apunta_a_view_correcta(self):
        """resolve() para /registro/ apunta a la función views.registro."""
        resultado = resolve('/registro/')
        self.assertEqual(resultado.func, views.registro)

    # ------------------------------------------------------------------
    # Nombre correcto
    # ------------------------------------------------------------------

    def test_nombre_url_es_registro(self):
        """La URL resuelta tiene el nombre 'registro'."""
        resultado = resolve('/registro/')
        self.assertEqual(resultado.url_name, 'registro')

    # ------------------------------------------------------------------
    # Namespace correcto
    # ------------------------------------------------------------------

    def test_namespace_url_es_lumat_app(self):
        """La URL resuelta pertenece al namespace 'lumat_app'."""
        resultado = resolve('/registro/')
        self.assertEqual(resultado.namespace, 'lumat_app')
