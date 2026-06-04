import datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch

from django.test import TestCase
from django.core.files.base import ContentFile

from django.contrib.auth.models import User
from lumat_app.models import Alumno, Docente, Comite, Seminario, FormularioComite

from django.core.files.uploadedfile import SimpleUploadedFile


class FormularioComiteMetodosTestCase(TestCase):

    def setUp(self):
        # 1. Crear el usuario obligatorio requerido por el modelo Alumno
        self.user_alumno = User.objects.create_user(
            username='alumno_modelo_test',
            password='password123'
        )

        self.alumno = Alumno.objects.create(
            user=self.user_alumno,
            nombre="Luis",
            apellido_paterno="Vega",
            apellido_materno="Mora",
            matricula="20261109",
            semestre="8",
            correo="luis@lumat.edu"
        )

        # 2. SOLUCIÓN AL INTEGRITY ERROR: Crear usuarios únicos para cada uno de los sinodales
        self.u_tutor = User.objects.create_user(
            username='usr_tutor_m', password='pwd')
        self.u_m1 = User.objects.create_user(
            username='usr_m1_m', password='pwd')
        self.u_m2 = User.objects.create_user(
            username='usr_m2_m', password='pwd')

        # 3. Asignar las instancias correspondientes al campo user de cada Docente
        self.tutor = Docente.objects.create(
            user=self.u_tutor, nombre="Carlos", apellido_paterno="Lopez", correo="t@uaz.mx")
        self.m1 = Docente.objects.create(
            user=self.u_m1, nombre="Maria", apellido_paterno="G", correo="m1@uaz.mx")
        self.m2 = Docente.objects.create(
            user=self.u_m2, nombre="Jose", apellido_paterno="S", correo="m2@uaz.mx")

        # 4. Construir la infraestructura del Comité y del Seminario con los objetos ya enlazados
        self.comite = Comite.objects.create(
            tutor=self.tutor, miembro1=self.m1, miembro2=self.m2)

        self.seminario = Seminario.objects.create(
            alumno=self.alumno,
            comite=self.comite,
            numero=8,
            periodo=1,
            fecha=datetime.date.today(),
            hora=datetime.time(10, 0)
        )

    # ── PATH 1: GENERACIÓN EXITOSA DE PDF SIN ANTECEDENTES DE ARCHIVO ──
    @patch('reportlab.lib.utils.ImageReader')
    def test_generar_y_guardar_pdf_exito_sin_acta_previa(self, mock_image_reader):
        """Genera el reporte correctamente y lo anexa al campo vacío actaComite del seminario."""
        # Configurar Mock del ImageReader de ReportLab para simular tamaños seguros de firmas
        mock_reader_instance = MagicMock()
        mock_reader_instance.getSize.return_value = (100, 100)
        mock_image_reader.return_value = mock_reader_instance

        formulario = FormularioComite(
            seminario=self.seminario,
            el_comite_encuentra="Excelente desarrollo",
            calificacion_tutor=Decimal("9.0"),
            calificacion_miembro1=Decimal("9.5"),
            calificacion_miembro2=Decimal("10.0")
        )

        # Evitamos que guarde físicamente en disco interceptando el save del modelo Seminario
        with patch.object(self.seminario, 'save', return_value=None):
            resultado = formulario.generar_y_guardar_pdf()

        # Validaciones de cobertura
        self.assertTrue(resultado)
        self.assertTrue(bool(formulario.seminario.actaComite))
        self.assertIn("acta_comite_sem8_p1_Luis_",
                      formulario.seminario.actaComite.name)

    # ── PATH 2: ELIMINACIÓN Y REEMPLAZO DE UN PDF EXISTENTE ──

    @patch('reportlab.lib.utils.ImageReader')
    def test_generar_y_guardar_pdf_reemplaza_archivo_existente(self, mock_image_reader):
        """Si el seminario ya contaba con un PDF archivado, lo elimina limpiamente antes de sobrescribir."""
        mock_reader_instance = MagicMock()
        mock_reader_instance.getSize.return_value = (100, 100)
        mock_image_reader.return_value = mock_reader_instance

        # Inicializamos el campo con un archivo simulado previo
        self.seminario.actaComite.save(
            "acta_vieja.pdf", ContentFile(b"%PDF-viejo"), save=False)

        formulario = FormularioComite(seminario=self.seminario)

        # Usamos patch.object sobre el método delete del archivo para poder usar las aserciones de mock
        with patch.object(formulario.seminario.actaComite, 'delete') as mock_delete:
            with patch.object(self.seminario, 'save', return_value=None):
                resultado = formulario.generar_y_guardar_pdf()

            # Comprobar que el método delete() de la línea de borrado previo fue ejecutado
            mock_delete.assert_called_once_with(save=False)

        self.assertTrue(resultado)

    @patch('lumat_app.utils_pdf_comite.generar_pdf_comite')
    def test_generar_y_guardar_pdf_atrapa_excepcion_y_retorna_false(self, mock_generar):
        """Si el compilador de ReportLab arroja un error imprevisto, captura la excepción y retorna False."""
        # Forzar que el generador lance un error de renderizado
        mock_generar.side_effect = Exception(
            "Fallo crítico en fuentes Tipográficas")

        formulario = FormularioComite(seminario=self.seminario)
        resultado = formulario.generar_y_guardar_pdf()

        # Comprobar que entró al bloque except de forma limpia devolviendo False
        self.assertFalse(resultado)


# class FormularioComiteModelTestCase(TestCase):

#     def setUp(self):
#         # 1. Configuración de usuarios base únicos
#         u_a = User.objects.create_user(
#             username='alumno_fc_test', password='pwd')
#         u_t = User.objects.create_user(
#             username='tutor_fc_test', password='pwd')
#         u_m1 = User.objects.create_user(username='m1_fc_test', password='pwd')
#         u_m2 = User.objects.create_user(username='m2_fc_test', password='pwd')

#         # Firma dummy requerida por el ImageField de Docente
#         firma_mock = SimpleUploadedFile(
#             name="firma.png",
#             content=b"\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\x3b",
#             content_type="image/png"
#         )

#         # 2. Creación de Alumnos (Uno regular y uno en octavo semestre)
#         self.alumno_quinto = Alumno.objects.create(
#             user=u_a, nombre="Luis", apellido_paterno="Vega", matricula="FC05", semestre="5"
#         )

#         # Alumno duplicando usuario dummy para aislar el escenario límite del semestre 8
#         u_a8 = User.objects.create_user(username='alumno_fc_8', password='pwd')
#         self.alumno_octavo = Alumno.objects.create(
#             user=u_a8, nombre="Juan", apellido_paterno="Perez", matricula="FC08", semestre="8"
#         )

#         # 3. Docentes y Comité Sínodo único
#         tutor = Docente.objects.create(
#             user=u_t, nombre="Carlos", apellido_paterno="Lopez", firma=firma_mock)
#         m1 = Docente.objects.create(
#             user=u_m1, nombre="Maria", apellido_paterno="Gomez", firma=firma_mock)
#         m2 = Docente.objects.create(
#             user=u_m2, nombre="Jose", apellido_paterno="Sanz", firma=firma_mock)
#         comite = Comite.objects.create(tutor=tutor, miembro1=m1, miembro2=m2)

#         # 4. Seminarios asociados correspondientes
#         self.seminario_quinto = Seminario.objects.create(
#             alumno=self.alumno_quinto, comite=comite, numero=5, periodo=1,
#             fecha=datetime.date.today(), hora=datetime.time(10, 0)
#         )

#         self.seminario_octavo = Seminario.objects.create(
#             alumno=self.alumno_octavo, comite=comite, numero=8, periodo=1,
#             fecha=datetime.date.today(), hora=datetime.time(11, 0)
#         )

#     # ── PRUEBA 1: ELIMINA LA LÍNEA PARCIAL 401 ↛ exit (ESCENARIO LÍMITE SEMESTRE 8) ──
#     @patch('lumat_app.models.FormularioComite.generar_y_guardar_pdf')
#     def test_save_alumno_en_semestre_ocho_no_se_promueve_mas(self, mock_pdf):
#         """
#         CUBRE RAMA 401 ↛ exit: Si el semestre actual es 8, la condición 'semestre_actual < 8'
#         da False, salta la mutación de semestre y finaliza el método de manera segura.
#         """
#         formulario = FormularioComite(
#             seminario=self.seminario_octavo,
#             calificacion_tutor=Decimal("9.00"),
#             calificacion_miembro1=Decimal("9.00"),
#             calificacion_miembro2=Decimal("9.00"),
#             firma_tutor=True,
#             firma_miembro1=True,
#             firma_miembro2=True
#         )
#         formulario.save()

#         # Comprobamos que el alumno sigue en el semestre 8 (no se incrementó a 9)
#         self.alumno_octavo.refresh_from_db()
#         self.assertEqual(self.alumno_octavo.semestre, "8")

#     # ── PRUEBA 2: COBERTURA TOTAL DE LAS VARIACIONES DEL MÉTODO __str__ ──
#     @patch('lumat_app.models.FormularioComite.generar_y_guardar_pdf')
#     def test_formulario_comite_str_con_y_sin_acta_pdf(self, mock_pdf):
#         """Prueba que el método __str__ refleje dinámicamente si el seminario tiene un PDF o no."""

#         # Caso A: Sin archivo actaComite en el seminario (Pintará un '✗ PDF')
#         formulario = FormularioComite.objects.create(
#             seminario=self.seminario_quinto,
#             estado_general="pendiente"
#         )
#         expected_str_sin_pdf = f"Formulario Comité — Seminario {self.seminario_quinto.id} (pendiente) ✗ PDF"
#         self.assertEqual(str(formulario), expected_str_sin_pdf)

#         # Caso B: Con un archivo asignado en actaComite (Pintará un '✓ PDF')
#         self.seminario_quinto.actaComite.save(
#             "acta_existente.pdf",
#             ContentFile(b"%PDF-1.4 binario_de_prueba"),
#             save=True
#         )
#         formulario.refresh_from_db()

#         expected_str_con_pdf = f"Formulario Comité — Seminario {self.seminario_quinto.id} (pendiente) ✓ PDF"
#         self.assertEqual(str(formulario), expected_str_con_pdf)

#         # Limpieza del archivo físico generado en la ejecución del Caso B
#         if self.seminario_quinto.actaComite and os.path.exists(self.seminario_quinto.actaComite.path):
#             import os
#             os.remove(self.seminario_quinto.actaComite.path)
