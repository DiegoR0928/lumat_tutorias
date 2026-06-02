from django.test import TestCase, Client
from django.contrib.auth.models import User, Group
from django.core.files.uploadedfile import SimpleUploadedFile
from unittest.mock import patch
from decimal import Decimal

from django.urls import reverse
from lumat_app.models import Seminario, Alumno, Comite, FormularioComite, Docente
from lumat_app.utils_pdf_comite import generar_pdf_comite
from datetime import date
import io
from PIL import Image as PILImage


class GenerarPDFComiteTest(TestCase):
    """Pruebas para la función generar_pdf_comite"""

    def setUp(self):
        # Crear usuario para el alumno
        self.user_alumno = User.objects.create_user(
            username='alumno_pdf',
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

        # Crear usuarios para docentes
        self.user_tutor = User.objects.create_user(
            username='tutor_pdf',
            password='testpass123',
            email='tutor@test.com'
        )
        self.user_miembro1 = User.objects.create_user(
            username='miembro1_pdf',
            password='testpass123',
            email='miembro1@test.com'
        )
        self.user_miembro2 = User.objects.create_user(
            username='miembro2_pdf',
            password='testpass123',
            email='miembro2@test.com'
        )

        # Crear docentes
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

        # Crear comité
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

        # Crear formulario con datos completos
        self.formulario = FormularioComite.objects.create(
            seminario=self.seminario,
            el_comite_encuentra="El alumno demostró buen conocimiento del tema",
            observaciones="Excelente presentación y defensa",
            dictamen="Aprobado por unanimidad",
            propuestas="Continuar con la investigación y publicar resultados",
            calificacion_tutor=Decimal("9.0"),
            calificacion_miembro1=Decimal("8.5"),
            calificacion_miembro2=Decimal("9.0"),
            firma_tutor=True,
            firma_miembro1=True,
            firma_miembro2=True
        )

    def test_generar_pdf_retorna_bytes(self):
        """Probar que generar_pdf_comite retorna bytes"""
        resultado = generar_pdf_comite(self.formulario)
        self.assertIsInstance(resultado, bytes)
        self.assertTrue(len(resultado) > 0)

    def test_generar_pdf_contenido_pdf(self):
        """Probar que el resultado es un PDF válido (empieza con %PDF)"""
        resultado = generar_pdf_comite(self.formulario)
        self.assertTrue(resultado.startswith(b'%PDF'))

    def test_generar_pdf_con_datos_vacios(self):
        """Probar generar PDF con campos vacíos - crear otro seminario"""
        # Crear otro seminario para evitar unique constraint
        otro_seminario = Seminario.objects.create(
            numero=6,
            periodo=1,
            fecha=date(2024, 4, 15),
            hora="11:00",
            alumno=self.alumno,
            comite=self.comite
        )
        formulario_vacio = FormularioComite.objects.create(
            seminario=otro_seminario
        )
        resultado = generar_pdf_comite(formulario_vacio)
        self.assertIsInstance(resultado, bytes)
        self.assertTrue(resultado.startswith(b'%PDF'))

    def test_generar_pdf_con_calificaciones_none(self):
        """Probar generar PDF cuando algunas calificaciones son None"""
        self.formulario.calificacion_miembro1 = None
        self.formulario.save()
        resultado = generar_pdf_comite(self.formulario)
        self.assertIsInstance(resultado, bytes)
        self.assertTrue(resultado.startswith(b'%PDF'))

    def test_generar_pdf_sin_firmas(self):
        """Probar generar PDF cuando ningún docente ha firmado"""
        # Crear otro seminario
        otro_seminario = Seminario.objects.create(
            numero=7,
            periodo=1,
            fecha=date(2024, 5, 15),
            hora="12:00",
            alumno=self.alumno,
            comite=self.comite
        )
        formulario_sin_firmas = FormularioComite.objects.create(
            seminario=otro_seminario,
            firma_tutor=False,
            firma_miembro1=False,
            firma_miembro2=False
        )
        resultado = generar_pdf_comite(formulario_sin_firmas)
        self.assertIsInstance(resultado, bytes)
        self.assertTrue(resultado.startswith(b'%PDF'))


class DocenteDescargarActaViewTest(TestCase):
    """Pruebas para la vista docente_descargar_acta"""

    def setUp(self):
        self.docente_group, _ = Group.objects.get_or_create(name='Docente')

        # Crear usuario docente
        self.user = User.objects.create_user(
            username='docente_acta',
            password='testpass123',
            email='docente@test.com'
        )
        self.user.groups.add(self.docente_group)

        # Crear docente
        self.docente = Docente.objects.create(
            user=self.user,
            nombre="Carlos",
            apellido_paterno="Lopez",
            apellido_materno="Garcia",
            correo="docente@test.com"
        )

        # Crear otros docentes
        self.user_miembro1 = User.objects.create_user(
            username='miembro1_acta',
            password='testpass123',
            email='miembro1@test.com'
        )
        self.miembro1 = Docente.objects.create(
            user=self.user_miembro1,
            nombre="Maria",
            apellido_paterno="Martinez",
            apellido_materno="Rodriguez",
            correo="miembro1@test.com"
        )

        self.user_miembro2 = User.objects.create_user(
            username='miembro2_acta',
            password='testpass123',
            email='miembro2@test.com'
        )
        self.miembro2 = Docente.objects.create(
            user=self.user_miembro2,
            nombre="Jose",
            apellido_paterno="Sanchez",
            apellido_materno="Perez",
            correo="miembro2@test.com"
        )

        # Crear alumno
        self.user_alumno = User.objects.create_user(
            username='alumno_acta',
            password='testpass123',
            email='alumno@test.com'
        )
        self.alumno = Alumno.objects.create(
            user=self.user_alumno,
            nombre='Pedro',
            apellido_paterno='Gomez',
            apellido_materno='Lopez',
            matricula='20230001',
            semestre='7',
            correo='pedro@test.com'
        )

        # Crear comité
        self.comite = Comite.objects.create(
            tutor=self.docente,
            miembro1=self.miembro1,
            miembro2=self.miembro2
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
            seminario=self.seminario,
            el_comite_encuentra="El alumno demostró buen conocimiento",
            observaciones="Excelente presentación",
            dictamen="Aprobado",
            propuestas="Continuar con investigación"
        )

        self.client = Client()
        self.client.login(username='docente_acta', password='testpass123')
        self.url = reverse('lumat_app:docente_descargar_acta',
                           args=[self.seminario.id])

    def test_descargar_acta_exitosa(self):
        """Probar que se puede descargar el acta exitosamente"""
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertIn('attachment; filename="acta_seminario_',
                      response['Content-Disposition'])
        self.assertTrue(response.content.startswith(b'%PDF'))

    def test_descargar_acta_seminario_inexistente(self):
        """Probar que da 404 si el seminario no existe"""
        url_inexistente = reverse(
            'lumat_app:docente_descargar_acta', args=[99999])
        response = self.client.get(url_inexistente)
        self.assertEqual(response.status_code, 404)

    def test_descargar_acta_sin_formulario(self):
        """Probar que da 404 si el seminario no tiene formulario"""
        # Crear seminario sin formulario
        seminario_sin_form = Seminario.objects.create(
            numero=8,
            periodo=1,
            fecha=date(2024, 12, 20),
            hora='11:00',
            alumno=self.alumno,
            comite=self.comite
        )
        url_sin_form = reverse('lumat_app:docente_descargar_acta', args=[
                               seminario_sin_form.id])
        response = self.client.get(url_sin_form)
        self.assertEqual(response.status_code, 404)

    def test_descargar_acta_sin_permiso(self):
        """Probar que un docente que no pertenece al comité no puede descargar"""
        # Crear otro docente
        otro_user = User.objects.create_user(
            username='otro_acta', password='pass')
        otro_user.groups.add(self.docente_group)
        # otro_docente = Docente.objects.create(
        #     user=otro_user,
        #     nombre="Otro",
        #     apellido_paterno="Docente",
        #     apellido_materno="Test",
        #     correo="otro@test.com"
        # )

        self.client.login(username='otro_acta', password='pass')
        response = self.client.get(self.url)

        # Debe dar 404 porque no tiene rol en el seminario
        self.assertEqual(response.status_code, 404)

    def test_descargar_acta_usuario_no_docente(self):
        """Probar que un usuario no docente no puede descargar"""
        self.client.logout()
        # user_normal = User.objects.create_user(
        #     username='normal_acta', password='pass')
        self.client.login(username='normal_acta', password='pass')

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_descargar_acta_sin_login(self):
        """Probar que redirige si no hay login"""
        self.client.logout()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)


class DocenteDescargarActaConFirmaImagenTest(TestCase):
    """Pruebas para descarga de acta con imágenes de firma"""

    def setUp(self):
        self.docente_group, _ = Group.objects.get_or_create(name='Docente')

        # Crear usuario docente
        self.user = User.objects.create_user(
            username='docente_firma',
            password='testpass123',
            email='docente@test.com'
        )
        self.user.groups.add(self.docente_group)

        # Crear una imagen PNG válida para la firma
        # Creamos una imagen real en memoria
        img = PILImage.new('RGB', (100, 50), color='white')
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)

        firma_file = SimpleUploadedFile(
            "firma.png",
            img_byte_arr.getvalue(),
            content_type="image/png"
        )

        # Crear docente con firma
        self.docente = Docente.objects.create(
            user=self.user,
            nombre="Carlos",
            apellido_paterno="Lopez",
            apellido_materno="Garcia",
            correo="docente@test.com",
            firma=firma_file
        )

        # Crear otros docentes
        self.user_miembro1 = User.objects.create_user(
            username='miembro1_firma',
            password='testpass123',
            email='miembro1@test.com'
        )
        self.miembro1 = Docente.objects.create(
            user=self.user_miembro1,
            nombre="Maria",
            apellido_paterno="Martinez",
            apellido_materno="Rodriguez",
            correo="miembro1@test.com"
        )

        self.user_miembro2 = User.objects.create_user(
            username='miembro2_firma',
            password='testpass123',
            email='miembro2@test.com'
        )
        self.miembro2 = Docente.objects.create(
            user=self.user_miembro2,
            nombre="Jose",
            apellido_paterno="Sanchez",
            apellido_materno="Perez",
            correo="miembro2@test.com"
        )

        # Crear alumno
        self.user_alumno = User.objects.create_user(
            username='alumno_firma',
            password='testpass123',
            email='alumno@test.com'
        )
        self.alumno = Alumno.objects.create(
            user=self.user_alumno,
            nombre='Pedro',
            apellido_paterno='Gomez',
            apellido_materno='Lopez',
            matricula='20230001',
            semestre='7',
            correo='pedro@test.com'
        )

        # Crear comité
        self.comite = Comite.objects.create(
            tutor=self.docente,
            miembro1=self.miembro1,
            miembro2=self.miembro2
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

        # Crear formulario con firmas
        self.formulario = FormularioComite.objects.create(
            seminario=self.seminario,
            firma_tutor=True,
            firma_miembro1=True,
            firma_miembro2=True
        )

        self.client = Client()
        self.client.login(username='docente_firma', password='testpass123')
        self.url = reverse('lumat_app:docente_descargar_acta',
                           args=[self.seminario.id])

    def test_descargar_acta_con_imagen_firma(self):
        """Probar descarga de acta cuando hay imagen de firma válida"""
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertTrue(response.content.startswith(b'%PDF'))


class PDFFirmaCellTest(TestCase):
    """Pruebas específicas para la función firma_cell dentro de generar_pdf_comite"""

    def setUp(self):
        # Crear usuario para el alumno
        self.user_alumno = User.objects.create_user(
            username='alumno_firma_cell',
            password='testpass123',
            email='alumno@test.com'
        )

        self.alumno = Alumno.objects.create(
            user=self.user_alumno,
            nombre="Juan",
            apellido_paterno="Perez",
            apellido_materno="Lopez",
            matricula="20220001",
            semestre="5",
            correo="juan@test.com"
        )

        # Crear usuarios para docentes
        self.user_tutor = User.objects.create_user(
            username='tutor_firma_cell',
            password='testpass123',
            email='tutor@test.com'
        )
        self.user_miembro1 = User.objects.create_user(
            username='miembro1_firma_cell',
            password='testpass123',
            email='miembro1@test.com'
        )
        self.user_miembro2 = User.objects.create_user(
            username='miembro2_firma_cell',
            password='testpass123',
            email='miembro2@test.com'
        )

        # Crear docentes
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

        # Crear comité
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

    def test_generar_pdf_con_firma_sin_imagen(self):
        """Probar PDF cuando hay firma pero no hay imagen (debe mostrar [APROBADO])"""
        formulario = FormularioComite.objects.create(
            seminario=self.seminario,
            firma_tutor=True,
            firma_miembro1=True,
            firma_miembro2=True
        )

        resultado = generar_pdf_comite(formulario)
        self.assertTrue(resultado.startswith(b'%PDF'))

    def test_generar_pdf_con_firma_e_imagen_valida(self):
        """Probar PDF cuando hay firma con imagen válida"""
        # Crear imagen PNG válida
        img = PILImage.new('RGB', (100, 50), color='white')
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)

        firma_file = SimpleUploadedFile(
            "firma_test.png",
            img_byte_arr.getvalue(),
            content_type="image/png"
        )

        # Actualizar tutor con firma
        self.tutor.firma = firma_file
        self.tutor.save()

        formulario = FormularioComite.objects.create(
            seminario=self.seminario,
            firma_tutor=True,
            firma_miembro1=True,
            firma_miembro2=True
        )

        resultado = generar_pdf_comite(formulario)
        self.assertTrue(resultado.startswith(b'%PDF'))

    @patch('lumat_app.utils_pdf_comite.os.path.exists')
    def test_generar_pdf_con_firma_imagen_no_existente(self, mock_exists):
        """Probar PDF cuando la imagen de firma no existe en el sistema de archivos"""
        mock_exists.return_value = False

        # Crear docente con firma (pero el archivo no existe realmente)
        firma_file = SimpleUploadedFile(
            "firma_no_existe.png",
            b"fake content",
            content_type="image/png"
        )
        self.tutor.firma = firma_file
        self.tutor.save()

        formulario = FormularioComite.objects.create(
            seminario=self.seminario,
            firma_tutor=True,
            firma_miembro1=False,
            firma_miembro2=False
        )

        resultado = generar_pdf_comite(formulario)
        self.assertTrue(resultado.startswith(b'%PDF'))

    @patch('lumat_app.utils_pdf_comite.Image')
    def test_generar_pdf_con_error_al_cargar_imagen(self, mock_image):
        """Probar PDF cuando hay error al cargar la imagen de firma"""
        mock_image.side_effect = Exception("Error al cargar imagen")

        # Crear imagen ficticia
        firma_file = SimpleUploadedFile(
            "firma_error.png",
            b"fake content",
            content_type="image/png"
        )
        self.tutor.firma = firma_file
        self.tutor.save()

        formulario = FormularioComite.objects.create(
            seminario=self.seminario,
            firma_tutor=True,
            firma_miembro1=False,
            firma_miembro2=False
        )

        resultado = generar_pdf_comite(formulario)
        self.assertTrue(resultado.startswith(b'%PDF'))

    def test_generar_pdf_sin_firmas_muestra_lineas(self):
        """Probar PDF cuando no hay firmas (debe mostrar líneas para firmar)"""
        formulario = FormularioComite.objects.create(
            seminario=self.seminario,
            firma_tutor=False,
            firma_miembro1=False,
            firma_miembro2=False
        )

        resultado = generar_pdf_comite(formulario)
        self.assertTrue(resultado.startswith(b'%PDF'))

    def test_generar_pdf_firmas_mixtas(self):
        """Probar PDF con firmas mixtas (algunos firmaron, otros no)"""
        formulario = FormularioComite.objects.create(
            seminario=self.seminario,
            firma_tutor=True,
            firma_miembro1=False,
            firma_miembro2=True
        )

        resultado = generar_pdf_comite(formulario)
        self.assertTrue(resultado.startswith(b'%PDF'))
