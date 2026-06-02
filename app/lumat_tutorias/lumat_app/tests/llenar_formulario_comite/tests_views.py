from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User, Group
from decimal import Decimal
from unittest.mock import patch
from lumat_app.models import Seminario, Alumno, Comite, FormularioComite, Docente
from datetime import date


class DocenteSeminariosViewTest(TestCase):
    """Pruebas para la vista docente_seminarios"""
    
    def setUp(self):
        # Crear grupo Docente
        self.docente_group, _ = Group.objects.get_or_create(name='Docente')
        
        # Crear usuario docente
        self.user = User.objects.create_user(
            username='docente1',
            password='testpass123',
            email='docente@test.com'
        )
        self.user.groups.add(self.docente_group)
        
        # Crear perfil docente
        self.docente = Docente.objects.create(
            user=self.user,
            nombre="Carlos",
            apellido_paterno="Lopez",
            apellido_materno="Garcia",
            correo="docente@test.com"
        )
        
        # Crear otros docentes para el comité (diferentes)
        self.user_otro1 = User.objects.create_user(
            username='otro1',
            password='testpass123',
            email='otro1@test.com'
        )
        self.docente_otro1 = Docente.objects.create(
            user=self.user_otro1,
            nombre="Maria",
            apellido_paterno="Martinez",
            apellido_materno="Rodriguez",
            correo="otro1@test.com"
        )
        
        self.user_otro2 = User.objects.create_user(
            username='otro2',
            password='testpass123',
            email='otro2@test.com'
        )
        self.docente_otro2 = Docente.objects.create(
            user=self.user_otro2,
            nombre="Jose",
            apellido_paterno="Sanchez",
            apellido_materno="Perez",
            correo="otro2@test.com"
        )
        
        # Crear usuario alumno
        self.user_alumno = User.objects.create_user(
            username='alumno1',
            password='testpass123',
            email='alumno@test.com'
        )
        
        # Crear alumno
        self.alumno = Alumno.objects.create(
            user=self.user_alumno,
            nombre='Pedro',
            apellido_paterno='Gomez',
            apellido_materno='Lopez',
            matricula='20230001',
            semestre='7',
            correo='pedro@test.com'
        )
        
        # Crear comité con 3 docentes diferentes
        self.comite = Comite.objects.create(
            tutor=self.docente,
            miembro1=self.docente_otro1,
            miembro2=self.docente_otro2
        )
        
        # Crear seminario
        self.seminario = Seminario.objects.create(
            numero=7,
            periodo=1,
            fecha=date(2024, 12, 15),
            hora='10:00',
            alumno=self.alumno,
            comite=self.comite
        )
        
        # Crear formulario
        self.formulario = FormularioComite.objects.create(
            seminario=self.seminario
        )
        
        self.client = Client()
        self.client.login(username='docente1', password='testpass123')
    
    def test_vista_acceso_con_login(self):
        """Probar que la vista requiere login (código 200 con usuario logueado)"""
        response = self.client.get(reverse('lumat_app:docente_seminarios'))
        self.assertEqual(response.status_code, 200)
    
    def test_redireccion_sin_login(self):
        """Probar que redirige si no hay login"""
        self.client.logout()
        response = self.client.get(reverse('lumat_app:docente_seminarios'))
        self.assertEqual(response.status_code, 302)
    
    def test_template_correcto(self):
        """Probar que usa el template correcto"""
        response = self.client.get(reverse('lumat_app:docente_seminarios'))
        self.assertTemplateUsed(response, 'docente_seminario.html')
    
    def test_contexto_docente(self):
        """Probar que el contexto contiene al docente"""
        response = self.client.get(reverse('lumat_app:docente_seminarios'))
        self.assertEqual(response.context['docente'], self.docente)
    
    def test_contexto_seminarios(self):
        """Probar que el contexto contiene la lista de seminarios"""
        response = self.client.get(reverse('lumat_app:docente_seminarios'))
        self.assertIn('seminarios', response.context)
    
    def test_acceso_denegado_usuario_no_docente(self):
        """Probar que un usuario que no es docente no puede acceder"""
        self.client.logout()
        user_normal = User.objects.create_user(username='normal', password='pass')
        self.client.login(username='normal', password='pass')
        
        response = self.client.get(reverse('lumat_app:docente_seminarios'))
        self.assertEqual(response.status_code, 302)


class DocenteFirmarSeminarioViewTest(TestCase):
    """Pruebas para la vista docente_firmar_seminario"""
    
    def setUp(self):
        self.docente_group, _ = Group.objects.get_or_create(name='Docente')
        
        self.user = User.objects.create_user(
            username='docente',
            password='testpass123',
            email='docente@test.com'
        )
        self.user.groups.add(self.docente_group)
        
        self.docente = Docente.objects.create(
            user=self.user,
            nombre="Carlos",
            apellido_paterno="Lopez",
            apellido_materno="Garcia",
            correo="docente@test.com"
        )
        
        # Crear otros docentes para el comité (diferentes)
        self.user_otro1 = User.objects.create_user(
            username='otro1_firmar',
            password='testpass123',
            email='otro1_firmar@test.com'
        )
        self.docente_otro1 = Docente.objects.create(
            user=self.user_otro1,
            nombre="Maria",
            apellido_paterno="Martinez",
            apellido_materno="Rodriguez",
            correo="otro1_firmar@test.com"
        )
        
        self.user_otro2 = User.objects.create_user(
            username='otro2_firmar',
            password='testpass123',
            email='otro2_firmar@test.com'
        )
        self.docente_otro2 = Docente.objects.create(
            user=self.user_otro2,
            nombre="Jose",
            apellido_paterno="Sanchez",
            apellido_materno="Perez",
            correo="otro2_firmar@test.com"
        )
        
        self.user_alumno = User.objects.create_user(
            username='alumno_firmar',
            password='testpass123',
            email='alumno_firmar@test.com'
        )
        
        self.alumno = Alumno.objects.create(
            user=self.user_alumno,
            nombre='Carlos',
            apellido_paterno='Ramirez',
            apellido_materno='Torres',
            matricula='20230003',
            semestre='6',
            correo='carlos@test.com'
        )
        
        # Crear comité con 3 docentes diferentes
        self.comite = Comite.objects.create(
            tutor=self.docente,
            miembro1=self.docente_otro1,
            miembro2=self.docente_otro2
        )
        
        self.seminario = Seminario.objects.create(
            numero=6,
            periodo=1,
            fecha=date(2024, 12, 25),
            hora='09:00',
            alumno=self.alumno,
            comite=self.comite
        )
        
        self.formulario = FormularioComite.objects.create(
            seminario=self.seminario
        )
        
        self.client = Client()
        self.client.login(username='docente', password='testpass123')
        self.url = reverse('lumat_app:docente_firmar_seminario', args=[self.seminario.id])
    
    def test_redireccion_si_no_post(self):
        """Probar que redirige si no es método POST"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
    
    def test_firmar_con_calificacion_valida(self):
        """Probar que puede firmar con calificación válida"""
        post_data = {
            'calificacion': '9.0',
            'confirmar_firma': True
        }
        response = self.client.post(self.url, post_data)
        self.assertEqual(response.status_code, 302)
        
        self.formulario.refresh_from_db()
        self.assertTrue(self.formulario.firma_tutor)
        self.assertEqual(self.formulario.calificacion_tutor, Decimal('9.0'))
    
    def test_no_puede_firmar_dos_veces(self):
        """Probar que no puede firmar dos veces"""
        self.formulario.firma_tutor = True
        self.formulario.calificacion_tutor = Decimal('8.0')
        self.formulario.save()
        
        post_data = {
            'calificacion': '9.0',
            'confirmar_firma': True
        }
        response = self.client.post(self.url, post_data, follow=True)
        
        messages = list(response.context['messages'])
        self.assertTrue(any('Ya habías firmado' in str(m) for m in messages))
        
        self.formulario.refresh_from_db()
        self.assertEqual(self.formulario.calificacion_tutor, Decimal('8.0'))
    
    def test_calificacion_invalida(self):
        """Probar que rechaza calificación inválida"""
        post_data = {
            'calificacion': '15',
            'confirmar_firma': True
        }
        response = self.client.post(self.url, post_data, follow=True)
        
        messages = list(response.context['messages'])
        self.assertTrue(any('Datos inválidos' in str(m) for m in messages))
        
        self.formulario.refresh_from_db()
        self.assertFalse(self.formulario.firma_tutor)