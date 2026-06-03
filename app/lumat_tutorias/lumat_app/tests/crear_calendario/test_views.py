import tempfile
from datetime import date, time, timedelta
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.contrib.auth.models import User
from lumat_app.models import Alumno, Docente, Comite, Seminario, CalendarioGenerado


@override_settings(MEDIA_ROOT=tempfile.gettempdir())
class TestCalendarioAndEstadisticasViews(TestCase):

    def setUp(self):
        self.client = Client()
        self.user_admin = User.objects.create_superuser(
            username='admin', password='testpass123'
        )
        self.user_normal = User.objects.create_user(
            username='alumno1', password='testpass123'
        )
        self.url_form = reverse('calendar_form')
        self.url_generate = reverse('calendar_pdf')
        self.url_stats = reverse('admin_estadisticas')
        self.hoy = date.today()

    def helper_crear_entorno(self, num_seminarios=2):
        u_d1 = User.objects.create_user(username='d1', password='123')
        u_d2 = User.objects.create_user(username='d2', password='123')
        u_d3 = User.objects.create_user(username='d3', password='123')
        doc1 = Docente.objects.create(user=u_d1)
        doc2 = Docente.objects.create(user=u_d2)
        doc3 = Docente.objects.create(user=u_d3)
        comite = Comite.objects.create(
            tutor=doc1, miembro1=doc2, miembro2=doc3
        )
        for i in range(num_seminarios):
            u_a = User.objects.create_user(
                username=f'a_{i}', password='123'
            )
            alumno = Alumno.objects.create(
                matricula=f'mat_{i}', user=u_a
            )
            Seminario.objects.create(
                alumno=alumno,
                comite=comite,
                fecha=self.hoy,
                hora=time(9, 0),
                numero=i + 1
            )

    def test_get_formulario_admin_retorna_200(self):
        self.client.login(username='admin', password='testpass123')
        response = self.client.get(self.url_form)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'admin/calendario_form.html')
        self.assertIn('calendarios', response.context)

    def test_generar_pdf_get_redirige(self):
        self.client.login(username='admin', password='testpass123')
        response = self.client.get(self.url_generate)
        self.assertRedirects(response, self.url_form)

    def test_generar_pdf_fechas_vacias(self):
        self.client.login(username='admin', password='testpass123')
        datos = {'fecha_inicial': '', 'fecha_final': ''}
        response = self.client.post(self.url_generate, datos)
        self.assertRedirects(response, self.url_form)

    def test_generar_pdf_sin_seminarios(self):
        self.client.login(username='admin', password='testpass123')
        inicio = (self.hoy + timedelta(days=1)).strftime('%Y-%m-%d')
        fin = (self.hoy + timedelta(days=5)).strftime('%Y-%m-%d')
        datos = {'fecha_inicial': inicio, 'fecha_final': fin}
        response = self.client.post(self.url_generate, datos)
        self.assertRedirects(response, self.url_form)

    def test_error_fecha_inicio_anterior_a_hoy(self):
        self.helper_crear_entorno()
        self.client.login(username='admin', password='testpass123')
        inicio = (self.hoy - timedelta(days=1)).strftime('%Y-%m-%d')
        fin = (self.hoy + timedelta(days=5)).strftime('%Y-%m-%d')
        datos = {'fecha_inicial': inicio, 'fecha_final': fin}
        response = self.client.post(self.url_generate, datos)
        self.assertRedirects(response, self.url_form)
        self.assertEqual(CalendarioGenerado.objects.count(), 0)

    def test_error_mismo_dia_hoy_a_hoy(self):
        self.helper_crear_entorno()
        self.client.login(username='admin', password='testpass123')
        inicio = self.hoy.strftime('%Y-%m-%d')
        fin = self.hoy.strftime('%Y-%m-%d')
        datos = {'fecha_inicial': inicio, 'fecha_final': fin}
        response = self.client.post(self.url_generate, datos)
        self.assertRedirects(response, self.url_form)
        self.assertEqual(CalendarioGenerado.objects.count(), 0)

    def test_error_fecha_inicial_posterior_a_final(self):
        self.helper_crear_entorno()
        self.client.login(username='admin', password='testpass123')
        inicio = (self.hoy + timedelta(days=5)).strftime('%Y-%m-%d')
        fin = (self.hoy + timedelta(days=2)).strftime('%Y-%m-%d')
        datos = {'fecha_inicial': inicio, 'fecha_final': fin}
        response = self.client.post(self.url_generate, datos)
        self.assertRedirects(response, self.url_form)
        self.assertEqual(CalendarioGenerado.objects.count(), 0)

    def test_error_insuficientes_slots_horarios(self):
        self.helper_crear_entorno(num_seminarios=20)
        self.client.login(username='admin', password='testpass123')
        inicio = (self.hoy + timedelta(days=1))
        fin = (self.hoy + timedelta(days=2))
        datos = {
            'fecha_inicial': inicio.strftime('%Y-%m-%d'),
            'fecha_final': fin.strftime('%Y-%m-%d')
        }
        response = self.client.post(self.url_generate, datos)
        self.assertRedirects(response, self.url_form)
        self.assertEqual(CalendarioGenerado.objects.count(), 0)

    def test_generacion_exitosa_con_rollover_de_horas(self):
        self.helper_crear_entorno(num_seminarios=9)
        self.client.login(username='admin', password='testpass123')
        inicio = (self.hoy + timedelta(days=1))
        fin = (self.hoy + timedelta(days=15))
        datos = {
            'fecha_inicial': inicio.strftime('%Y-%m-%d'),
            'fecha_final': fin.strftime('%Y-%m-%d')
        }
        response = self.client.post(self.url_generate, datos)
        self.assertRedirects(response, self.url_form)
        self.assertEqual(CalendarioGenerado.objects.count(), 1)

        for sem in Seminario.objects.all():
            self.assertNotEqual(sem.fecha, self.hoy)
            self.assertIn(sem.hora.hour, range(8, 16))

    def test_get_estadisticas_vacias(self):
        self.client.login(username='admin', password='testpass123')
        response = self.client.get(self.url_stats)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'admin/estadisticas.html')
        self.assertEqual(response.context['total_alumnos'], 0)
        self.assertEqual(response.context['promedio_seminarios'], 0)

    def test_get_estadisticas_con_datos(self):
        self.helper_crear_entorno(num_seminarios=2)
        self.client.login(username='admin', password='testpass123')
        response = self.client.get(self.url_stats)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_alumnos'], 2)
        self.assertEqual(response.context['total_seminarios'], 2)
        self.assertEqual(response.context['promedio_seminarios'], 1.0)
