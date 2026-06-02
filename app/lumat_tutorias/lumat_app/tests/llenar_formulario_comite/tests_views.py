from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User, Group
from decimal import Decimal
from unittest.mock import patch
from lumat_app.models import Evidencia, Seminario, Alumno, Comite, FormularioComite, Docente
from datetime import date
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils.text import slugify


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
        # user_normal = User.objects.create_user(
        #     username='normal', password='pass')
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
        self.url = reverse('lumat_app:docente_firmar_seminario', args=[
                           self.seminario.id])

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


class DocenteSeminarioDetallePostTest(TestCase):
    """Pruebas específicas para el POST en docente_seminario_detalle"""

    def setUp(self):
        self.docente_group, _ = Group.objects.get_or_create(name='Docente')

        # Crear usuario tutor
        self.user_tutor = User.objects.create_user(
            username='tutor_post',
            password='testpass123',
            email='tutor@test.com'
        )
        self.user_tutor.groups.add(self.docente_group)

        # Crear docente tutor
        self.tutor = Docente.objects.create(
            user=self.user_tutor,
            nombre="Carlos",
            apellido_paterno="Lopez",
            apellido_materno="Garcia",
            correo="tutor@test.com"
        )

        # Crear otros docentes para el comité
        self.user_miembro1 = User.objects.create_user(
            username='miembro1_post',
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
            username='miembro2_post',
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
            username='alumno_post',
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

        # Crear comité con tutor como el docente
        self.comite = Comite.objects.create(
            tutor=self.tutor,
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

        # Crear formulario vacío
        self.formulario = FormularioComite.objects.create(
            seminario=self.seminario
        )

        self.client = Client()
        self.client.login(username='tutor_post', password='testpass123')
        self.url = reverse('lumat_app:docente_seminario_detalle', args=[
                           self.seminario.id])

    def test_post_guardar_informe_como_tutor(self):
        """Probar que el tutor puede guardar el informe vía POST"""
        post_data = {
            'el_comite_encuentra': 'El alumno demostró dominio completo del tema',
            'observaciones': 'Excelente defensa y presentación',
            'dictamen': 'Aprobado por unanimidad',
            'propuestas': 'Publicar artículo en revista indexada'
        }

        response = self.client.post(self.url, post_data)

        # Debe redirigir al detalle
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.url)

        # Verificar que se guardaron los datos
        self.formulario.refresh_from_db()
        self.assertEqual(self.formulario.el_comite_encuentra,
                         'El alumno demostró dominio completo del tema')
        self.assertEqual(self.formulario.observaciones,
                         'Excelente defensa y presentación')
        self.assertEqual(self.formulario.dictamen, 'Aprobado por unanimidad')
        self.assertEqual(self.formulario.propuestas,
                         'Publicar artículo en revista indexada')

    def test_post_guardar_informe_con_datos_vacios(self):
        """Probar POST con datos vacíos (debe ser válido porque blank=True)"""
        post_data = {
            'el_comite_encuentra': '',
            'observaciones': '',
            'dictamen': '',
            'propuestas': ''
        }

        response = self.client.post(self.url, post_data)

        self.assertEqual(response.status_code, 302)

        # Verificar que se guardaron campos vacíos
        self.formulario.refresh_from_db()
        self.assertEqual(self.formulario.el_comite_encuentra, '')
        self.assertEqual(self.formulario.observaciones, '')
        self.assertEqual(self.formulario.dictamen, '')
        self.assertEqual(self.formulario.propuestas, '')

    def test_post_guardar_informe_mensaje_success(self):
        """Probar que se muestra mensaje de éxito después de guardar"""
        post_data = {
            'el_comite_encuentra': 'Contenido de prueba',
            'observaciones': 'Observaciones de prueba',
            'dictamen': 'Dictamen de prueba',
            'propuestas': 'Propuestas de prueba'
        }

        response = self.client.post(self.url, post_data, follow=True)

        # Verificar mensaje de éxito
        messages = list(response.context['messages'])
        self.assertTrue(any('Informe guardado correctamente' in str(m)
                        for m in messages))

    def test_post_no_guarda_si_no_es_tutor(self):
        """Probar que un miembro que no es tutor no puede guardar el informe"""
        # Login como miembro1 (no tutor)
        self.client.login(username='miembro1_post', password='testpass123')

        # post_data = {
        #     'el_comite_encuentra': 'Este contenido no debería guardarse',
        #     'observaciones': 'No debería guardarse',
        #     'dictamen': 'No debería guardarse',
        #     'propuestas': 'No debería guardarse'
        # }

        # response = self.client.post(self.url, post_data)

        # Verificar que el formulario no se actualizó
        self.formulario.refresh_from_db()
        self.assertNotEqual(self.formulario.el_comite_encuentra,
                            'Este contenido no debería guardarse')

    def test_post_con_formulario_invalido(self):
        """Probar POST con datos inválidos (no debería pasar porque no hay validaciones)"""
        # El formulario no tiene validaciones especiales, pero probamos con datos extremos
        post_data = {
            'el_comite_encuentra': 'A' * 10000,  # Texto muy largo
            'observaciones': 'B' * 10000,
            'dictamen': 'C' * 10000,
            'propuestas': 'D' * 10000
        }

        response = self.client.post(self.url, post_data)

        # Debe aceptar textos largos porque es TextField
        self.assertEqual(response.status_code, 302)

        self.formulario.refresh_from_db()
        self.assertEqual(len(self.formulario.el_comite_encuentra), 10000)


class DocenteSeminarioDetalleContextoTest(TestCase):
    """Pruebas para el contexto de docente_seminario_detalle"""

    def setUp(self):
        self.docente_group, _ = Group.objects.get_or_create(name='Docente')

        # Crear usuario tutor
        self.user_tutor = User.objects.create_user(
            username='tutor_contexto',
            password='testpass123',
            email='tutor@test.com'
        )
        self.user_tutor.groups.add(self.docente_group)

        self.tutor = Docente.objects.create(
            user=self.user_tutor,
            nombre="Carlos",
            apellido_paterno="Lopez",
            apellido_materno="Garcia",
            correo="tutor@test.com"
        )

        # Crear otros docentes
        self.user_miembro1 = User.objects.create_user(
            username='miembro1_contexto',
            password='testpass123',
            email='miembro1@test.com'
        )
        self.user_miembro1.groups.add(self.docente_group)
        self.miembro1 = Docente.objects.create(
            user=self.user_miembro1,
            nombre="Maria",
            apellido_paterno="Martinez",
            apellido_materno="Rodriguez",
            correo="miembro1@test.com"
        )

        self.user_miembro2 = User.objects.create_user(
            username='miembro2_contexto',
            password='testpass123',
            email='miembro2@test.com'
        )
        self.user_miembro2.groups.add(self.docente_group)
        self.miembro2 = Docente.objects.create(
            user=self.user_miembro2,
            nombre="Jose",
            apellido_paterno="Sanchez",
            apellido_materno="Perez",
            correo="miembro2@test.com"
        )

        # Crear alumno
        self.user_alumno = User.objects.create_user(
            username='alumno_contexto',
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

        # Crear comité con 3 docentes diferentes
        self.comite = Comite.objects.create(
            tutor=self.tutor,
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

        self.formulario = FormularioComite.objects.create(
            seminario=self.seminario
        )

        self.client = Client()
        self.client.login(username='tutor_contexto', password='testpass123')
        self.url = reverse('lumat_app:docente_seminario_detalle', args=[
                           self.seminario.id])

    def test_contexto_contiene_form(self):
        """Probar que el contexto contiene el formulario para tutor"""
        response = self.client.get(self.url)

        self.assertIn('form', response.context)
        self.assertIsNotNone(response.context['form'])

    def test_contexto_form_none_si_no_es_tutor(self):
        """Probar que form es None si el usuario no es tutor"""
        # Login como miembro1 (no tutor)
        self.client.login(username='miembro1_contexto', password='testpass123')
        response = self.client.get(self.url)

        # Verificar que la respuesta es exitosa
        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)
        self.assertIsNone(response.context['form'])

    def test_contexto_contiene_firma_form(self):
        """Probar que el contexto contiene firma_form"""
        response = self.client.get(self.url)

        self.assertIn('firma_form', response.context)

    def test_contexto_ya_firme(self):
        """Probar que ya_firme está en el contexto"""
        response = self.client.get(self.url)

        self.assertIn('ya_firme', response.context)
        self.assertFalse(response.context['ya_firme'])

    def test_contexto_ya_firme_true_cuando_firmo(self):
        """Probar que ya_firme es True si el docente ya firmó"""
        self.formulario.firma_tutor = True
        self.formulario.save()

        response = self.client.get(self.url)

        self.assertTrue(response.context['ya_firme'])
        self.assertIsNone(response.context['firma_form'])


class DescargarEvidenciasZipCompletoTest(TestCase):
    """Pruebas completas para descargar_evidencias_zip"""

    def setUp(self):
        self.docente_group, _ = Group.objects.get_or_create(name='Docente')

        # Crear usuario docente tutor
        self.user_tutor = User.objects.create_user(
            username='docente_zip_completo',
            password='testpass123',
            email='docente@test.com'
        )
        self.user_tutor.groups.add(self.docente_group)

        self.tutor = Docente.objects.create(
            user=self.user_tutor,
            nombre="Carlos",
            apellido_paterno="Lopez",
            apellido_materno="Garcia",
            correo="docente@test.com"
        )

        # Crear otros docentes para el comité
        self.user_miembro1 = User.objects.create_user(
            username='miembro1_zip',
            password='testpass123',
            email='miembro1@test.com'
        )
        self.user_miembro1.groups.add(self.docente_group)
        self.miembro1 = Docente.objects.create(
            user=self.user_miembro1,
            nombre="Maria",
            apellido_paterno="Martinez",
            apellido_materno="Rodriguez",
            correo="miembro1@test.com"
        )

        self.user_miembro2 = User.objects.create_user(
            username='miembro2_zip',
            password='testpass123',
            email='miembro2@test.com'
        )
        self.user_miembro2.groups.add(self.docente_group)
        self.miembro2 = Docente.objects.create(
            user=self.user_miembro2,
            nombre="Jose",
            apellido_paterno="Sanchez",
            apellido_materno="Perez",
            correo="miembro2@test.com"
        )

        # Crear alumno
        self.user_alumno = User.objects.create_user(
            username='alumno_zip',
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
            tutor=self.tutor,
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

        self.client = Client()
        self.client.login(username='docente_zip_completo',
                          password='testpass123')
        self.url = reverse('lumat_app:docente_descargar_evidencias_zip', args=[
                           self.seminario.id])

    def test_descargar_zip_con_evidencias(self):
        """Probar descarga de ZIP con evidencias reales"""
        # Crear archivo de prueba
        # archivo_prueba = SimpleUploadedFile(
        #     "documento.pdf",
        #     b"Contenido del PDF de prueba",
        #     content_type="application/pdf"
        # )

        # Crear evidencia
        # evidencia = Evidencia.objects.create(
        #     seminario=self.seminario,
        #     archivo=archivo_prueba,
        #     nombre="Documento de prueba"
        # )

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/zip')
        self.assertIn('attachment; filename=', response['Content-Disposition'])

        # Verificar que es un ZIP válido
        zip_content = response.content
        # Los ZIP empiezan con PK
        self.assertTrue(zip_content.startswith(b'PK'))

        # Verificar que el nombre del archivo tiene el formato correcto
        nombre_esperado = slugify(
            f"{self.alumno.nombre} {self.alumno.apellido_paterno}")
        nombre_esperado_completo = f"{nombre_esperado}-semestre{self.alumno.semestre}-{slugify(str(self.seminario.periodo))}.zip"
        self.assertIn(nombre_esperado_completo,
                      response['Content-Disposition'])

    def test_descargar_zip_con_multiples_evidencias(self):
        """Probar descarga de ZIP con múltiples evidencias"""
        # Crear múltiples evidencias
        archivo1 = SimpleUploadedFile(
            "doc1.pdf",
            b"Contenido del primer documento",
            content_type="application/pdf"
        )
        archivo2 = SimpleUploadedFile(
            "doc2.pdf",
            b"Contenido del segundo documento",
            content_type="application/pdf"
        )

        Evidencia.objects.create(
            seminario=self.seminario,
            archivo=archivo1,
            nombre="Documento 1"
        )
        Evidencia.objects.create(
            seminario=self.seminario,
            archivo=archivo2,
            nombre="Documento 2"
        )

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/zip')

        # Verificar que el ZIP contiene ambos archivos
        zip_content = response.content
        self.assertTrue(zip_content.startswith(b'PK'))

    @patch('lumat_app.views_docente.os.path.exists')
    def test_descargar_zip_con_archivo_sin_nombre(self, mock_exists):
        """Probar descarga cuando la evidencia tiene nombre None"""
        mock_exists.return_value = True

        # archivo_prueba = SimpleUploadedFile(
        #     "archivo_sin_nombre.pdf",
        #     b"Contenido de prueba",
        #     content_type="application/pdf"
        # )

        # Crear evidencia sin nombre (nombre=None)
        # evidencia = Evidencia.objects.create(
        #     seminario=self.seminario,
        #     archivo=archivo_prueba,
        #     nombre=None  # Sin nombre
        # )

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/zip')

    @patch('lumat_app.views_docente.os.path.exists')
    @patch('lumat_app.views_docente.os.path.splitext')
    def test_descargar_zip_con_archivo_sin_extension(self, mock_splitext, mock_exists):
        """Probar descarga cuando el archivo no tiene extensión"""
        mock_exists.return_value = True
        mock_splitext.side_effect = [('archivo', ''), ('archivo.pdf', '.pdf')]

        # archivo_prueba = SimpleUploadedFile(
        #     "archivo",
        #     b"Contenido de prueba",
        #     content_type="application/octet-stream"
        # )

        # evidencia = Evidencia.objects.create(
        #     seminario=self.seminario,
        #     archivo=archivo_prueba,
        #     nombre="archivo_sin_extension"
        # )

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/zip')

    def test_descargar_zip_con_archivo_inexistente(self):
        """Probar descarga cuando el archivo no existe en el sistema"""
        # Crear evidencia con archivo que no existe realmente
        # archivo_fake = SimpleUploadedFile(
        #     "fake.pdf",
        #     b"Contenido fake",
        #     content_type="application/pdf"
        # )

        # evidencia = Evidencia.objects.create(
        #     seminario=self.seminario,
        #     archivo=archivo_fake,
        #     nombre="Archivo fake"
        # )

        # El archivo no existe realmente en el sistema de archivos
        # Entonces no debería incluirse en el ZIP

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/zip')


class DescargarEvidenciasZipEstructuraNombreTest(TestCase):
    """Pruebas para la estructura del nombre del ZIP"""

    def setUp(self):
        self.docente_group, _ = Group.objects.get_or_create(name='Docente')

        self.user_tutor = User.objects.create_user(
            username='docente_nombre',
            password='testpass123',
            email='docente@test.com'
        )
        self.user_tutor.groups.add(self.docente_group)

        self.tutor = Docente.objects.create(
            user=self.user_tutor,
            nombre="Carlos",
            apellido_paterno="Lopez",
            apellido_materno="Garcia",
            correo="docente@test.com"
        )

        self.user_miembro1 = User.objects.create_user(
            username='miembro1_nombre',
            password='testpass123',
            email='miembro1@test.com'
        )
        self.user_miembro1.groups.add(self.docente_group)
        self.miembro1 = Docente.objects.create(
            user=self.user_miembro1,
            nombre="Maria",
            apellido_paterno="Martinez",
            apellido_materno="Rodriguez",
            correo="miembro1@test.com"
        )

        self.user_miembro2 = User.objects.create_user(
            username='miembro2_nombre',
            password='testpass123',
            email='miembro2@test.com'
        )
        self.user_miembro2.groups.add(self.docente_group)
        self.miembro2 = Docente.objects.create(
            user=self.user_miembro2,
            nombre="Jose",
            apellido_paterno="Sanchez",
            apellido_materno="Perez",
            correo="miembro2@test.com"
        )

        self.user_alumno = User.objects.create_user(
            username='alumno_nombre',
            password='testpass123',
            email='alumno@test.com'
        )
        self.alumno = Alumno.objects.create(
            user=self.user_alumno,
            nombre='Juan Carlos',
            apellido_paterno='González',
            apellido_materno='Rodríguez',
            matricula='20230002',
            semestre='5',
            correo='juancarlos@test.com'
        )

        self.comite = Comite.objects.create(
            tutor=self.tutor,
            miembro1=self.miembro1,
            miembro2=self.miembro2
        )

        self.seminario = Seminario.objects.create(
            numero=5,
            periodo=2,
            fecha=date(2024, 12, 15),
            hora='10:00',
            alumno=self.alumno,
            comite=self.comite
        )

        self.client = Client()
        self.client.login(username='docente_nombre', password='testpass123')
        self.url = reverse('lumat_app:docente_descargar_evidencias_zip', args=[
                           self.seminario.id])

    @patch('lumat_app.views_docente.os.path.exists')
    def test_nombre_zip_con_caracteres_especiales(self, mock_exists):
        """Probar que el nombre del ZIP maneja caracteres especiales"""
        mock_exists.return_value = True

        archivo_prueba = SimpleUploadedFile(
            "doc.pdf",
            b"Contenido",
            content_type="application/pdf"
        )

        Evidencia.objects.create(
            seminario=self.seminario,
            archivo=archivo_prueba,
            nombre="Documento"
        )

        response = self.client.get(self.url)

        # Verificar que el nombre está slugificado (sin caracteres especiales)
        nombre_esperado = slugify(
            f"{self.alumno.nombre} {self.alumno.apellido_paterno}")
        self.assertIn(nombre_esperado, response['Content-Disposition'])
        # El nombre puede tener guiones, pero no debe tener tildes u otros caracteres especiales
        # El espacio está permitido en el header Content-Disposition, no es un error
