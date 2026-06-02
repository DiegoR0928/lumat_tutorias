from django.test import TestCase
from django.contrib.auth.models import User
from decimal import Decimal
from lumat_app.models import Seminario, Alumno, Comite, FormularioComite, Docente
from datetime import date


class FormularioComiteModelTest(TestCase):
    """Pruebas simples para el modelo FormularioComite"""
    
    def setUp(self):
        # Crear usuario para el alumno
        self.user_alumno = User.objects.create_user(
            username='alumno_test',
            password='testpass123',
            email='alumno@test.com'
        )
        
        # Crear alumno
        self.alumno = Alumno.objects.create(
            user=self.user_alumno,
            nombre="Juan",
            apellido_paterno="Perez",
            apellido_materno="Lopez",
            matricula="20220001",
            semestre="5",
            correo="juan@test.com"
        )
        
        # Crear usuarios para docentes (3 diferentes)
        self.user_tutor = User.objects.create_user(
            username='tutor_test',
            password='testpass123',
            email='tutor@test.com'
        )
        self.user_miembro1 = User.objects.create_user(
            username='miembro1_test',
            password='testpass123',
            email='miembro1@test.com'
        )
        self.user_miembro2 = User.objects.create_user(
            username='miembro2_test',
            password='testpass123',
            email='miembro2@test.com'
        )
        
        # Crear docentes (3 diferentes)
        self.tutor = Docente.objects.create(
            user=self.user_tutor,
            nombre="Carlos",
            apellido_paterno="Lopez",
            apellido_materno="Garcia",
            correo="tutor@test.com"
        )
        
        self.miembro1 = Docente.objects.create(
            user=self.user_miembro1,
            nombre="Maria",
            apellido_paterno="Martinez",
            apellido_materno="Rodriguez",
            correo="miembro1@test.com"
        )
        
        self.miembro2 = Docente.objects.create(
            user=self.user_miembro2,
            nombre="Jose",
            apellido_paterno="Sanchez",
            apellido_materno="Perez",
            correo="miembro2@test.com"
        )
        
        # Crear comité con 3 docentes diferentes
        self.comite = Comite.objects.create(
            tutor=self.tutor,
            miembro1=self.miembro1,
            miembro2=self.miembro2
        )
        
        # Crear seminario
        self.seminario = Seminario.objects.create(
            numero=5,
            periodo=1,
            fecha=date(2024, 3, 15),
            hora="10:00",
            alumno=self.alumno,
            comite=self.comite
        )
        
        # Crear formulario
        self.formulario = FormularioComite.objects.create(
            seminario=self.seminario,
            el_comite_encuentra="El alumno demostró buen conocimiento",
            observaciones="Excelente presentación",
            dictamen="Aprobado",
            propuestas="Continuar con investigación"
        )
    
    def test_creacion_formulario(self):
        """Probar que se puede crear un formulario correctamente"""
        self.assertEqual(self.formulario.seminario, self.seminario)
        self.assertEqual(self.formulario.el_comite_encuentra, "El alumno demostró buen conocimiento")
        self.assertEqual(self.formulario.estado_general, "pendiente")
    
    def test_str_method(self):
        """Probar el método __str__"""
        expected = f"Formulario Comité — Seminario {self.seminario.id} (pendiente)"
        self.assertEqual(str(self.formulario), expected)
    
    def test_valores_por_defecto(self):
        """Probar valores por defecto - crear otro seminario para otro formulario"""
        # Crear otro seminario para probar valores por defecto
        otro_seminario = Seminario.objects.create(
            numero=6,
            periodo=1,
            fecha=date(2024, 4, 15),
            hora="11:00",
            alumno=self.alumno,
            comite=self.comite
        )
        nuevo_form = FormularioComite.objects.create(seminario=otro_seminario)
        self.assertFalse(nuevo_form.firma_tutor)
        self.assertFalse(nuevo_form.firma_miembro1)
        self.assertFalse(nuevo_form.firma_miembro2)
        self.assertEqual(nuevo_form.estado_general, "pendiente")
        self.assertIsNone(nuevo_form.calificacion_final)
    
    def test_todos_firmaron_property(self):
        """Probar la propiedad todos_firmaron"""
        # Inicialmente nadie ha firmado
        self.assertFalse(self.formulario.todos_firmaron)
        
        # Firmar tutor
        self.formulario.firma_tutor = True
        self.assertFalse(self.formulario.todos_firmaron)
        
        # Firmar miembro1
        self.formulario.firma_miembro1 = True
        self.assertFalse(self.formulario.todos_firmaron)
        
        # Firmar todos
        self.formulario.firma_miembro2 = True
        self.assertTrue(self.formulario.todos_firmaron)
    
    def test_calcular_calificacion_final(self):
        """Probar cálculo de calificación final"""
        self.formulario.calificacion_tutor = Decimal("8.5")
        self.formulario.calificacion_miembro1 = Decimal("9.0")
        self.formulario.calificacion_miembro2 = Decimal("7.5")
        
        resultado = self.formulario.calcular_calificacion_final()
        self.assertEqual(resultado, Decimal("8.33"))
    
    def test_calcular_calificacion_sin_datos(self):
        """Probar cálculo cuando no hay calificaciones"""
        resultado = self.formulario.calcular_calificacion_final()
        self.assertIsNone(resultado)
    
    def test_calcular_con_una_calificacion(self):
        """Probar cálculo con solo una calificación"""
        self.formulario.calificacion_tutor = Decimal("9.5")
        resultado = self.formulario.calcular_calificacion_final()
        self.assertEqual(resultado, Decimal("9.50"))
    
    def test_save_actualiza_estado_completo(self):
        """Probar que save() actualiza estado_general cuando todos firman"""
        self.formulario.firma_tutor = True
        self.formulario.firma_miembro1 = True
        self.formulario.firma_miembro2 = True
        self.formulario.save()
        
        self.assertEqual(self.formulario.estado_general, "completo")
    
    def test_save_actualiza_calificacion_seminario(self):
        """Probar que la calificación final se sincroniza con el seminario"""
        self.formulario.calificacion_tutor = Decimal("9.0")
        self.formulario.calificacion_miembro1 = Decimal("8.5")
        self.formulario.calificacion_miembro2 = Decimal("9.5")
        self.formulario.save()
        
        self.seminario.refresh_from_db()
        self.assertEqual(self.seminario.calificacion, Decimal("9.00"))
    
    def test_restriccion_one_to_one(self):
        """Probar que un seminario solo puede tener un formulario"""
        with self.assertRaises(Exception):
            FormularioComite.objects.create(seminario=self.seminario)
    
    def test_promocion_semestre_al_aprobar(self):
        """Probar que el alumno avanza de semestre al aprobar"""
        # Guardar semestre original como entero
        semestre_original = int(self.alumno.semestre)
        
        # Asegurar que el número del seminario coincide con el semestre
        # (esto es necesario para que la promoción funcione)
        self.seminario.numero = semestre_original
        self.seminario.save()
        
        # Completar todas las firmas y calificaciones
        self.formulario.firma_tutor = True
        self.formulario.firma_miembro1 = True
        self.formulario.firma_miembro2 = True
        self.formulario.calificacion_tutor = Decimal("8.0")
        self.formulario.calificacion_miembro1 = Decimal("8.0")
        self.formulario.calificacion_miembro2 = Decimal("8.0")
        self.formulario.save()
        
        self.alumno.refresh_from_db()
        # El semestre debería aumentar en 1
        self.assertEqual(int(self.alumno.semestre), semestre_original + 1)
    
    def test_no_promocion_si_nota_menor_6(self):
        """Probar que no promociona si la calificación es menor a 6"""
        semestre_original = self.alumno.semestre
        
        self.formulario.firma_tutor = True
        self.formulario.firma_miembro1 = True
        self.formulario.firma_miembro2 = True
        self.formulario.calificacion_tutor = Decimal("5.5")
        self.formulario.calificacion_miembro1 = Decimal("5.5")
        self.formulario.calificacion_miembro2 = Decimal("5.5")
        self.formulario.save()
        
        self.alumno.refresh_from_db()
        self.assertEqual(self.alumno.semestre, semestre_original)
    
    def test_no_promocion_si_no_firmas_completas(self):
        """Probar que no promociona si no han firmado todos"""
        semestre_original = self.alumno.semestre
        
        self.formulario.calificacion_tutor = Decimal("9.0")
        self.formulario.calificacion_miembro1 = Decimal("9.0")
        self.formulario.calificacion_miembro2 = Decimal("9.0")
        self.formulario.firma_tutor = True
        self.formulario.save()
        
        self.alumno.refresh_from_db()
        self.assertEqual(self.alumno.semestre, semestre_original)