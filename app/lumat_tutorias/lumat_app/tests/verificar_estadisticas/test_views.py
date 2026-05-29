from datetime import date, time
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from lumat_app.models import Alumno, Docente, Comite, Seminario


class TestEstadisticasAdminView(TestCase):

    def setUp(self):
        """Configuración inicial para las pruebas de estadísticas."""
        self.client = Client()

        # Usuario Administrador (Staff con acceso completo)
        self.user_admin = User.objects.create_superuser(
            username='admin', password='testpass123'
        )

        # Usuario Alumno regular (Sin permisos de administrador)
        self.user_normal = User.objects.create_user(
            username='alumno_regular', password='testpass123'
        )

        # Nombre de la ruta configurada en tu urls.py principal
        self.url_estadisticas = reverse('admin_estadisticas')

    def test_get_estadisticas_admin_retorna_200(self):
        """Un superusuario debería poder cargar el panel de estadísticas."""
        self.client.login(username='admin', password='testpass123')
        response = self.client.get(self.url_estadisticas)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'admin/estadisticas.html')

    def test_usuario_sin_permisos_redirige_a_login(self):
        """Un usuario común es rebotado al login del admin por seguridad."""
        self.client.login(username='alumno_regular', password='testpass123')
        response = self.client.get(self.url_estadisticas)
        
        expected_url = f'/admin/login/?next={self.url_estadisticas}'
        self.assertRedirects(response, expected_url)

    def test_metricas_vacias_retornan_ceros(self):
        """Si la BD está vacía, el promedio debe ser 0 evitando un crash."""
        self.client.login(username='admin', password='testpass123')
        response = self.client.get(self.url_estadisticas)

        self.assertEqual(response.context['total_alumnos'], 0)
        self.assertEqual(response.context['total_docentes'], 0)
        self.assertEqual(response.context['total_seminarios'], 0)
        self.assertEqual(response.context['promedio_seminarios'], 0)

    def test_calculo_correcto_de_metricas_y_promedio(self):
        """Verifica que cuente bien los registros y procese el promedio."""
        # 1. Crear 3 docentes para cumplir con la regla de sínodo único
        u_d1 = User.objects.create_user(username='d1', password='123')
        u_d2 = User.objects.create_user(username='d2', password='123')
        u_d3 = User.objects.create_user(username='d3', password='123')
        
        doc1 = Docente.objects.create(user=u_d1)
        doc2 = Docente.objects.create(user=u_d2)
        doc3 = Docente.objects.create(user=u_d3)

        # 2. Instanciar el Comité obligatorio para los seminarios
        comite_ejemplo = Comite.objects.create(
            tutor=doc1,
            miembro1=doc2,
            miembro2=doc3
        )

        # 3. Crear los usuarios y registros para 2 alumnos base
        u_a1 = User.objects.create_user(username='a1', password='123')
        u_a2 = User.objects.create_user(username='a2', password='123')
        
        alumno1 = Alumno.objects.create(matricula="20260001", user=u_a1)
        alumno2 = Alumno.objects.create(matricula="20260002", user=u_a2)

        # 4. Crear 3 seminarios inyectando todas sus dependencias confirmadas
        Seminario.objects.create(
            alumno=alumno1,
            comite=comite_ejemplo,
            fecha=date(2026, 6, 1),
            hora=time(10, 0)
        )
        Seminario.objects.create(
            alumno=alumno1,
            comite=comite_ejemplo,
            fecha=date(2026, 6, 2),
            hora=time(11, 0)
        )
        Seminario.objects.create(
            alumno=alumno2,
            comite=comite_ejemplo,
            fecha=date(2026, 6, 3),
            hora=time(12, 0)
        )

        # Ejecutar la petición autenticados como administrador
        self.client.login(username='admin', password='testpass123')
        response = self.client.get(self.url_estadisticas)

        # 5. Validaciones de la lógica del contexto enviado a la plantilla
        self.assertEqual(response.context['total_alumnos'], 2)
        self.assertEqual(response.context['total_docentes'], 3)
        self.assertEqual(response.context['total_seminarios'], 3)
        
        # 3 seminarios / 2 alumnos = 1.5 en promedio esperado
        self.assertEqual(response.context['promedio_seminarios'], 1.5)