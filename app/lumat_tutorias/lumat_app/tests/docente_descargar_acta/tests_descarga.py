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
        self.user_alumno = User.objects.create_user(
            username='alumno_test', password='pwd')
        self.alumno = Alumno.objects.create(
            user=self.user_alumno, nombre="Luis", apellido_paterno="Vega",
            apellido_materno="Mora", matricula="12345", semestre="5", correo="luis@uaz.mx"
        )

        u_m1 = User.objects.create_user(username='u_m1', password='pwd')
        u_m2 = User.objects.create_user(username='u_m2', password='pwd')
        doc_m1 = Docente.objects.create(
            user=u_m1, nombre="M1", apellido_paterno="A", correo="m1@uaz.mx")
        doc_m2 = Docente.objects.create(
            user=u_m2, nombre="M2", apellido_paterno="B", correo="m2@uaz.mx")

        self.comite = Comite.objects.create(
            tutor=self.docente, miembro1=doc_m1, miembro2=doc_m2)

        # 3. Crear el Seminario
        self.seminario = Seminario.objects.create(
            alumno=self.alumno, comite=self.comite, numero=5,
            fecha=datetime.date.today(), hora=datetime.time(10, 0)
        )

        with patch.object(FormularioComite, 'save', autospec=True):
            self.formulario = FormularioComite(
                seminario=self.seminario,
                firma_tutor=False,
                firma_miembro1=False,
                firma_miembro2=False
            )
            super(FormularioComite, self.formulario).save()

        self.url_descarga = reverse('lumat_app:docente_descargar_evidencias_zip', kwargs={
                                    'seminario_id': self.seminario.id})
        self.url_detalle = reverse('lumat_app:docente_seminario_detalle', kwargs={
                                   'seminario_id': self.seminario.id})

        # Forzar inicio de sesión del docente
        self.client.force_login(self.user_docente)

    # ── PATH 1: REDIRECCIÓN Y MENSAJE DE ERROR CUANDO NO HAY EVIDENCIAS ──
    def test_seminario_sin_evidencias_redirige_a_detalle_con_exito_200(self):
        """
        Si el seminario no tiene evidencias ligadas, genera un mensaje de error,
        se produce un redireccionamiento y la página final responde con código 200.
        """
        self.seminario.evidencias.all().delete()

        with patch.object(FormularioComite, 'save', return_value=None):
            response = self.client.get(self.url_descarga, follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, self.url_detalle,
                             status_code=302, target_status_code=200)

        mensajes = list(get_messages(response.wsgi_request))
        self.assertEqual(len(mensajes), 1)
        self.assertEqual(
            str(mensajes[0]), "Este seminario no tiene evidencias para descargar.")

    # ── PATH 2: COMPRESIÓN ZIP EXITOSA MANEJANDO EXTENSIONES (CUBRE RAMA 424 ↛ 428) ──
    def test_descarga_zip_exitosa_con_evidencias_existentes(self):
        archivo_simulado1 = SimpleUploadedFile(
            name="avance_tesis.pdf",
            content=b"%PDF-1.4 contenido_evidencia_1",
            content_type="application/pdf"
        )
        archivo_simulado2 = SimpleUploadedFile(
            name="grafica.png",
            content=b"contenido_evidencia_2",
            content_type="image/png"
        )

        evidencia_sin_ext = Evidencia.objects.create(
            seminario=self.seminario,
            nombre="Reporte de Actividades",  # Sin el '.pdf'
            archivo=archivo_simulado1
        )

        evidencia_con_ext = Evidencia.objects.create(
            seminario=self.seminario,
            nombre="esquema_datos.png",  # Ya incluye el '.png'
            archivo=archivo_simulado2
        )

        try:
            response = self.client.get(self.url_descarga)

            self.assertEqual(response.status_code, 200)
            self.assertEqual(response['Content-Type'], 'application/zip')

            nombre_esperado = "luis-vega-semestre5-1.zip"
            self.assertIn(f'filename="{nombre_esperado}"',
                          response['Content-Disposition'])

            # Validar que el ZIP se estructuró de forma correcta por dentro
            zip_buffer = io.BytesIO(response.content)
            with zipfile.ZipFile(zip_buffer, 'r') as zip_leido:
                lista_archivos = zip_leido.namelist()
                # Comprobamos que a la evidencia A se le anexó automáticamente '.pdf'
                self.assertIn("Reporte de Actividades.pdf", lista_archivos)
                self.assertIn("esquema_datos.png", lista_archivos)

                contenido_archivo = zip_leido.read(
                    "Reporte de Actividades.pdf")
                self.assertIn(b"contenido_evidencia_1", contenido_archivo)

        finally:
            # Limpieza obligatoria preventiva del storage de pruebas
            if evidencia_sin_ext.archivo and os.path.exists(evidencia_sin_ext.archivo.path):
                os.remove(evidencia_sin_ext.archivo.path)
            if evidencia_con_ext.archivo and os.path.exists(evidencia_con_ext.archivo.path):
                os.remove(evidencia_con_ext.archivo.path)

    # ── PATH 3: ARCHIVO ELIMINADO FÍSICAMENTE (CUBRE LA RAMA PARCIAL 419 ↛ 418) ──
    def test_descargar_zip_evidencia_sin_archivo_fisico_en_disco(self):
        """
        Si un registro existe en la base de datos de evidencias pero el archivo físico no
        está físicamente en el storage, os.path.exists da False, saltando de regreso al ciclo for.
        """
        archivo_dummy = SimpleUploadedFile(
            "archivo_fantasma.txt", b"Texto de prueba")
        evidencia = Evidencia.objects.create(
            seminario=self.seminario,
            nombre="Evidencia_Falsa",
            archivo=archivo_dummy
        )

        # Forzamos la ausencia del recurso eliminándolo de la carpeta de pruebas antes del GET
        if os.path.exists(evidencia.archivo.path):
            os.remove(evidencia.archivo.path)

        # Ejecutamos la petición (El ZIP se compilará vacío de forma segura)
        response = self.client.get(self.url_descarga)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/zip')
