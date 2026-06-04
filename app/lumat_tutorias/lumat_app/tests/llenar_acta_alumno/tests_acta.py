import datetime
import io
import os
from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User, Group
from django.contrib.messages import get_messages
from django.core.files.uploadedfile import SimpleUploadedFile

from lumat_app.models import Alumno, Docente, Comite, Seminario, ActaAlumnoData


class GenerarActaViewTestCase(TestCase):

    def setUp(self):
        self.client = Client()

        # 1. Configurar el grupo y rol requeridos por @user_passes_test(es_alumno)
        self.grupo_alumno, _ = Group.objects.get_or_create(name='Alumno')
        self.user_alumno = User.objects.create_user(
            username='alumno_test_acta', password='password123')
        self.user_alumno.groups.add(self.grupo_alumno)

        self.alumno = Alumno.objects.create(
            user=self.user_alumno,
            nombre="Luis",
            apellido_paterno="Vega",
            matricula="2026_AA",
            semestre="5",
            correo="luis@lumat.edu"
        )

        self.imagen_firma = SimpleUploadedFile(
            name="firma_dummie.png",
            content=(
                b"\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00"
                b"\x00\x00\x00\xff\xff\xff\x21\xf9\x04\x01\x00\x00\x00"
                b"\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02"
                b"\x4c\x01\x00\x3b"
            ),
            content_type="image/png"
        )

        # 3. Infraestructura de docentes ÚNICOS con firmas asignadas para pasar Comite.clean()
        u_t = User.objects.create_user(username='u_t_a', password='pwd')
        u_m1 = User.objects.create_user(username='u_m1_a', password='pwd')
        u_m2 = User.objects.create_user(username='u_m2_a', password='pwd')

        self.doc_t = Docente.objects.create(
            user=u_t,
            nombre="Tutor",
            apellido_paterno="A",
            correo="t@uaz.mx",
            firma=self.imagen_firma,
        )

        self.doc_m1 = Docente.objects.create(
            user=u_m1,
            nombre="Miembro1",
            apellido_paterno="B",
            correo="m1@uaz.mx",
            firma=self.imagen_firma,
        )

        self.doc_m2 = Docente.objects.create(
            user=u_m2,
            nombre="Miembro2",
            apellido_paterno="C",
            correo="m2@uaz.mx",
            firma=self.imagen_firma,
        )

        self.comite = Comite.objects.create(
            tutor=self.doc_t, miembro1=self.doc_m1, miembro2=self.doc_m2)

        # 4. Crear un seminario calificado válido (Seminario número 1)
        self.seminario_calificado = Seminario.objects.create(
            alumno=self.alumno,
            comite=self.comite,
            numero=1,
            periodo=1,
            fecha=datetime.date.today(),
            hora=datetime.time(10, 0),
            calificacion=Decimal("9.50")
        )

        # 5. Crear un seminario SIN calificar (Seminario número 2)
        self.seminario_sin_calificar = Seminario.objects.create(
            alumno=self.alumno,
            comite=self.comite,
            numero=2,
            periodo=1,
            fecha=datetime.date.today(),
            hora=datetime.time(11, 0),
            calificacion=None
        )

        # Forzar el login del alumno bajo prueba
        self.client.force_login(self.user_alumno)

    def tearDown(self):
        """Limpieza física del sistema de archivos posterior a la ejecución de las pruebas."""
        for docente in [self.doc_t, self.doc_m1, self.doc_m2]:
            if docente.firma and os.path.exists(docente.firma.path):
                os.remove(docente.firma.path)

    # ── PATH 1: CORREGIDO PARA REDIRECCIONES EN CADENA MULTIPLE (num=9) ──
    def test_generar_acta_seminario_inexistente_error_y_redirige(self):
        url = reverse('lumat_app:generar_acta', kwargs={'num': 9})
        response = self.client.get(url)

        # Validamos el código de redirección inicial de forma directa
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('lumat_app:seminario_detalle', kwargs={
                             'num': 9}), status_code=302, target_status_code=302)

        mensajes = list(get_messages(response.wsgi_request))
        self.assertEqual(len(mensajes), 1)
        self.assertEqual(
            str(mensajes[0]), "No hay seminario registrado para este número.")

    # ── PATH 2: CUBRE LA LÍNEA PARCIAL 270 ↛ 275 (SEMINARIO SIN NOTA) ──
    def test_generar_acta_seminario_sin_calificacion_error_y_redirige(self):
        """Si el seminario existe pero no tiene calificación asignada, prohíbe la generación."""
        url = reverse('lumat_app:generar_acta', kwargs={'num': 2})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse(
            'lumat_app:seminario_detalle', kwargs={'num': 2}))

        mensajes = list(get_messages(response.wsgi_request))
        self.assertEqual(len(mensajes), 1)
        self.assertEqual(
            str(mensajes[0]), "Solo puedes generar el acta de un seminario completado.")

    # ── PATH 3: INTENTO DE ACCESO POR MÉTODO GET MANUAL ──
    def test_generar_acta_peticion_get_manual_redirige_a_detalle(self):
        url = reverse('lumat_app:generar_acta', kwargs={'num': 1})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse(
            'lumat_app:seminario_detalle', kwargs={'num': 1}))

    # ── PATH 4: POST RECHAZADO POR ACTA YA EXISTENTE ANTERIORMENTE ──
    def test_post_generar_acta_ya_existente_warning_y_redirige(self):
        ActaAlumnoData.objects.create(
            seminario=self.seminario_calificado,
            actividad_principal="Simulador educativo de Física Cuántica",
            plan_siguiente="Escritura de capítulo 3"
        )

        url = reverse('lumat_app:generar_acta', kwargs={'num': 1})
        response = self.client.post(
            url, data={'actividad_principal': 'Otra actividad'})

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse(
            'lumat_app:seminario_detalle', kwargs={'num': 1}))

        mensajes = list(get_messages(response.wsgi_request))
        self.assertEqual(
            str(mensajes[0]), "Tu acta ya fue generada y no puede modificarse.")

    # ── PATH 5: CORREGIDO PARA LA SESIÓN DIRECTA EN EL REQUEST DE DJANGO ──
    @patch('lumat_app.views.ActaAlumnoForm')
    def test_post_generar_acta_formulario_invalido_guarda_en_sesion(self, mock_form_class):
        mock_form_instance = mock_form_class.return_value
        mock_form_instance.is_valid.return_value = False

        url = reverse('lumat_app:generar_acta', kwargs={'num': 1})
        payload = {'actividad_principal': 'Contenido Incompleto'}

        response = self.client.post(url, data=payload)

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse(
            'lumat_app:seminario_detalle', kwargs={'num': 1}))

        # Validamos directamente contra el objeto session del request que procesó la vista
        self.assertIn('failed_acta_form_data', response.wsgi_request.session)
        self.assertEqual(
            response.wsgi_request.session['failed_acta_form_data'][
                'actividad_principal'
            ],
            'Contenido Incompleto',
        )

        mensajes = list(get_messages(response.wsgi_request))
        self.assertEqual(str(
            mensajes[0]), "Por favor corrige los campos marcados en rojo antes de guardar.")

    # ── PATH 6: POST EXCEPCIÓN AL RENDERIZAR EL PDF (CON DETECCIÓN DE DATA HUÉRFANA) ──
    @patch('lumat_app.views.generar_acta_alumno')
    @patch('lumat_app.views.ActaAlumnoForm')
    def test_post_generar_acta_falla_renderizador_pdf_elimina_data_y_redirige(
        self,
        mock_form_class,
        mock_generar_pdf,
    ):
        mock_form_instance = mock_form_class.return_value
        mock_form_instance.is_valid.return_value = True
        mock_form_instance.cleaned_data = {
            'actividad_principal': 'Desarrollo de Software IoT',
            'plan_siguiente': 'Pruebas de estres'
        }

        mock_generar_pdf.side_effect = Exception(
            "Falta de memoria RAM en el servidor")

        url = reverse('lumat_app:generar_acta', kwargs={'num': 1})
        response = self.client.post(
            url, data={'actividad_principal': 'Desarrollo de Software IoT'})

        self.assertEqual(response.status_code, 302)
        self.assertEqual(ActaAlumnoData.objects.filter(
            seminario=self.seminario_calificado).count(), 0)

        mensajes = list(get_messages(response.wsgi_request))
        self.assertIn(
            "Error al generar el PDF técnico: "
            "Falta de memoria RAM en el servidor",
            str(mensajes[0]),
        )

    # ── PATH 7: POST PROCESAMIENTO TOTALMENTE EXITOSO ──
    @patch('lumat_app.views.generar_acta_alumno')
    @patch('lumat_app.views.ActaAlumnoForm')
    def test_post_generar_acta_exito_total_guarda_archivo(
        self,
        mock_form_class,
        mock_generar_pdf,
    ):
        mock_form_instance = mock_form_class.return_value
        mock_form_instance.is_valid.return_value = True
        mock_form_instance.cleaned_data = {
            'actividad_principal': 'Interactive High School Physics Simulator',
            'plan_siguiente': 'Desplegar en producción'
        }

        buffer_simulado = io.BytesIO(b"%PDF-1.5 contenido_binario_acta_alumno")
        mock_generar_pdf.return_value = buffer_simulado

        url = reverse('lumat_app:generar_acta', kwargs={'num': 1})
        response = self.client.post(
            url, data={'actividad_principal': 'Interactive High School Physics Simulator'})

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse(
            'lumat_app:seminario_detalle', kwargs={'num': 1}))

        self.assertEqual(ActaAlumnoData.objects.filter(
            seminario=self.seminario_calificado).count(), 1)

        self.seminario_calificado.refresh_from_db()
        self.assertTrue(bool(self.seminario_calificado.actaAlumno))
        self.assertIn("acta_1_2026_AA.pdf",
                      self.seminario_calificado.actaAlumno.name)

        mensajes = list(get_messages(response.wsgi_request))
        self.assertEqual(
            str(mensajes[0]), "Acta generada y guardada correctamente.")

        if (
            self.seminario_calificado.actaAlumno
            and os.path.exists(
                self.seminario_calificado.actaAlumno.path
            )
        ):
            os.remove(self.seminario_calificado.actaAlumno.path)
