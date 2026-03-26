from django.test import TestCase

class SmokeTest(TestCase):
    def test_hola_mundo(self):
        self.assertEqual(1 + 1, 2)
    
    