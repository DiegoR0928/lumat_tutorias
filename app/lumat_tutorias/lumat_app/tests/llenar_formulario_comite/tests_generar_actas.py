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

    # ── PATH 1: COMPILACIÓN COMPLETA SIN FIRMAS DIGITALES FÍSICAS ──
    def test_generar_pdf_comite_sin_firmas_exito(self):
        """Genera los bytes del PDF de forma correcta cuando los docentes aún no han firmado (línea clásica)."""
        pdf_bytes = generar_pdf_comite(self.formulario)
        
        # Validaciones de integridad del flujo binario
        self.assertIsInstance(pdf_bytes, bytes)
        self.assertTrue(pdf_bytes.startswith(b"%PDF"))  # Cabecera mágica de archivos PDF
        self.assertTrue(pdf_bytes.endswith(b"%%EOF\n") or b"%%EOF" in pdf_bytes)

    # ── PATH 2: COMPRESIÓN CON IMÁGENES DE FIRMA EXISTENTES EN EL DISCO (CORREGIDO) ──
    @patch('os.path.exists')
    @patch('reportlab.lib.utils.ImageReader')  # 👈 CORREGIDO: Apunta al origen real en ReportLab
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
        
    # ── PATH 3: CONTROL DE BIFURCACIÓN CUANDO FALTAN LOS ARCHIVOS DE IMAGEN EN DISCO ──
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

    # ── PATH 4: CAPTURA COMPLETA DE EXCEPCIONES EN EL FLUJO DE IMÁGENES ──
    @patch('os.path.exists')
    def test_generar_pdf_comite_captura_excepciones_de_renderizado_de_imagen(self, mock_exists):
        """Si ReportLab truena al leer la ruta de la firma, el bloque except la atrapa y monta el texto de respaldo [APROBADO]."""
        mock_exists.return_value = True
        
        self.formulario.firma_tutor = True
        # Forzamos un fallo de atributos en el path para obligar a entrar al bloque 'except Exception:'
        type(self.tutor.firma).path = property(lambda self: Exception("Fallo de IO en sector de disco simulado"))

        pdf_bytes = generar_pdf_comite(self.formulario)
        
        self.assertIsInstance(pdf_bytes, bytes)
        self.assertTrue(b"%PDF" in pdf_bytes)

    # ── PATH 5: COMPORTAMIENTO CON CAMPOS VACÍOS O EVALUACIONES EN BLANCO (VALORES 'NONE') ──
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