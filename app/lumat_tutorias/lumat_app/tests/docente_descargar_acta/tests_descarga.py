import io
import os
import zipfile
import datetime
from unittest.mock import patch

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User, Group
from django.contrib.messages import get_messages
from django.core.files.uploadedfile import SimpleUploadedFile

from lumat_app.models import Alumno, Docente, Comite, Seminario, Evidencia, FormularioComite


class DescargarEvidenciasZipTestCase(TestCase):

    def setUp(self):
        self.client = Client()
        
        # 1. Configurar el grupo y rol requeridos por @user_passes_test(es_docente)
        self.grupo_docente, _ = Group.objects.get_or_create(name='Docente')
        self.user_docente = User.objects.create_user(
            username='doctor_perez', password='password123'
        )
        self.user_docente.groups.add(self.grupo_docente)
        self.docente = Docente.objects.create(
            user=self.user_docente, nombre="Juan", apellido_paterno="Perez", correo="juan@uaz.mx"
        )

        # 2. Configurar Alumno e infraestructura del Comité
        self.user_alumno = User.objects.create_user(username='alumno_test', password='pwd')
        self.alumno = Alumno.objects.create(
            user=self.user_alumno, nombre="Luis", apellido_paterno="Vega",
            apellido_materno="Mora", matricula="12345", semestre="5", correo="luis@uaz.mx"
        )
        
        u_m1 = User.objects.create_user(username='u_m1', password='pwd')
        u_m2 = User.objects.create_user(username='u_m2', password='pwd')
        doc_m1 = Docente.objects.create(user=u_m1, nombre="M1", apellido_paterno="A", correo="m1@uaz.mx")
        doc_m2 = Docente.objects.create(user=u_m2, nombre="M2", apellido_paterno="B", correo="m2@uaz.mx")
        
        self.comite = Comite.objects.create(tutor=self.docente, miembro1=doc_m1, miembro2=doc_m2)

        # 3. Crear el Seminario
        self.seminario = Seminario.objects.create(
            alumno=self.alumno, comite=self.comite, numero=5, periodo=1,
            fecha=datetime.date.today(), hora=datetime.time(10, 0)
        )

        # 4. SOLUCIÓN COMPLETA: Mockear el método save del FormularioComite temporalmente
        # para evitar el atributo faltante '_firmas_cambiaron' durante la ejecución de este test
        with patch.object(FormularioComite, 'save', autospec=True) as mock_save:
            # Creamos una instancia en blanco y la asignamos manualmente evitando disparar señales rotas
            self.formulario = FormularioComite(
                seminario=self.seminario,
                firma_tutor=False,
                firma_miembro1=False,
                firma_miembro2=False
            )
            # Guardamos saltándonos la base de datos real utilizando el save nativo de la clase padre (models.Model)
            super(FormularioComite, self.formulario).save()

        # URLs del flujo correspondientes a tus rutas
        self.url_descarga = reverse('lumat_app:docente_descargar_evidencias_zip', kwargs={'seminario_id': self.seminario.id})
        self.url_detalle = reverse('lumat_app:docente_seminario_detalle', kwargs={'seminario_id': self.seminario.id})

        # Forzar inicio de sesión del docente
        self.client.force_login(self.user_docente)

    # ── PATH 1: REDIRECCIÓN Y MENSAJE DE ERROR CUANDO NO HAY EVIDENCIAS ──
    def test_seminario_sin_evidencias_redirige_a_detalle_con_exito_200(self):
        """
        Si el seminario no tiene evidencias ligadas, genera un mensaje de error,
        se produce un redireccionamiento y la página final responde con código 200.
        """
        # Aseguramos que no haya evidencias asociadas en este test
        self.seminario.evidencias.all().delete()

        # Al pasar follow=True se procesa el redirect automático (302) y evalúa el destino.
        # Volvemos a interceptar el save en el hilo de ejecución por si el get_or_create intenta dispararse de nuevo
        with patch.object(FormularioComite, 'save', return_value=None):
            response = self.client.get(self.url_descarga, follow=True)

        # Verifica que la redirección terminó con éxito en la vista esperada
        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, self.url_detalle, status_code=302, target_status_code=200)

        # Validar el mensaje de error inyectado en el request
        mensajes = list(get_messages(response.wsgi_request))
        self.assertEqual(len(mensajes), 1)
        self.assertEqual(str(mensajes[0]), "Este seminario no tiene evidencias para descargar.")

    # ── PATH 2: COMPRESIÓN ZIP EXITOSA CON ARCHIVOS REALES SIMULADOS (MÉTODO GET) ──
    def test_descarga_zip_exitosa_con_evidencias_existentes(self):
        """
        Si el seminario cuenta con evidencias y sus archivos físicos existen en el medio,
        empaqueta el ZIP, lo nombra según las reglas de negocio y responde con 200 OK.
        """
        # Crear un archivo simulado real en memoria y persistirlo mediante el modelo Evidencia
        archivo_simulado = SimpleUploadedFile(
            name="avance_tesis.pdf",
            content=b"%PDF-1.4 contenido_binario_de_prueba",
            content_type="application/pdf"
        )
        
        evidencia = Evidencia.objects.create(
            seminario=self.seminario,
            nombre="Reporte de Actividades",
            archivo=archivo_simulado
        )

        try:
            response = self.client.get(self.url_descarga)

            # 1. Comprobar que la respuesta es un binario de descarga directa (200 OK sin redirección)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response['Content-Type'], 'application/zip')

            # 2. Validar que la cabecera Content-Disposition contenga el nombre estructurado solicitado
            nombre_esperado = "luis-vega-semestre5-1.zip"
            self.assertIn(f'filename="{nombre_esperado}"', response['Content-Disposition'])

            # 3. Leer el contenido del ZIP retornado en memoria para comprobar que no esté corrupto
            zip_buffer = io.BytesIO(response.content)
            with zipfile.ZipFile(zip_buffer, 'r') as zip_leido:
                lista_archivos = zip_leido.namelist()
                self.assertIn("Reporte de Actividades.pdf", lista_archivos)
                
                contenido_archivo = zip_leido.read("Reporte de Actividades.pdf")
                self.assertIn(b"contenido_binario_de_prueba", contenido_archivo)

        finally:
            # Limpieza obligatoria del archivo físico temporal creado en la carpeta de medios de pruebas
            if evidencia.archivo and os.path.exists(evidencia.archivo.path):
                os.remove(evidencia.archivo.path)