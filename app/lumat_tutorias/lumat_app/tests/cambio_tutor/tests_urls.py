from django.test import SimpleTestCase
from django.urls import reverse, resolve

from lumat_app.views import cambio_tutor


class UrlsTest(SimpleTestCase):

    def test_url_cambio_tutor_resuelve(self):

        url = reverse(
            "lumat_app:cambio_tutor"
        )

        self.assertEqual(
            resolve(url).func,
            cambio_tutor
        )
