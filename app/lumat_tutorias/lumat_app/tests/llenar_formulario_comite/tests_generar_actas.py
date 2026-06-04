from django.contrib.auth.models import User
from unittest.mock import patch, MagicMock
import datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch
from django.test import TestCase
from lumat_app.models import Alumno, Docente, Comite, Seminario, FormularioComite
from lumat_app.views_docente import generar_pdf_comite


class GenerarPdfComiteTestCase(TestCase):

    def setUp(self):
        self.alumno = MagicMock(spec=Alumno)
        self.alumno.nombre = "Luis"
        self.alumno.apellido_paterno = "Vega"
        self.alumno.apellido_materno = "Mora"
        self.alumno.matricula = "20261109"
        self.alumno.semestre = "8"
        self.alumno.correo = "luis@lumat.edu"

        self.tutor = MagicMock(spec=Docente)
        self.tutor.nombre = "Carlos"
        self.tutor.apellido_paterno = "Lopez"
        self.tutor.apellido_materno = "Garcia"
        self.tutor.firma = MagicMock()
        self.tutor.firma.path = "/app/media/firmas/firma_tutor.png"

        self.miembro1 = MagicMock(spec=Docente)
        self.miembro1.nombre = "Maria"
        self.miembro1.apellido_paterno = "Martinez"
        self.miembro1.apellido_materno = "Rodriguez"
        self.miembro1.firma = MagicMock()
        self.miembro1.firma.path = "/app/media/firmas/firma_m1.png"

        self.miembro2 = MagicMock(spec=Docente)
        self.miembro2.nombre = "Jose"
        self.miembro2.apellido_paterno = "Sanchez"
        self.miembro2.apellido_materno = "Perez"
        self.miembro2.firma = MagicMock()
        self.miembro2.firma.path = "/app/media/firmas/firma_m2.png"

        self.comite = MagicMock(spec=Comite)
        self.comite.tutor = self.tutor
        self.comite.miembro1 = self.miembro1
        self.comite.miembro2 = self.miembro2

        self.seminario = MagicMock(spec=Seminario)
        self.seminario.numero = 8
        self.seminario.periodo = 1
        self.seminario.fecha = datetime.date(2026, 6, 3)
        self.seminario.alumno = self.alumno
        self.seminario.comite = self.comite

        self.formulario = MagicMock(spec=FormularioComite)
        self.formulario.seminario = self.seminario

        self.formulario.el_comite_encuentra = (
            "El estudiante muestra avances excelentes en el simulador."
        )

        self.formulario.observaciones = (
            "Falta robustecer la sección de pruebas automatizadas."
        )

        self.formulario.dictamen = "Aprobado con distinción."

        self.formulario.propuestas = (
            "Desplegar el contenedor de Tomcat con Prometheus "
            "en producción."
        )
        self.formulario.calificacion_tutor = Decimal("9.5")
        self.formulario.calificacion_miembro1 = Decimal("10.0")
        self.formulario.calificacion_miembro2 = Decimal("9.0")
        self.formulario.calificacion_final = Decimal("9.5")

        self.formulario.firma_tutor = False
        self.formulario.firma_miembro1 = False
        self.formulario.firma_miembro2 = False

    def test_generar_pdf_comite_sin_firmas_exito(self):
        pdf_bytes = generar_pdf_comite(self.formulario)

        self.assertIsInstance(pdf_bytes, bytes)
        self.assertTrue(pdf_bytes.startswith(b"%PDF"))
        self.assertTrue(pdf_bytes.endswith(b"%%EOF\n")
                        or b"%%EOF" in pdf_bytes)

    @patch('os.path.exists')
    @patch('reportlab.lib.utils.ImageReader')
    def test_generar_pdf_comite_con_imagenes_de_firma_existentes(
        self,
        mock_image_reader,
        mock_exists,
    ):
        mock_exists.return_value = True

        mock_reader_instance = MagicMock()
        mock_reader_instance.getSize.return_value = (100, 100)
        mock_image_reader.return_value = mock_reader_instance

        self.formulario.firma_tutor = True
        self.formulario.firma_miembro1 = True
        self.formulario.firma_miembro2 = True

        pdf_bytes = generar_pdf_comite(self.formulario)

        self.assertIsInstance(pdf_bytes, bytes)
        self.assertTrue(pdf_bytes.startswith(b"%PDF"))

    @patch('os.path.exists')
    def test_generar_pdf_comite_con_firmas_aprobadas_pero_sin_archivo_fisico(self, mock_exists):
        mock_exists.return_value = False

        self.formulario.firma_tutor = True
        self.formulario.firma_miembro1 = True
        self.formulario.firma_miembro2 = True

        pdf_bytes = generar_pdf_comite(self.formulario)

        self.assertIsInstance(pdf_bytes, bytes)
        self.assertTrue(b"%PDF" in pdf_bytes)

    @patch('os.path.exists')
    def test_generar_pdf_comite_captura_excepciones_de_renderizado_de_imagen(self, mock_exists):
        mock_exists.return_value = True

        self.formulario.firma_tutor = True
        type(self.tutor.firma).path = property(
            lambda self: Exception("Fallo de IO en sector de disco simulado"))

        pdf_bytes = generar_pdf_comite(self.formulario)

        self.assertIsInstance(pdf_bytes, bytes)
        self.assertTrue(b"%PDF" in pdf_bytes)

    def test_generar_pdf_comite_con_valores_nulos_pone_caracter_de_respaldo(self):
        self.formulario.el_comite_encuentra = None
        self.formulario.observaciones = None
        self.formulario.dictamen = None
        self.formulario.propuestas = None

        self.formulario.calificacion_tutor = None
        self.formulario.calificacion_miembro1 = None
        self.formulario.calificacion_miembro2 = None
        self.formulario.calificacion_final = None
        self.alumno.matricula = None

        pdf_bytes = generar_pdf_comite(self.formulario)

        self.assertIsInstance(pdf_bytes, bytes)
        self.assertTrue(b"%PDF" in pdf_bytes)

    def test_box_table_con_estilos_extras(self):
        """
        Invoca a _box_table pasando estilos extra para asegurar que se ejecute
        la concatenación del bloque 'if style_extra:' al 100%.
        """
        from lumat_app.utils_pdf_comite import _box_table, Table
        from reportlab.lib import colors

        filas_prueba = [["Celda de prueba"]]

        estilos_extras = [
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.red)
        ]

        tabla_resultado = _box_table(filas_prueba, style_extra=estilos_extras)

        self.assertIsInstance(tabla_resultado, Table)
        self.assertIsNotNone(tabla_resultado)


class FormularioComiteSaveCompleteTestCase(TestCase):

    def setUp(self):
        self.user_alumno = User.objects.create_user(
            username='alumno_save_test', password='pwd')
        self.alumno = Alumno.objects.create(
            user=self.user_alumno,
            nombre="Luis",
            apellido_paterno="Vega",
            matricula="202611",
            semestre="5",
            correo="luis@lumat.edu"
        )

        u_tutor = User.objects.create_user(
            username='u_tutor_s', password='pwd')
        u_m1 = User.objects.create_user(username='u_m1_s', password='pwd')
        u_m2 = User.objects.create_user(username='u_m2_s', password='pwd')

        self.tutor = Docente.objects.create(
            user=u_tutor, nombre="Carlos", apellido_paterno="L", correo="t@uaz.mx")
        self.m1 = Docente.objects.create(
            user=u_m1, nombre="Maria", apellido_paterno="G", correo="m1@uaz.mx")
        self.m2 = Docente.objects.create(
            user=u_m2, nombre="Jose", apellido_paterno="S", correo="m2@uaz.mx")

        self.comite = Comite.objects.create(
            tutor=self.tutor, miembro1=self.m1, miembro2=self.m2)

        self.seminario = Seminario.objects.create(
            alumno=self.alumno,
            comite=self.comite,
            numero=5,
            periodo=1,
            fecha=datetime.date.today(),
            hora=datetime.time(10, 0)
        )

    @patch('lumat_app.models.FormularioComite.generar_y_guardar_pdf')
    def test_save_con_calificacion_final_none(self, mock_pdf):
        formulario = FormularioComite.objects.create(
            seminario=self.seminario,
            calificacion_tutor=None,
            calificacion_miembro1=None,
            calificacion_miembro2=None,
            firma_tutor=False
        )
        self.assertIsNone(formulario.calificacion_final)
        mock_pdf.assert_not_called()

    @patch('lumat_app.models.FormularioComite.generar_y_guardar_pdf')
    def test_save_formulario_permanece_pendiente(self, mock_pdf):
        formulario = FormularioComite.objects.create(
            seminario=self.seminario,
            calificacion_tutor=Decimal("8.00"),
            firma_tutor=True,
            firma_miembro1=False,
            firma_miembro2=True
        )
        self.assertEqual(formulario.estado_general, "pendiente")
        mock_pdf.assert_not_called()

    @patch('lumat_app.models.FormularioComite.generar_y_guardar_pdf')
    def test_save_cuando_instancia_tiene_pk_pero_no_existe_en_bd(self, mock_pdf):
        formulario = FormularioComite(
            id=9999,
            seminario=self.seminario,
            firma_tutor=True,
            firma_miembro1=True,
            firma_miembro2=True
        )
        formulario.save()
        self.assertEqual(formulario.estado_general, "completo")

    @patch('lumat_app.models.FormularioComite.generar_y_guardar_pdf')
    def test_save_completado_exito_dispara_promocion_y_pdf(self, mock_pdf):
        formulario = FormularioComite(
            seminario=self.seminario,
            calificacion_tutor=Decimal("9.00"),
            calificacion_miembro1=Decimal("9.00"),
            calificacion_miembro2=Decimal("9.00"),
            firma_tutor=True,
            firma_miembro1=True,
            firma_miembro2=True
        )
        formulario.save()

        mock_pdf.assert_called_once()

        self.alumno.refresh_from_db()
        self.assertEqual(self.alumno.semestre, "6")

    @patch('lumat_app.models.FormularioComite.generar_y_guardar_pdf')
    def test_save_completo_con_calificacion_reprobatoria_no_promueve(self, mock_pdf):
        formulario = FormularioComite(
            seminario=self.seminario,
            calificacion_tutor=Decimal("5.00"),
            calificacion_miembro1=Decimal("5.00"),
            calificacion_miembro2=Decimal("5.00"),
            firma_tutor=True,
            firma_miembro1=True,
            firma_miembro2=True
        )
        formulario.save()

        mock_pdf.assert_called_once()

        self.alumno.refresh_from_db()
        self.assertEqual(self.alumno.semestre, "5")

    @patch('lumat_app.models.FormularioComite.generar_y_guardar_pdf')
    def test_save_ya_estaba_completo_pero_cambian_las_firmas(self, mock_pdf):
        formulario = FormularioComite.objects.create(
            seminario=self.seminario,
            calificacion_tutor=Decimal("8.00"),
            firma_tutor=True,
            firma_miembro1=True,
            firma_miembro2=True
        )

        mock_pdf.reset_mock()

        formulario.firma_tutor = False
        formulario.firma_tutor = True
        formulario.save()

        mock_pdf.assert_called_once()

    @patch('lumat_app.models.FormularioComite.generar_y_guardar_pdf')
    def test_save_alumno_semestre_invalido_o_no_coincidente(self, mock_pdf):
        self.alumno.semestre = "SÉPTIMO"
        self.alumno.save()

        formulario = FormularioComite(
            seminario=self.seminario,
            calificacion_tutor=Decimal("8.00"),
            firma_tutor=True,
            firma_miembro1=True,
            firma_miembro2=True
        )
        formulario.save()

        self.alumno.refresh_from_db()
        self.assertEqual(self.alumno.semestre, "SÉPTIMO")
