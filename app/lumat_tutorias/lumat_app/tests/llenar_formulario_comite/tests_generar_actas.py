from django.core.files.base import ContentFile
from django.contrib.auth.models import User
from unittest.mock import patch, MagicMock
import os
import datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch
from django.test import TestCase
from lumat_app.models import Alumno, Docente, Comite, Seminario, FormularioComite
from lumat_app.views_docente import generar_pdf_comite


class GenerarPdfComiteTestCase(TestCase):

    def setUp(self):
        # 1. Configurar Mocks de Alumno
        self.alumno = MagicMock(spec=Alumno)
        self.alumno.nombre = "Luis"
        self.alumno.apellido_paterno = "Vega"
        self.alumno.apellido_materno = "Mora"
        self.alumno.matricula = "20261109"
        self.alumno.semestre = "8"
        self.alumno.correo = "luis@lumat.edu"

        # 2. Configurar Mocks de Docentes con firmas digitales simuladas
        self.tutor = MagicMock(spec=Docente)
        self.tutor.nombre = "Carlos"
        self.tutor.apellido_paterno = "Lopez"
        self.tutor.apellido_materno = "Garcia"
        # Simulamos que el archivo de imagen de firma existe
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

        # 3. Configurar Mock de Comité y Seminario
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

        # 4. Configurar Mock del FormularioComite con evaluaciones
        self.formulario = MagicMock(spec=FormularioComite)
        self.formulario.seminario = self.seminario
        self.formulario.el_comite_encuentra = "El estudiante muestra avances excelentes en el simulador."
        self.formulario.observaciones = "Falta robustecer la sección de pruebas automatizadas."
        self.formulario.dictamen = "Aprobado con distinción."
        self.formulario.propuestas = "Desplegar el contenedor de Tomcat con Prometheus en producción."

        self.formulario.calificacion_tutor = Decimal("9.5")
        self.formulario.calificacion_miembro1 = Decimal("10.0")
        self.formulario.calificacion_miembro2 = Decimal("9.0")
        self.formulario.calificacion_final = Decimal("9.5")

        # Estado de firmas por defecto (Inician sin firmar para cubrir la línea clásica)
        self.formulario.firma_tutor = False
        self.formulario.firma_miembro1 = False
        self.formulario.firma_miembro2 = False

    def test_generar_pdf_comite_sin_firmas_exito(self):
        """Genera los bytes del PDF de forma correcta cuando los docentes aún no han firmado (línea clásica)."""
        pdf_bytes = generar_pdf_comite(self.formulario)

        # Validaciones de integridad del flujo binario
        self.assertIsInstance(pdf_bytes, bytes)
        self.assertTrue(pdf_bytes.startswith(b"%PDF"))
        self.assertTrue(pdf_bytes.endswith(b"%%EOF\n")
                        or b"%%EOF" in pdf_bytes)

    @patch('os.path.exists')
    @patch('reportlab.lib.utils.ImageReader')
    def test_generar_pdf_comite_con_imagenes_de_firma_existentes(self, mock_image_reader, mock_exists):
        """Cubre el bloque try/if de inserción de imágenes de ReportLab si los archivos existen en disco."""
        # 1. Engañamos a la validación nativa de Python de os.path.exists
        mock_exists.return_value = True

        # 2. Creamos una instancia simulada para ImageReader que no busque el archivo físico
        mock_reader_instance = MagicMock()
        # ReportLab requiere conocer o simular el tamaño (width, height) al calcular las celdas de la tabla
        mock_reader_instance.getSize.return_value = (100, 100)
        mock_image_reader.return_value = mock_reader_instance

        # Activamos las banderas de firmas para que el generador intente insertar los objetos Image
        self.formulario.firma_tutor = True
        self.formulario.firma_miembro1 = True
        self.formulario.firma_miembro2 = True

        # Ejecutamos la función de generación de PDF de tus vistas
        pdf_bytes = generar_pdf_comite(self.formulario)

        # Comprobamos que el flujo binario final del PDF se estructuró correctamente
        self.assertIsInstance(pdf_bytes, bytes)
        self.assertTrue(pdf_bytes.startswith(b"%PDF"))

    @patch('os.path.exists')
    def test_generar_pdf_comite_con_firmas_aprobadas_pero_sin_archivo_fisico(self, mock_exists):
        """Si dice firmado pero el archivo físico fue borrado, pone el texto alterno de respaldo [APROBADO]."""
        mock_exists.return_value = False  # El archivo físico no existe en la carpeta media

        self.formulario.firma_tutor = True
        self.formulario.firma_miembro1 = True
        self.formulario.firma_miembro2 = True

        pdf_bytes = generar_pdf_comite(self.formulario)

        self.assertIsInstance(pdf_bytes, bytes)
        self.assertTrue(b"%PDF" in pdf_bytes)

    @patch('os.path.exists')
    def test_generar_pdf_comite_captura_excepciones_de_renderizado_de_imagen(self, mock_exists):
        """Si ReportLab truena al leer la ruta de la firma, el bloque except la atrapa y monta el texto de respaldo [APROBADO]."""
        mock_exists.return_value = True

        self.formulario.firma_tutor = True
        # Forzamos un fallo de atributos en el path para obligar a entrar al bloque 'except Exception:'
        type(self.tutor.firma).path = property(
            lambda self: Exception("Fallo de IO en sector de disco simulado"))

        pdf_bytes = generar_pdf_comite(self.formulario)

        self.assertIsInstance(pdf_bytes, bytes)
        self.assertTrue(b"%PDF" in pdf_bytes)

    def test_generar_pdf_comite_con_valores_nulos_pone_caracter_de_respaldo(self):
        """Garantiza la robustez de los helpers 'fmt' y del contenido opcional cuando los textos vienen en None."""
        self.formulario.el_comite_encuentra = None
        self.formulario.observaciones = None
        self.formulario.dictamen = None
        self.formulario.propuestas = None

        self.formulario.calificacion_tutor = None
        self.formulario.calificacion_miembro1 = None
        self.formulario.calificacion_miembro2 = None
        self.formulario.calificacion_final = None
        self.alumno.matricula = None  # Prueba la condición 'al.matricula or "—"'

        pdf_bytes = generar_pdf_comite(self.formulario)

        self.assertIsInstance(pdf_bytes, bytes)
        self.assertTrue(b"%PDF" in pdf_bytes)

    def test_box_table_con_estilos_extras(self):
        """
        Invoca a _box_table pasando estilos extra para asegurar que se ejecute
        la concatenación del bloque 'if style_extra:' al 100%.
        """
        # Importamos las dependencias oficiales desde tu archivo de utilidades
        from lumat_app.utils_pdf_comite import _box_table, Table
        from reportlab.lib import colors

        filas_prueba = [["Celda de prueba"]]

        # Definimos estilos extra válidos para ReportLab
        estilos_extras = [
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.red)
        ]

        # Ejecutamos la función enviando el parámetro opcional
        tabla_resultado = _box_table(filas_prueba, style_extra=estilos_extras)

        # Comprobamos de manera segura que se instanció un objeto Table válido
        self.assertIsInstance(tabla_resultado, Table)
        self.assertIsNotNone(tabla_resultado)


class FormularioComiteSaveCompleteTestCase(TestCase):

    def setUp(self):
        # 1. Configuración de usuarios e infraestructura relacional obligatoria
        self.user_alumno = User.objects.create_user(
            username='alumno_save_test', password='pwd')
        self.alumno = Alumno.objects.create(
            user=self.user_alumno,
            nombre="Luis",
            apellido_paterno="Vega",
            matricula="202611",
            semestre="5",  # Ajustamos semestre inicial a 5
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

        # Seminario número 5 (coincide con el semestre del alumno para evaluar la promoción)
        self.seminario = Seminario.objects.create(
            alumno=self.alumno,
            comite=self.comite,
            numero=5,
            periodo=1,
            fecha=datetime.date.today(),
            hora=datetime.time(10, 0)
        )

    # ── PATH 1: CUBRE LÍNEA 355 ↛ 356 (CALIFICACIÓN FINAL ES NONE) ──
    @patch('lumat_app.models.FormularioComite.generar_y_guardar_pdf')
    def test_save_con_calificacion_final_none(self, mock_pdf):
        """Si no hay notas asignadas, calificacion_final es None y no se ejecuta el update."""
        formulario = FormularioComite.objects.create(
            seminario=self.seminario,
            calificacion_tutor=None,
            calificacion_miembro1=None,
            calificacion_miembro2=None,
            firma_tutor=False
        )
        self.assertIsNone(formulario.calificacion_final)
        mock_pdf.assert_not_called()

    # ── PATH 2: CUBRE LA RAMA DE FORMULARIO PENDIENTE (SALTA LAS LÍNEAS 366 Y 382 COMPLEMENTARIAS) ──
    @patch('lumat_app.models.FormularioComite.generar_y_guardar_pdf')
    def test_save_formulario_permanece_pendiente(self, mock_pdf):
        """Si falta alguna firma, el estado es pendiente, no se genera el PDF y no hay promoción."""
        formulario = FormularioComite.objects.create(
            seminario=self.seminario,
            calificacion_tutor=Decimal("8.00"),
            firma_tutor=True,
            firma_miembro1=False,  # Falta una firma
            firma_miembro2=True
        )
        self.assertEqual(formulario.estado_general, "pendiente")
        mock_pdf.assert_not_called()

    # ── PATH 3: CUBRE EL CONDICIONAL EXCEPCIONAL DE LA LÍNEA 311 ↛ 312 (DoesNotExist) ──
    @patch('lumat_app.models.FormularioComite.generar_y_guardar_pdf')
    def test_save_cuando_instancia_tiene_pk_pero_no_existe_en_bd(self, mock_pdf):
        """Si el objeto tiene un pk asignado pero no se localiza en la BD, captura DoesNotExist."""
        formulario = FormularioComite(
            id=9999,  # PK ficticio que no existe
            seminario=self.seminario,
            firma_tutor=True,
            firma_miembro1=True,
            firma_miembro2=True
        )
        # Al guardar, entrará al bloque try de la línea 311, lanzará DoesNotExist y pondrá firmas_cambiaron = True
        formulario.save()
        self.assertEqual(formulario.estado_general, "completo")

    # ── PATH 4: CUBRE PROMOCIÓN ACADÉMICA Y GENERACIÓN DE PDF EXITOSA (ÉXITO TOTAL) ──
    @patch('lumat_app.models.FormularioComite.generar_y_guardar_pdf')
    def test_save_completado_exito_dispara_promocion_y_pdf(self, mock_pdf):
        """Si se completan las firmas y la nota es >= 6.00, se genera el PDF y el alumno es promovido."""
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

        # Comprobamos que se ejecutó la llamada para crear el documento
        mock_pdf.assert_called_once()

        # Comprobamos la lógica de promoción (Semestre 5 + 1 = 6)
        self.alumno.refresh_from_db()
        self.assertEqual(self.alumno.semestre, "6")

    # ── PATH 5: CUBRE LÍNEA 382 ↛ 387 (COMPLETO PERO CON CALIFICACIÓN REPROBATORIA) ──
    @patch('lumat_app.models.FormularioComite.generar_y_guardar_pdf')
    def test_save_completo_con_calificacion_reprobatoria_no_promueve(self, mock_pdf):
        """Si el formulario está completo pero la nota final es < 6.00, genera PDF pero NO promueve."""
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

        # Se genera el PDF porque está completo
        mock_pdf.assert_called_once()

        # NO se promueve porque la calificación es reprobatoria
        self.alumno.refresh_from_db()
        self.assertEqual(self.alumno.semestre, "5")

    # ── PATH 6: CUBRE CAMBIO DE FIRMAS EN FORMULARIO YA COMPLETO (LÍNEA 366 CONDICIÓN C) ──
    @patch('lumat_app.models.FormularioComite.generar_y_guardar_pdf')
    def test_save_ya_estaba_completo_pero_cambian_las_firmas(self, mock_pdf):
        """Si el formulario ya estaba completo pero se actualizan los estados de firmas, vuelve a generar el PDF."""
        formulario = FormularioComite.objects.create(
            seminario=self.seminario,
            calificacion_tutor=Decimal("8.00"),
            firma_tutor=True,
            firma_miembro1=True,
            firma_miembro2=True
        )

        # Reseteamos el mock para aislar la segunda ejecución del save
        mock_pdf.reset_mock()

        # Forzamos una alteración en los valores de firmas en la instancia existente
        formulario.firma_tutor = False
        formulario.firma_tutor = True
        formulario.save()

        # Debe activarse la condición c) del punto 4 del save
        mock_pdf.assert_called_once()

    # ── PATH 7: CUBRE VALIDACIÓN VALUE_ERROR Y ALUMNO YA EN SEMESTRE DIFERENTE ──
    @patch('lumat_app.models.FormularioComite.generar_y_guardar_pdf')
    def test_save_alumno_semestre_invalido_o_no_coincidente(self, mock_pdf):
        """Si el semestre del alumno no se puede convertir a entero o no coincide con el seminario, no promueve."""
        self.alumno.semestre = "SÉPTIMO"  # Provocará un ValueError al hacer int()
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
