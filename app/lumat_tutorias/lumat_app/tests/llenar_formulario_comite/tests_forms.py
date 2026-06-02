from django.test import TestCase
from decimal import Decimal
from lumat_app.forms import FormularioComiteForm, FirmaCalificacionForm


class FormularioComiteFormTest(TestCase):
    """Pruebas simples para FormularioComiteForm"""
    
    def test_formulario_valido_con_datos_completos(self):
        """Probar que el formulario es válido con datos correctos"""
        form_data = {
            'el_comite_encuentra': 'El alumno demostró dominio del tema',
            'observaciones': 'Excelente presentación y defensa',
            'dictamen': 'Aprobado por unanimidad',
            'propuestas': 'Publicar resultados en revista indexada'
        }
        form = FormularioComiteForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_campos_obligatorios_no_son_requeridos(self):
        """Probar que todos los campos son opcionales (blank=True)"""
        form_data = {
            'el_comite_encuentra': '',
            'observaciones': '',
            'dictamen': '',
            'propuestas': ''
        }
        form = FormularioComiteForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_campos_correctos_en_meta(self):
        """Probar que los campos del Meta son correctos"""
        expected_fields = [
            'el_comite_encuentra',
            'observaciones',
            'dictamen',
            'propuestas'
        ]
        self.assertEqual(list(FormularioComiteForm.Meta.fields), expected_fields)
    
    def test_labels_personalizados(self):
        """Probar que las etiquetas están personalizadas"""
        form = FormularioComiteForm()
        self.assertEqual(form.fields['el_comite_encuentra'].label, 
                        'El Comité encuentra que el estudiante')
        self.assertEqual(form.fields['observaciones'].label,
                        'Otros aspectos observados por el Comité')
        self.assertEqual(form.fields['dictamen'].label, 'Dictamen')
        self.assertEqual(form.fields['propuestas'].label, 'Plan de trabajo propuesto')


class FirmaCalificacionFormTest(TestCase):
    """Pruebas simples para FirmaCalificacionForm"""
    
    def test_formulario_valido_con_datos_correctos(self):
        """Probar que el formulario es válido con datos correctos"""
        form_data = {
            'calificacion': '8.50',
            'confirmar_firma': True
        }
        form = FirmaCalificacionForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_calificacion_minima_0(self):
        """Probar que acepta calificación 0"""
        form_data = {
            'calificacion': '0',
            'confirmar_firma': True
        }
        form = FirmaCalificacionForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_calificacion_maxima_10(self):
        """Probar que acepta calificación 10"""
        form_data = {
            'calificacion': '10',
            'confirmar_firma': True
        }
        form = FirmaCalificacionForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_calificacion_invalida_negativa(self):
        """Probar que rechaza calificación negativa"""
        form_data = {
            'calificacion': '-1',
            'confirmar_firma': True
        }
        form = FirmaCalificacionForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('calificacion', form.errors)
    
    def test_calificacion_invalida_mayor_10(self):
        """Probar que rechaza calificación mayor a 10"""
        form_data = {
            'calificacion': '10.5',
            'confirmar_firma': True
        }
        form = FirmaCalificacionForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('calificacion', form.errors)
    
    def test_campo_confirmar_firma_es_requerido(self):
        """Probar que confirmar_firma es requerido"""
        form_data = {
            'calificacion': '8.50',
            'confirmar_firma': False
        }
        form = FirmaCalificacionForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('confirmar_firma', form.errors)