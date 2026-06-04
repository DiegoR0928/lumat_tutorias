import datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch
from django.test import TestCase
from django.core.files.base import ContentFile
from django.contrib.auth.models import User
from lumat_app.models import Alumno, Docente, Comite, Seminario, FormularioComite


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
        mock_reader_instance = MagicMock()
        mock_reader_instance.getSize.return_value = (100, 100)
        mock_image_reader.return_value = mock_reader_instance

        # Inicializamos el campo con un archivo simulado previo
        self.seminario.actaComite.save(
            "acta_vieja.pdf", ContentFile(b"%PDF-viejo"), save=False)

        formulario = FormularioComite(seminario=self.seminario)

        with patch.object(formulario.seminario.actaComite, 'delete') as mock_delete:
            with patch.object(self.seminario, 'save', return_value=None):
                resultado = formulario.generar_y_guardar_pdf()

            # Comprobar que el método delete() de la línea de borrado previo fue ejecutado
            mock_delete.assert_called_once_with(save=False)

        self.assertTrue(resultado)

    @patch('lumat_app.utils_pdf_comite.generar_pdf_comite')
    def test_generar_y_guardar_pdf_atrapa_excepcion_y_retorna_false(self, mock_generar):
        # Forzar que el generador lance un error de renderizado
        mock_generar.side_effect = Exception(
            "Fallo crítico en fuentes Tipográficas")

        formulario = FormularioComite(seminario=self.seminario)
        resultado = formulario.generar_y_guardar_pdf()

        # Comprobar que entró al bloque except de forma limpia devolviendo False
        self.assertFalse(resultado)
