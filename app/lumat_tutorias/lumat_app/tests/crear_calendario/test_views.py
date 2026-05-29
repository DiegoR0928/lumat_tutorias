import tempfile
from datetime import date, time
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.contrib.auth.models import User
from lumat_app.models import Alumno, Docente, Comite
from lumat_app.models import Seminario, CalendarioGenerado


# 🌟 Redirige los archivos MEDIA de los test a una carpeta temporal limpia
@override_settings(MEDIA_ROOT=tempfile.gettempdir())
class TestCalendarioViews(TestCase):

    def setUp(self):
        self.client = Client()

        # Usuario Administrador de LUMAT (Staff para acceder a vistas admin)
        self.user_admin = User.objects.create_superuser(
            username='admin', password='testpass123'
        )

        # Usuario Alumno regular (Sin permisos de Staff)
        self.user_normal = User.objects.create_user(
            username='alumno1', password='testpass123'
        )

        # 1. Crear 3 docentes para cumplir con la regla de sínodo del comité
        u_d1 = User.objects.create_user(username='d1', password='123')
        u_d2 = User.objects.create_user(username='d2', password='123')
        u_d3 = User.objects.create_user(username='d3', password='123')

        doc1 = Docente.objects.create(user=u_d1)
        doc2 = Docente.objects.create(user=u_d2)
        doc3 = Docente.objects.create(user=u_d3)

        # 2. Instanciar el Comité base
        self.comite_test = Comite.objects.create(
            tutor=doc1,
            miembro1=doc2,
            miembro2=doc3
        )

        # 3. Crear los usuarios y registros para 2 alumnos base
        u_a1 = User.objects.create_user(username='a1', password='123')
        u_a2 = User.objects.create_user(username='a2', password='123')

        alumno1 = Alumno.objects.create(matricula="20260001", user=u_a1)
        alumno2 = Alumno.objects.create(matricula="20260002", user=u_a2)

        # 4. Instanciar 2 seminarios usando los campos obligatorios reales
        Seminario.objects.create(
            alumno=alumno1,
            comite=self.comite_test,
            fecha=date(2026, 6, 1),
            hora=time(9, 0)
        )
        Seminario.objects.create(
            alumno=alumno2,
            comite=self.comite_test,
            fecha=date(2026, 6, 2),
            hora=time(10, 0)
        )

        # Mapeo de URLs del sistema
        self.url_form = reverse('calendar_form')
        self.url_generate = reverse('calendar_pdf')

    # --- Pruebas de la Vista del Formulario (GET) ---

    def test_get_formulario_admin_retorna_200(self):
        """Un administrador autenticado debe poder cargar el panel."""
        self.client.login(username='admin', password='testpass123')
        response = self.client.get(self.url_form)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'admin/calendario_form.html')
        # Verifica que la lista de calendarios va incorporada en el contexto
        self.assertIn('calendarios', response.context)

    def test_usuario_sin_permisos_redirige_a_login(self):
        """Un alumno o usuario sin staff es rebotado por seguridad."""
        self.client.login(username='alumno1', password='testpass123')
        response = self.client.get(self.url_form)
        expected_url = f'/admin/login/?next={self.url_form}'
        self.assertRedirects(response, expected_url)

    # --- Pruebas del Algoritmo de Generación (POST) ---

    def test_generacion_exitosa_crea_objeto_y_redirige(self):
        """
        Crea el PDF, guarda el registro en BD y limpia los fines de semana.
        """
        self.client.login(username='admin', password='testpass123')

        # Rango amplio de 1 mes (Días hábiles de sobra para los 2 seminarios)
        datos = {
            'fecha_inicial': '2026-06-01',
            'fecha_final': '2026-06-30'
        }
        response = self.client.post(self.url_generate, datos)

        # Verifica redirección exitosa de vuelta al formulario (302)
        self.assertRedirects(response, self.url_form)
        # Verifica que se grabó el registro del PDF en la base de datos
        self.assertEqual(CalendarioGenerado.objects.count(), 1)

    def test_error_fecha_inicial_posterior_a_final(self):
        """Si la fecha inicial es mayor, cancela la operación con mensaje."""
        self.client.login(username='admin', password='testpass123')

        datos = {
            'fecha_inicial': '2026-06-15',
            'fecha_final': '2026-06-01'  # Fecha menor
        }
        response = self.client.post(self.url_generate, datos)

        self.assertRedirects(response, self.url_form)
        # Asegura que la base de datos se mantuvo intacta y protegida
        self.assertEqual(CalendarioGenerado.objects.count(), 0)

    def test_error_insuficientes_dias_habiles_para_seminarios(self):
        """Si hay más seminarios que días laborables, arroja alerta."""
        self.client.login(username='admin', password='testpass123')

        # El 6 y 7 de junio de 2026 son fin de semana. 0 días hábiles.
        datos = {
            'fecha_inicial': '2026-06-06',
            'fecha_final': '2026-06-07'
        }
        response = self.client.post(self.url_generate, datos)

        self.assertRedirects(response, self.url_form)
        self.assertEqual(CalendarioGenerado.objects.count(), 0)

    # --- Pruebas de Persistencia en el Sistema de Archivos ---

    def test_archivo_pdf_se_escribe_en_disco_exitosamente(self):
        """Verifica que el PDF se genere y almacene físicamente en MEDIA."""
        self.client.login(username='admin', password='testpass123')

        datos = {
            'fecha_inicial': '2026-06-01',
            'fecha_final': '2026-06-10'
        }
        self.client.post(self.url_generate, datos)

        # Obtenemos el registro generado de la base de datos
        cal = CalendarioGenerado.objects.first()

        # 1. Validar que el objeto tiene un archivo asociado
        self.assertIsNotNone(cal.archivo_pdf)

        # 2. Validar que el archivo físico existe en el storage del servidor
        archivo_existe = cal.archivo_pdf.storage.exists(cal.archivo_pdf.name)
        self.assertTrue(archivo_existe)
