# from decimal import Decimal
# from datetime import date
# import io
# from unittest.mock import patch
# from PIL import Image as PILImage
# from django.test import TestCase, Client
# from django.contrib.auth.models import User, Group
# from django.core.files.uploadedfile import SimpleUploadedFile
# from django.urls import reverse
# from lumat_app.models import Seminario, Alumno, Comite, FormularioComite, Docente
# from lumat_app.utils_pdf_comite import generar_pdf_comite


# class GenerarPDFComiteTest(TestCase):
#     """Pruebas para la función generar_pdf_comite"""

#     def setUp(self):
#         # Usuario y alumno
#         self.user_alumno = User.objects.create_user(
#             username='alumno_pdf',
#             password='testpass123',
#             email='alumno@test.com'
#         )
#         self.alumno = Alumno.objects.create(
#             user=self.user_alumno,
#             nombre="Juan",
#             apellido_paterno="Perez",
#             apellido_materno="Lopez",
#             matricula="20220001",
#             semestre="5",
#             correo="juan@test.com"
#         )

#         # Crear docentes (3)
#         users_data = [
#             ('tutor_pdf', 'tutor@test.com', 'Carlos', 'Lopez', 'Garcia'),
#             ('miembro1_pdf', 'miembro1@test.com', 'Maria', 'Martinez', 'Rodriguez'),
#             ('miembro2_pdf', 'miembro2@test.com', 'Jose', 'Sanchez', 'Perez')
#         ]

#         users = {}
#         for username, email, nombre, apellido_p, apellido_m in users_data:
#             user = User.objects.create_user(
#                 username=username,
#                 password='testpass123',
#                 email=email
#             )
#             users[username] = user

#         self.tutor = Docente.objects.create(
#             user=users['tutor_pdf'],
#             nombre="Carlos",
#             apellido_paterno="Lopez",
#             apellido_materno="Garcia",
#             correo="tutor@test.com"
#         )
#         self.miembro1 = Docente.objects.create(
#             user=users['miembro1_pdf'],
#             nombre="Maria",
#             apellido_paterno="Martinez",
#             apellido_materno="Rodriguez",
#             correo="miembro1@test.com"
#         )
#         self.miembro2 = Docente.objects.create(
#             user=users['miembro2_pdf'],
#             nombre="Jose",
#             apellido_paterno="Sanchez",
#             apellido_materno="Perez",
#             correo="miembro2@test.com"
#         )

#         # Comité y seminario
#         self.comite = Comite.objects.create(
#             tutor=self.tutor,
#             miembro1=self.miembro1,
#             miembro2=self.miembro2
#         )
#         self.seminario = Seminario.objects.create(
#             numero=5,
#             periodo=1,
#             fecha=date(2024, 3, 15),
#             hora="10:00",
#             alumno=self.alumno,
#             comite=self.comite
#         )

#         # Formulario completo
#         self.formulario = FormularioComite.objects.create(
#             seminario=self.seminario,
#             el_comite_encuentra="El alumno demostró buen conocimiento del tema",
#             observaciones="Excelente presentación y defensa",
#             dictamen="Aprobado por unanimidad",
#             propuestas="Continuar con la investigación y publicar resultados",
#             calificacion_tutor=Decimal("9.0"),
#             calificacion_miembro1=Decimal("8.5"),
#             calificacion_miembro2=Decimal("9.0"),
#             firma_tutor=True,
#             firma_miembro1=True,
#             firma_miembro2=True
#         )

#     def _crear_seminario_adicional(self, numero, hora):
#         """Helper para crear seminarios adicionales"""
#         return Seminario.objects.create(
#             numero=numero,
#             periodo=1,
#             fecha=date(2024, 4, 15),
#             hora=hora,
#             alumno=self.alumno,
#             comite=self.comite
#         )

#     def _assert_pdf_valido(self, resultado):
#         """Helper para verificar que el resultado es un PDF válido"""
#         self.assertIsInstance(resultado, bytes)
#         self.assertTrue(len(resultado) > 0)
#         self.assertTrue(resultado.startswith(b'%PDF'))

#     def test_generar_pdf_retorna_bytes(self):
#         self._assert_pdf_valido(generar_pdf_comite(self.formulario))

#     def test_generar_pdf_con_datos_vacios(self):
#         otro_seminario = self._crear_seminario_adicional(6, "11:00")
#         formulario_vacio = FormularioComite.objects.create(seminario=otro_seminario)
#         self._assert_pdf_valido(generar_pdf_comite(formulario_vacio))

#     def test_generar_pdf_con_calificaciones_none(self):
#         self.formulario.calificacion_miembro1 = None
#         self.formulario.save()
#         self._assert_pdf_valido(generar_pdf_comite(self.formulario))

#     def test_generar_pdf_sin_firmas(self):
#         otro_seminario = self._crear_seminario_adicional(7, "12:00")
#         formulario_sin_firmas = FormularioComite.objects.create(
#             seminario=otro_seminario,
#             firma_tutor=False,
#             firma_miembro1=False,
#             firma_miembro2=False
#         )
#         self._assert_pdf_valido(generar_pdf_comite(formulario_sin_firmas))


# class BaseActaTest(TestCase):
#     """Clase base para pruebas de actas con configuración común"""

#     def setUp(self):
#         self.docente_group, _ = Group.objects.get_or_create(name='Docente')

#         # Crear usuario docente principal
#         self.user = User.objects.create_user(
#             username='docente_acta',
#             password='testpass123',
#             email='docente@test.com'
#         )
#         self.user.groups.add(self.docente_group)

#         self.docente = Docente.objects.create(
#             user=self.user,
#             nombre="Carlos",
#             apellido_paterno="Lopez",
#             apellido_materno="Garcia",
#             correo="docente@test.com"
#         )

#         # Crear otros docentes
#         self.user_miembro1 = User.objects.create_user(
#             username='miembro1_acta',
#             password='testpass123',
#             email='miembro1@test.com'
#         )
#         self.miembro1 = Docente.objects.create(
#             user=self.user_miembro1,
#             nombre="Maria",
#             apellido_paterno="Martinez",
#             apellido_materno="Rodriguez",
#             correo="miembro1@test.com"
#         )

#         self.user_miembro2 = User.objects.create_user(
#             username='miembro2_acta',
#             password='testpass123',
#             email='miembro2@test.com'
#         )
#         self.miembro2 = Docente.objects.create(
#             user=self.user_miembro2,
#             nombre="Jose",
#             apellido_paterno="Sanchez",
#             apellido_materno="Perez",
#             correo="miembro2@test.com"
#         )

#         # Crear alumno
#         self.user_alumno = User.objects.create_user(
#             username='alumno_acta',
#             password='testpass123',
#             email='alumno@test.com'
#         )
#         self.alumno = Alumno.objects.create(
#             user=self.user_alumno,
#             nombre='Pedro',
#             apellido_paterno='Gomez',
#             apellido_materno='Lopez',
#             matricula='20230001',
#             semestre='7',
#             correo='pedro@test.com'
#         )

#         # Crear comité y seminario
#         self.comite = Comite.objects.create(
#             tutor=self.docente,
#             miembro1=self.miembro1,
#             miembro2=self.miembro2
#         )
#         self.seminario = Seminario.objects.create(
#             numero=7,
#             periodo=1,
#             fecha=date(2024, 12, 15),
#             hora='10:00',
#             alumno=self.alumno,
#             comite=self.comite
#         )

#         self.formulario = FormularioComite.objects.create(
#             seminario=self.seminario,
#             el_comite_encuentra="El alumno demostró buen conocimiento",
#             observaciones="Excelente presentación",
#             dictamen="Aprobado",
#             propuestas="Continuar con investigación"
#         )

#         self.client = Client()
#         self.client.login(username='docente_acta', password='testpass123')
#         self.url = reverse('lumat_app:docente_descargar_acta', args=[self.seminario.id])

#     def _assert_response_pdf(self, response):
#         """Helper para verificar respuesta PDF"""
#         self.assertEqual(response.status_code, 200)
#         self.assertEqual(response['Content-Type'], 'application/pdf')
#         self.assertTrue(response.content.startswith(b'%PDF'))


# class DocenteDescargarActaViewTest(BaseActaTest):
#     """Pruebas para la vista docente_descargar_acta"""

#     def test_descargar_acta_exitosa(self):
#         response = self.client.get(self.url)
#         self._assert_response_pdf(response)
#         self.assertIn('attachment; filename="acta_seminario_', response['Content-Disposition'])

#     def test_descargar_acta_seminario_inexistente(self):
#         url_inexistente = reverse('lumat_app:docente_descargar_acta', args=[99999])
#         response = self.client.get(url_inexistente)
#         self.assertEqual(response.status_code, 404)

#     def test_descargar_acta_sin_formulario(self):
#         seminario_sin_form = Seminario.objects.create(
#             numero=8,
#             periodo=1,
#             fecha=date(2024, 12, 20),
#             hora='11:00',
#             alumno=self.alumno,
#             comite=self.comite
#         )
#         url_sin_form = reverse('lumat_app:docente_descargar_acta', args=[seminario_sin_form.id])
#         response = self.client.get(url_sin_form)
#         self.assertEqual(response.status_code, 404)

#     # def test_descargar_acta_sin_permiso(self):
#     #     otro_user = User.objects.create_user(username='otro_acta', password='pass')
#     #     otro_user.groups.add(self.docente_group)
#     #     self.client.login(username='otro_acta', password='pass')
#     #     response = self.client.get(self.url)
#     #     self.assertEqual(response.status_code, 404)

#     def test_descargar_acta_usuario_no_docente(self):
#         self.client.logout()
#         self.client.login(username='normal_acta', password='pass')
#         response = self.client.get(self.url)
#         self.assertEqual(response.status_code, 302)

#     def test_descargar_acta_sin_login(self):
#         self.client.logout()
#         response = self.client.get(self.url)
#         self.assertEqual(response.status_code, 302)


# class DocenteDescargarActaConFirmaImagenTest(BaseActaTest):
#     """Pruebas para descarga de acta con imágenes de firma"""

#     def setUp(self):
#         super().setUp()

#         # Crear imagen PNG válida
#         img = PILImage.new('RGB', (100, 50), color='white')
#         img_byte_arr = io.BytesIO()
#         img.save(img_byte_arr, format='PNG')
#         img_byte_arr.seek(0)

#         firma_file = SimpleUploadedFile(
#             "firma.png",
#             img_byte_arr.getvalue(),
#             content_type="image/png"
#         )

#         # Agregar firma al docente
#         self.docente.firma = firma_file
#         self.docente.save()

#         # Actualizar formulario con firmas
#         self.formulario.firma_tutor = True
#         self.formulario.firma_miembro1 = True
#         self.formulario.firma_miembro2 = True
#         self.formulario.save()

#     def test_descargar_acta_con_imagen_firma(self):
#         response = self.client.get(self.url)
#         self._assert_response_pdf(response)


# class PDFFirmaCellTest(TestCase):
#     """Pruebas para la función firma_cell dentro de generar_pdf_comite"""

#     def setUp(self):
#         # Usuario y alumno
#         self.user_alumno = User.objects.create_user(
#             username='alumno_firma_cell',
#             password='testpass123',
#             email='alumno@test.com'
#         )
#         self.alumno = Alumno.objects.create(
#             user=self.user_alumno,
#             nombre="Juan",
#             apellido_paterno="Perez",
#             apellido_materno="Lopez",
#             matricula="20220001",
#             semestre="5",
#             correo="juan@test.com"
#         )

#         # Crear docentes
#         users_data = [
#             ('tutor_firma_cell', 'tutor@test.com', 'Carlos', 'Lopez', 'Garcia'),
#             ('miembro1_firma_cell', 'miembro1@test.com', 'Maria', 'Martinez', 'Rodriguez'),
#             ('miembro2_firma_cell', 'miembro2@test.com', 'Jose', 'Sanchez', 'Perez')
#         ]

#         users = {}
#         for username, email, nombre, apellido_p, apellido_m in users_data:
#             user = User.objects.create_user(
#                 username=username,
#                 password='testpass123',
#                 email=email
#             )
#             users[username] = user

#         self.tutor = Docente.objects.create(
#             user=users['tutor_firma_cell'],
#             nombre="Carlos",
#             apellido_paterno="Lopez",
#             apellido_materno="Garcia",
#             correo="tutor@test.com"
#         )
#         self.miembro1 = Docente.objects.create(
#             user=users['miembro1_firma_cell'],
#             nombre="Maria",
#             apellido_paterno="Martinez",
#             apellido_materno="Rodriguez",
#             correo="miembro1@test.com"
#         )
#         self.miembro2 = Docente.objects.create(
#             user=users['miembro2_firma_cell'],
#             nombre="Jose",
#             apellido_paterno="Sanchez",
#             apellido_materno="Perez",
#             correo="miembro2@test.com"
#         )

#         self.comite = Comite.objects.create(
#             tutor=self.tutor,
#             miembro1=self.miembro1,
#             miembro2=self.miembro2
#         )
#         self.seminario = Seminario.objects.create(
#             numero=5,
#             periodo=1,
#             fecha=date(2024, 3, 15),
#             hora="10:00",
#             alumno=self.alumno,
#             comite=self.comite
#         )

#     def _crear_formulario_con_firmas(self, firma_tutor, firma_miembro1, firma_miembro2):
#         """Helper para crear formulario con configuración específica de firmas"""
#         return FormularioComite.objects.create(
#             seminario=self.seminario,
#             firma_tutor=firma_tutor,
#             firma_miembro1=firma_miembro1,
#             firma_miembro2=firma_miembro2
#         )

#     def _agregar_imagen_firma(self, docente):
#         """Helper para agregar imagen de firma a un docente"""
#         img = PILImage.new('RGB', (100, 50), color='white')
#         img_byte_arr = io.BytesIO()
#         img.save(img_byte_arr, format='PNG')
#         img_byte_arr.seek(0)

#         firma_file = SimpleUploadedFile(
#             "firma_test.png",
#             img_byte_arr.getvalue(),
#             content_type="image/png"
#         )
#         docente.firma = firma_file
#         docente.save()

#     def _assert_pdf_valido(self, formulario):
#         """Helper para verificar PDF válido"""
#         resultado = generar_pdf_comite(formulario)
#         self.assertIsInstance(resultado, bytes)
#         self.assertTrue(resultado.startswith(b'%PDF'))

#     def test_generar_pdf_con_firma_sin_imagen(self):
#         formulario = self._crear_formulario_con_firmas(True, True, True)
#         self._assert_pdf_valido(formulario)

#     def test_generar_pdf_con_firma_e_imagen_valida(self):
#         self._agregar_imagen_firma(self.tutor)
#         formulario = self._crear_formulario_con_firmas(True, True, True)
#         self._assert_pdf_valido(formulario)

#     @patch('lumat_app.utils_pdf_comite.os.path.exists')
#     def test_generar_pdf_con_firma_imagen_no_existente(self, mock_exists):
#         mock_exists.return_value = False
#         self._agregar_imagen_firma(self.tutor)
#         formulario = self._crear_formulario_con_firmas(True, False, False)
#         self._assert_pdf_valido(formulario)

#     @patch('lumat_app.utils_pdf_comite.Image')
#     def test_generar_pdf_con_error_al_cargar_imagen(self, mock_image):
#         mock_image.side_effect = Exception("Error al cargar imagen")
#         self._agregar_imagen_firma(self.tutor)
#         formulario = self._crear_formulario_con_firmas(True, False, False)
#         self._assert_pdf_valido(formulario)

#     def test_generar_pdf_sin_firmas_muestra_lineas(self):
#         formulario = self._crear_formulario_con_firmas(False, False, False)
#         self._assert_pdf_valido(formulario)

#     def test_generar_pdf_firmas_mixtas(self):
#         formulario = self._crear_formulario_con_firmas(True, False, True)
#         self._assert_pdf_valido(formulario)
