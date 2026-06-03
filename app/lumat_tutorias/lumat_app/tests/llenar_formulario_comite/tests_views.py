from decimal import Decimal
from datetime import date
from unittest.mock import patch
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User, Group
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils.text import slugify

from lumat_app.models import Evidencia, Seminario, Alumno, Comite, FormularioComite, Docente


# ==================== HELPERS ====================

class BaseDocenteTest(TestCase):
    """Clase base con configuración común para pruebas de docentes"""
    
    def setUp(self):
        self.docente_group, _ = Group.objects.get_or_create(name='Docente')
        
        # Configuración por defecto - se puede sobrescribir
        self.setup_users()
        self.setup_comite_seminario()
        
        self.client = Client()
        if hasattr(self, 'login_username'):
            self.client.login(username=self.login_username, password='testpass123')
    
    def setup_users(self):
        """Crear usuarios básicos - sobrescribir en subclases"""
        self.login_username = 'docente1'
        
        # Usuario docente principal
        self.user = User.objects.create_user(
            username=self.login_username,
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
        
        # Otros docentes
        self.user_otro1 = User.objects.create_user(
            username='otro1', password='testpass123', email='otro1@test.com'
        )
        self.docente_otro1 = Docente.objects.create(
            user=self.user_otro1, nombre="Maria", apellido_paterno="Martinez",
            apellido_materno="Rodriguez", correo="otro1@test.com"
        )
        
        self.user_otro2 = User.objects.create_user(
            username='otro2', password='testpass123', email='otro2@test.com'
        )
        self.docente_otro2 = Docente.objects.create(
            user=self.user_otro2, nombre="Jose", apellido_paterno="Sanchez",
            apellido_materno="Perez", correo="otro2@test.com"
        )
        
        # Alumno
        self.user_alumno = User.objects.create_user(
            username='alumno1', password='testpass123', email='alumno@test.com'
        )
        self.alumno = Alumno.objects.create(
            user=self.user_alumno, nombre='Pedro', apellido_paterno='Gomez',
            apellido_materno='Lopez', matricula='20230001', semestre='7', correo='pedro@test.com'
        )
    
    def setup_comite_seminario(self):
        """Crear comité y seminario"""
        self.comite = Comite.objects.create(
            tutor=self.docente,
            miembro1=self.docente_otro1,
            miembro2=self.docente_otro2
        )
        
        self.seminario = Seminario.objects.create(
            numero=7, periodo=1, fecha=date(2024, 12, 15), hora='10:00',
            alumno=self.alumno, comite=self.comite
        )
        
        self.formulario = FormularioComite.objects.create(seminario=self.seminario)


class DocenteSeminariosViewTest(BaseDocenteTest):
    """Pruebas para la vista docente_seminarios"""
    
    login_username = 'docente1'
    
    def test_vista_acceso_con_login(self):
        response = self.client.get(reverse('lumat_app:docente_seminarios'))
        self.assertEqual(response.status_code, 200)
    
    def test_redireccion_sin_login(self):
        self.client.logout()
        response = self.client.get(reverse('lumat_app:docente_seminarios'))
        self.assertEqual(response.status_code, 302)
    
    def test_template_correcto(self):
        response = self.client.get(reverse('lumat_app:docente_seminarios'))
        self.assertTemplateUsed(response, 'docente_seminario.html')
    
    def test_contexto_docente(self):
        response = self.client.get(reverse('lumat_app:docente_seminarios'))
        self.assertEqual(response.context['docente'], self.docente)
    
    def test_contexto_seminarios(self):
        response = self.client.get(reverse('lumat_app:docente_seminarios'))
        self.assertIn('seminarios', response.context)
    
    def test_acceso_denegado_usuario_no_docente(self):
        self.client.logout()
        self.client.login(username='normal', password='pass')
        response = self.client.get(reverse('lumat_app:docente_seminarios'))
        self.assertEqual(response.status_code, 302)


class DocenteFirmarSeminarioViewTest(BaseDocenteTest):
    """Pruebas para la vista docente_firmar_seminario"""
    
    login_username = 'docente1'
    
    def setUp(self):
        super().setUp()
        self.url = reverse('lumat_app:docente_firmar_seminario', args=[self.seminario.id])
    
    def test_redireccion_si_no_post(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
    
    def test_firmar_con_calificacion_valida(self):
        response = self.client.post(self.url, {
            'calificacion': '9.0', 'confirmar_firma': True
        })
        self.assertEqual(response.status_code, 302)
        
        self.formulario.refresh_from_db()
        self.assertTrue(self.formulario.firma_tutor)
        self.assertEqual(self.formulario.calificacion_tutor, Decimal('9.0'))
    
    def test_no_puede_firmar_dos_veces(self):
        self.formulario.firma_tutor = True
        self.formulario.calificacion_tutor = Decimal('8.0')
        self.formulario.save()
        
        response = self.client.post(self.url, {
            'calificacion': '9.0', 'confirmar_firma': True
        }, follow=True)
        
        messages = list(response.context['messages'])
        self.assertTrue(any('Ya habías firmado' in str(m) for m in messages))
        
        self.formulario.refresh_from_db()
        self.assertEqual(self.formulario.calificacion_tutor, Decimal('8.0'))
    
    def test_calificacion_invalida(self):
        response = self.client.post(self.url, {
            'calificacion': '15', 'confirmar_firma': True
        }, follow=True)
        
        messages = list(response.context['messages'])
        self.assertTrue(any('Datos inválidos' in str(m) for m in messages))
        
        self.formulario.refresh_from_db()
        self.assertFalse(self.formulario.firma_tutor)


class DocenteSeminarioDetallePostTest(BaseDocenteTest):
    """Pruebas para el POST en docente_seminario_detalle"""
    
    login_username = 'tutor_post'
    
    def setup_users(self):
        """Sobrescribir para crear usuario tutor específico"""
        self.login_username = 'tutor_post'
        
        self.user_tutor = User.objects.create_user(
            username='tutor_post', password='testpass123', email='tutor@test.com'
        )
        self.user_tutor.groups.add(self.docente_group)
        
        self.tutor = Docente.objects.create(
            user=self.user_tutor, nombre="Carlos", apellido_paterno="Lopez",
            apellido_materno="Garcia", correo="tutor@test.com"
        )
        
        # Otros docentes
        self.user_miembro1 = User.objects.create_user(
            username='miembro1_post', password='testpass123', email='miembro1@test.com'
        )
        self.miembro1 = Docente.objects.create(
            user=self.user_miembro1, nombre="Maria", apellido_paterno="Martinez",
            apellido_materno="Rodriguez", correo="miembro1@test.com"
        )
        
        self.user_miembro2 = User.objects.create_user(
            username='miembro2_post', password='testpass123', email='miembro2@test.com'
        )
        self.miembro2 = Docente.objects.create(
            user=self.user_miembro2, nombre="Jose", apellido_paterno="Sanchez",
            apellido_materno="Perez", correo="miembro2@test.com"
        )
        
        # Alumno
        self.user_alumno = User.objects.create_user(
            username='alumno_post', password='testpass123', email='alumno@test.com'
        )
        self.alumno = Alumno.objects.create(
            user=self.user_alumno, nombre='Pedro', apellido_paterno='Gomez',
            apellido_materno='Lopez', matricula='20230001', semestre='7', correo='pedro@test.com'
        )
    
    def setup_comite_seminario(self):
        self.comite = Comite.objects.create(
            tutor=self.tutor, miembro1=self.miembro1, miembro2=self.miembro2
        )
        self.seminario = Seminario.objects.create(
            numero=7, periodo=1, fecha=date(2024, 12, 15), hora='10:00',
            alumno=self.alumno, comite=self.comite
        )
        self.formulario = FormularioComite.objects.create(seminario=self.seminario)
        self.url = reverse('lumat_app:docente_seminario_detalle', args=[self.seminario.id])
    
    def _guardar_informe(self, data):
        """Helper para guardar informe y verificar redirección"""
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.url)
        return response
    
    def test_post_guardar_informe_como_tutor(self):
        data = {
            'el_comite_encuentra': 'El alumno demostró dominio completo del tema',
            'observaciones': 'Excelente defensa y presentación',
            'dictamen': 'Aprobado por unanimidad',
            'propuestas': 'Publicar artículo en revista indexada'
        }
        self._guardar_informe(data)
        
        self.formulario.refresh_from_db()
        self.assertEqual(self.formulario.el_comite_encuentra, data['el_comite_encuentra'])
        self.assertEqual(self.formulario.observaciones, data['observaciones'])
        self.assertEqual(self.formulario.dictamen, data['dictamen'])
        self.assertEqual(self.formulario.propuestas, data['propuestas'])
    
    def test_post_guardar_informe_con_datos_vacios(self):
        data = {'el_comite_encuentra': '', 'observaciones': '', 'dictamen': '', 'propuestas': ''}
        self._guardar_informe(data)
        
        self.formulario.refresh_from_db()
        self.assertEqual(self.formulario.el_comite_encuentra, '')
        self.assertEqual(self.formulario.observaciones, '')
        self.assertEqual(self.formulario.dictamen, '')
        self.assertEqual(self.formulario.propuestas, '')
    
    def test_post_guardar_informe_mensaje_success(self):
        data = {
            'el_comite_encuentra': 'Contenido de prueba',
            'observaciones': 'Observaciones de prueba',
            'dictamen': 'Dictamen de prueba',
            'propuestas': 'Propuestas de prueba'
        }
        response = self.client.post(self.url, data, follow=True)
        
        messages = list(response.context['messages'])
        self.assertTrue(any('Informe guardado correctamente' in str(m) for m in messages))
    
    def test_post_con_formulario_invalido(self):
        """Probar POST con textos muy largos (TextField debería aceptarlos)"""
        data = {
            'el_comite_encuentra': 'A' * 10000,
            'observaciones': 'B' * 10000,
            'dictamen': 'C' * 10000,
            'propuestas': 'D' * 10000
        }
        self._guardar_informe(data)
        
        self.formulario.refresh_from_db()
        self.assertEqual(len(self.formulario.el_comite_encuentra), 10000)


class DocenteSeminarioDetalleContextoTest(BaseDocenteTest):
    """Pruebas para el contexto de docente_seminario_detalle"""
    
    login_username = 'tutor_contexto'
    
    def setup_users(self):
        self.login_username = 'tutor_contexto'
        
        self.user_tutor = User.objects.create_user(
            username='tutor_contexto', password='testpass123', email='tutor@test.com'
        )
        self.user_tutor.groups.add(self.docente_group)
        
        self.tutor = Docente.objects.create(
            user=self.user_tutor, nombre="Carlos", apellido_paterno="Lopez",
            apellido_materno="Garcia", correo="tutor@test.com"
        )
        
        self.user_miembro1 = User.objects.create_user(
            username='miembro1_contexto', password='testpass123', email='miembro1@test.com'
        )
        self.user_miembro1.groups.add(self.docente_group)
        self.miembro1 = Docente.objects.create(
            user=self.user_miembro1, nombre="Maria", apellido_paterno="Martinez",
            apellido_materno="Rodriguez", correo="miembro1@test.com"
        )
        
        self.user_miembro2 = User.objects.create_user(
            username='miembro2_contexto', password='testpass123', email='miembro2@test.com'
        )
        self.user_miembro2.groups.add(self.docente_group)
        self.miembro2 = Docente.objects.create(
            user=self.user_miembro2, nombre="Jose", apellido_paterno="Sanchez",
            apellido_materno="Perez", correo="miembro2@test.com"
        )
        
        self.user_alumno = User.objects.create_user(
            username='alumno_contexto', password='testpass123', email='alumno@test.com'
        )
        self.alumno = Alumno.objects.create(
            user=self.user_alumno, nombre='Pedro', apellido_paterno='Gomez',
            apellido_materno='Lopez', matricula='20230001', semestre='7', correo='pedro@test.com'
        )
    
    def setup_comite_seminario(self):
        self.comite = Comite.objects.create(
            tutor=self.tutor, miembro1=self.miembro1, miembro2=self.miembro2
        )
        self.seminario = Seminario.objects.create(
            numero=7, periodo=1, fecha=date(2024, 12, 15), hora='10:00',
            alumno=self.alumno, comite=self.comite
        )
        self.formulario = FormularioComite.objects.create(seminario=self.seminario)
        self.url = reverse('lumat_app:docente_seminario_detalle', args=[self.seminario.id])
    
    def test_contexto_contiene_form(self):
        response = self.client.get(self.url)
        self.assertIn('form', response.context)
        self.assertIsNotNone(response.context['form'])
    
    def test_contexto_form_none_si_no_es_tutor(self):
        self.client.login(username='miembro1_contexto', password='testpass123')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)
        self.assertIsNone(response.context['form'])
    
    def test_contexto_contiene_firma_form(self):
        response = self.client.get(self.url)
        self.assertIn('firma_form', response.context)
    
    def test_contexto_ya_firme(self):
        response = self.client.get(self.url)
        self.assertIn('ya_firme', response.context)
        self.assertFalse(response.context['ya_firme'])
    
    def test_contexto_ya_firme_true_cuando_firmo(self):
        self.formulario.firma_tutor = True
        self.formulario.save()
        
        response = self.client.get(self.url)
        self.assertTrue(response.context['ya_firme'])
        self.assertIsNone(response.context['firma_form'])


class DescargarEvidenciasZipTest(BaseDocenteTest):
    """Pruebas para descargar_evidencias_zip"""
    
    login_username = 'docente_zip'
    
    def setup_users(self):
        self.login_username = 'docente_zip'
        
        self.user_tutor = User.objects.create_user(
            username='docente_zip', password='testpass123', email='docente@test.com'
        )
        self.user_tutor.groups.add(self.docente_group)
        
        self.tutor = Docente.objects.create(
            user=self.user_tutor, nombre="Carlos", apellido_paterno="Lopez",
            apellido_materno="Garcia", correo="docente@test.com"
        )
        
        self.user_miembro1 = User.objects.create_user(
            username='miembro1_zip', password='testpass123', email='miembro1@test.com'
        )
        self.user_miembro1.groups.add(self.docente_group)
        self.miembro1 = Docente.objects.create(
            user=self.user_miembro1, nombre="Maria", apellido_paterno="Martinez",
            apellido_materno="Rodriguez", correo="miembro1@test.com"
        )
        
        self.user_miembro2 = User.objects.create_user(
            username='miembro2_zip', password='testpass123', email='miembro2@test.com'
        )
        self.user_miembro2.groups.add(self.docente_group)
        self.miembro2 = Docente.objects.create(
            user=self.user_miembro2, nombre="Jose", apellido_paterno="Sanchez",
            apellido_materno="Perez", correo="miembro2@test.com"
        )
        
        self.user_alumno = User.objects.create_user(
            username='alumno_zip', password='testpass123', email='alumno@test.com'
        )
        self.alumno = Alumno.objects.create(
            user=self.user_alumno, nombre='Pedro', apellido_paterno='Gomez',
            apellido_materno='Lopez', matricula='20230001', semestre='7', correo='pedro@test.com'
        )
    
    def setup_comite_seminario(self):
        self.comite = Comite.objects.create(
            tutor=self.tutor, miembro1=self.miembro1, miembro2=self.miembro2
        )
        self.seminario = Seminario.objects.create(
            numero=7, periodo=1, fecha=date(2024, 12, 15), hora='10:00',
            alumno=self.alumno, comite=self.comite
        )
        self.url = reverse('lumat_app:docente_descargar_evidencias_zip', args=[self.seminario.id])
    
    def _crear_evidencia(self, nombre, contenido, filename=None):
        """Helper para crear evidencia de prueba"""
        nombre_archivo = filename or f"{nombre}.pdf"
        archivo = SimpleUploadedFile(
            nombre_archivo,
            contenido.encode() if isinstance(contenido, str) else contenido,
            content_type="application/pdf"
        )
        return Evidencia.objects.create(
            seminario=self.seminario,
            archivo=archivo,
            nombre=nombre
        )
    
    def _assert_zip_response(self, response):
        """Helper para validar respuesta ZIP"""
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/zip')
        self.assertTrue(response.content.startswith(b'PK'))
    
    def test_descargar_zip_con_evidencias(self):
        self._crear_evidencia("Documento de prueba", "Contenido del PDF de prueba")
        response = self.client.get(self.url)
        
        self._assert_zip_response(response)
        self.assertIn('attachment; filename=', response['Content-Disposition'])
        
        nombre_esperado = slugify(f"{self.alumno.nombre} {self.alumno.apellido_paterno}")
        self.assertIn(nombre_esperado, response['Content-Disposition'])
    
    def test_descargar_zip_con_multiples_evidencias(self):
        self._crear_evidencia("Documento 1", "Contenido del primer documento")
        self._crear_evidencia("Documento 2", "Contenido del segundo documento")
        
        response = self.client.get(self.url)
        self._assert_zip_response(response)
    
    @patch('lumat_app.views_docente.os.path.exists')
    def test_descargar_zip_con_archivo_sin_nombre(self, mock_exists):
        mock_exists.return_value = True
        
        archivo = SimpleUploadedFile("archivo_sin_nombre.pdf", b"Contenido", content_type="application/pdf")
        Evidencia.objects.create(seminario=self.seminario, archivo=archivo, nombre=None)
        
        response = self.client.get(self.url)
        self._assert_zip_response(response)
    
    @patch('lumat_app.views_docente.os.path.exists')
    def test_descargar_zip_con_archivo_inexistente(self, mock_exists):
        mock_exists.return_value = False
        
        archivo = SimpleUploadedFile("fake.pdf", b"Contenido fake", content_type="application/pdf")
        Evidencia.objects.create(seminario=self.seminario, archivo=archivo, nombre="Archivo fake")
        
        response = self.client.get(self.url)
        self._assert_zip_response(response)


class DescargarEvidenciasZipEstructuraNombreTest(BaseDocenteTest):
    """Pruebas para la estructura del nombre del ZIP"""
    
    login_username = 'docente_nombre'
    
    def setup_users(self):
        self.login_username = 'docente_nombre'
        
        self.user_tutor = User.objects.create_user(
            username='docente_nombre', password='testpass123', email='docente@test.com'
        )
        self.user_tutor.groups.add(self.docente_group)
        
        self.tutor = Docente.objects.create(
            user=self.user_tutor, nombre="Carlos", apellido_paterno="Lopez",
            apellido_materno="Garcia", correo="docente@test.com"
        )
        
        self.user_miembro1 = User.objects.create_user(
            username='miembro1_nombre', password='testpass123', email='miembro1@test.com'
        )
        self.user_miembro1.groups.add(self.docente_group)
        self.miembro1 = Docente.objects.create(
            user=self.user_miembro1, nombre="Maria", apellido_paterno="Martinez",
            apellido_materno="Rodriguez", correo="miembro1@test.com"
        )
        
        self.user_miembro2 = User.objects.create_user(
            username='miembro2_nombre', password='testpass123', email='miembro2@test.com'
        )
        self.user_miembro2.groups.add(self.docente_group)
        self.miembro2 = Docente.objects.create(
            user=self.user_miembro2, nombre="Jose", apellido_paterno="Sanchez",
            apellido_materno="Perez", correo="miembro2@test.com"
        )
        
        # Alumno con caracteres especiales
        self.user_alumno = User.objects.create_user(
            username='alumno_nombre', password='testpass123', email='alumno@test.com'
        )
        self.alumno = Alumno.objects.create(
            user=self.user_alumno, nombre='Juan Carlos', apellido_paterno='González',
            apellido_materno='Rodríguez', matricula='20230002', semestre='5', correo='juancarlos@test.com'
        )
    
    def setup_comite_seminario(self):
        self.comite = Comite.objects.create(
            tutor=self.tutor, miembro1=self.miembro1, miembro2=self.miembro2
        )
        self.seminario = Seminario.objects.create(
            numero=5, periodo=2, fecha=date(2024, 12, 15), hora='10:00',
            alumno=self.alumno, comite=self.comite
        )
        self.url = reverse('lumat_app:docente_descargar_evidencias_zip', args=[self.seminario.id])
    
    @patch('lumat_app.views_docente.os.path.exists')
    def test_nombre_zip_con_caracteres_especiales(self, mock_exists):
        mock_exists.return_value = True
        
        archivo = SimpleUploadedFile("doc.pdf", b"Contenido", content_type="application/pdf")
        Evidencia.objects.create(seminario=self.seminario, archivo=archivo, nombre="Documento")
        
        response = self.client.get(self.url)
        
        nombre_esperado = slugify(f"{self.alumno.nombre} {self.alumno.apellido_paterno}")
        self.assertIn(nombre_esperado, response['Content-Disposition'])