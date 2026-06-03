import datetime
from datetime import time
from io import BytesIO
from unittest.mock import patch, MagicMock

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User, Group
from django.contrib.messages import get_messages

from lumat_app.models import Alumno, Docente, Comite, Seminario, ActaAlumnoData


class GenerarActaViewAllPathsTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.url = reverse('lumat_app:generar_acta', kwargs={'num': 1})
        self.url_detalle = reverse(
            'lumat_app:seminario_detalle', kwargs={'num': 1})

        # 1. Configurar el rol y el grupo requeridos para pasar el decorador @user_passes_test(es_alumno)
        self.grupo_alumno, _ = Group.objects.get_or_create(name='Alumno')
        self.user_alumno = User.objects.create_user(
            username='alumno_sga', password='password123')
        self.user_alumno.groups.add(self.grupo_alumno)

        # 2. Configurar la instancia del Alumno
        self.alumno = Alumno.objects.create(
            user=self.user_alumno, nombre="Luis", apellido_paterno="Vega",
            apellido_materno="Mora", matricula="12345", semestre="1", correo="luis@lumat.edu"
        )

        # 3. Crear docentes indispensables para construir el Comité Tutor
        user_tutor = User.objects.create_user(
            username='u_tutor', password='pwd')
        user_m1 = User.objects.create_user(username='u_m1', password='pwd')
        user_m2 = User.objects.create_user(username='u_m2', password='pwd')

        self.docente_tutor = Docente.objects.create(
            user=user_tutor, nombre="Dr. T", apellido_paterno="P", correo="t@edu")
        self.docente_m1 = Docente.objects.create(
            user=user_m1, nombre="Dra. M1", apellido_paterno="T1", correo="m1@edu")
        self.docente_m2 = Docente.objects.create(
            user=user_m2, nombre="Dr. M2", apellido_paterno="T2", correo="m2@edu")

        self.comite = Comite.objects.create(
            tutor=self.docente_tutor, miembro1=self.docente_m1, miembro2=self.docente_m2)

        # 4. Configurar el Seminario completado por defecto (con calificación)
        self.seminario = Seminario.objects.create(
            alumno=self.alumno, numero=1, periodo=1, calificacion=9.5,
            comite=self.comite, fecha=datetime.date(2026, 6, 1), hora=time(10, 0)
        )

        # 5. Payload válido basado en los campos del formulario HTML provisto
        self.payload_valido = {
            'actividad_principal': 'Desarrollo de Tesis en Software',
            'reuniones_tutor': 4,
            'reuniones_comite': 1,
            'coloquios': 1,
            'cursos': 'Ninguno',
            'articulos': 'Ninguno',
            'eventos': 'Ninguno',
            'plan_siguiente': 'Graduación',
            'comentarios': 'Todo correcto'
        }

        # Forzar el inicio de sesión del alumno para evitar bloqueos de cuenta
        self.client.force_login(self.user_alumno)

    # ── PATH 1: REDIRECCIÓN CUANDO NO EXISTE EL SEMINARIO ──
    def test_seminario_inexistente_redirige_a_detalle_200(self):
        """Si se busca un número de seminario que no existe, da error y el destino responde con 200."""
        url_invalida = reverse('lumat_app:generar_acta', kwargs={
                               'num': 9})  # No existe seminario 9
        response = self.client.post(url_invalida, data=self.payload_valido)

        # Comprobar la redirección hacia la vista detalle correspondiente
        url_detalle_invalida = reverse(
            'lumat_app:seminario_detalle', kwargs={'num': 9})
        self.assertRedirects(response, url_detalle_invalida,
                             status_code=302, target_status_code=200)

        mensajes = list(get_messages(response.wsgi_request))
        self.assertEqual(
            str(mensajes[0]), "No hay seminario registrado para este número.")

    # ── PATH 2: REDIRECCIÓN CUANDO EL SEMINARIO NO TIENE CALIFICACIÓN ──
    def test_seminario_sin_calificacion_redirige_a_detalle_200(self):
        """Si el seminario existe pero no tiene calificación, da error y el destino responde con 200."""
        self.seminario.calificacion = None
        self.seminario.save()

        response = self.client.post(self.url, data=self.payload_valido)

        self.assertRedirects(response, self.url_detalle,
                             status_code=302, target_status_code=200)

        mensajes = list(get_messages(response.wsgi_request))
        self.assertEqual(
            str(mensajes[0]), "Solo puedes generar el acta de un seminario completado.")

    # ── PATH 3: REDIRECCIÓN CUANDO EL ACTA YA EXISTE (POST) ──
    def test_acta_ya_existente_bloquea_post_y_redirige_a_detalle_200(self):
        """Si el acta ya fue creada con anterioridad, prohíbe la duplicación y el destino responde con 200."""
        # Instanciar un acta previa ligada al seminario
        ActaAlumnoData.objects.create(
            seminario=self.seminario, actividad_principal="Previa", plan_siguiente="Previa")

        response = self.client.post(self.url, data=self.payload_valido)

        self.assertRedirects(response, self.url_detalle,
                             status_code=302, target_status_code=200)

        mensajes = list(get_messages(response.wsgi_request))
        self.assertEqual(
            str(mensajes[0]), "Tu acta ya fue generada y no puede modificarse.")

    # ── PATH 4: REDIRECCIÓN POR FORMULARIO INVALIDO ──
    def test_formulario_invalido_guarda_en_sesion_y_redirige_a_detalle_200(self):
        """Si faltan campos requeridos, guarda la información en la sesión y el destino responde con 200."""
        payload_incompleto = {
            'actividad_principal': '',  # Campo obligatorio vacío
            'reuniones_tutor': -5       # Dato numérico erróneo
        }
        response = self.client.post(self.url, data=payload_incompleto)

        self.assertRedirects(response, self.url_detalle,
                             status_code=302, target_status_code=200)

        # Verificar resguardo de variables en sesión para no borrar el progreso del alumno
        self.assertIn('failed_acta_form_data', self.client.session)

        mensajes = list(get_messages(response.wsgi_request))
        self.assertEqual(str(
            mensajes[0]), "Por favor corrige los campos marcados en rojo antes de guardar.")

    # ── PATH 5: FLUJO COMPLETO EXITOSO (POST) ──
    @patch('lumat_app.views.generar_acta_alumno')
    def test_flujo_exitoso_crea_datos_pdf_y_redirige_a_detalle_200(self, mock_generar_pdf):
        """Flujo ideal: persiste datos, guarda archivo adjunto en Seminario y el destino responde con 200."""
        # Mockear el generador ReportLab para retornar un flujo BytesIO simulado
        mock_buffer = MagicMock()
        mock_buffer.read.return_value = b"%PDF-1.4 simulacion_binaria_pdf"
        mock_generar_pdf.return_value = mock_buffer

        response = self.client.post(self.url, data=self.payload_valido)

        # Validar redirección y estado 200 de la página de destino final
        self.assertRedirects(response, self.url_detalle,
                             status_code=302, target_status_code=200)

        # Validar persistencia en BD
        self.assertTrue(ActaAlumnoData.objects.filter(
            seminario=self.seminario).exists())

        # Validar actualización física del campo de archivo (FileField) en Seminario
        self.seminario.refresh_from_db()
        self.assertTrue(self.seminario.actaAlumno.name.startswith("acta_1_"))

        mensajes = list(get_messages(response.wsgi_request))
        self.assertEqual(
            str(mensajes[0]), "Acta generada y guardada correctamente.")

    # ── PATH 6: REDIRECCIÓN POR EXCEPCIÓN / FALLO TÉCNICO PDF ──
    @patch('lumat_app.views.generar_acta_alumno')
    def test_error_en_pdf_limpia_data_y_redirige_a_detalle_200(self, mock_generar_pdf):
        """Si el compilador de ReportLab arroja una excepción, borra data huérfana y el destino responde con 200."""
        mock_generar_pdf.side_effect = Exception(
            "Fallo crítico inesperado de ReportLab")

        response = self.client.post(self.url, data=self.payload_valido)

        self.assertRedirects(response, self.url_detalle,
                             status_code=302, target_status_code=200)

        # Validar la limpieza de datos (rollback manual) en el bloque except
        self.assertFalse(ActaAlumnoData.objects.filter(
            seminario=self.seminario).exists())

        mensajes = list(get_messages(response.wsgi_request))
        self.assertIn("Error al generar el PDF técnico", str(mensajes[0]))

    # ── PATH 7: REDIRECCIÓN EN ACCESO POR MÉTODO GET ──
    def test_peticion_get_manual_redirige_a_detalle_200(self):
        """Si un alumno intenta forzar la URL por método GET, se le deniega el acceso y el destino responde con 200."""
        response = self.client.get(self.url)

        self.assertRedirects(response, self.url_detalle,
                             status_code=302, target_status_code=200)
