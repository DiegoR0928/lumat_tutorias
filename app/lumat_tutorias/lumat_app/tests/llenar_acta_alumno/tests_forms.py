from django.test import TestCase
from lumat_app.forms import ActaAlumnoForm


class ActaAlumnoFormTest(TestCase):

    def test_form_datos_validos(self):
        """El formulario procesa datos correctos incluyendo números enteros."""
        payload = {
            'actividad_principal': 'Investigación en física computacional',
            'cursos': 'Métodos Numéricos Avanzados',
            'articulos': 'No tengo artículos este semestre',
            'eventos': 'Asistencia al coloquio anual',
            'plan_siguiente': 'Redacción de capítulo 1 de tesis',
            'comentarios': 'Todo excelente',
            'reuniones_tutor': 5,
            'reuniones_comite': 2,
            'coloquios': 1
        }
        form = ActaAlumnoForm(data=payload)
        self.assertTrue(form.is_valid())

    def test_form_campos_invalidos(self):
        """El formulario falla si se mandan datos de tipo erróneo (ej. letras en enteros)."""
        payload = {
            'actividad_principal': 'Corto',
            'reuniones_tutor': 'Cinco',  # Debería ser un número entero
        }
        form = ActaAlumnoForm(data=payload)
        self.assertFalse(form.is_valid())
        self.assertIn('reuniones_tutor', form.errors)
