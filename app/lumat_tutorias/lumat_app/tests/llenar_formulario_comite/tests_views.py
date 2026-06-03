from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User, Group
from datetime import date, time, timedelta
from unittest.mock import patch
from lumat_app.models import Docente, Comite, Seminario, Alumno, FormularioComite, CalendarioGenerado

class ViewsTests(TestCase):

    def setUp(self):
        # 1. Configuración de seguridad y grupos para burlar el @user_passes_test
        self.user_docente = User.objects.create_user(username='docente', password='123')
        
        # Agregamos el usuario a ambas variantes de grupo comunes para mitigar typos en el decorador
        for nombre_grupo in ['Docentes', 'Docente']:
            grupo, _ = Group.objects.get_or_create(name=nombre_grupo)
            self.user_docente.groups.add(grupo)

        self.docente = Docente.objects.create(user=self.user_docente, nombre="Docente", apellido_paterno="Test")

        # Usuarios secundarios de soporte para los comités
        self.otro_user = User.objects.create_user(username='otro', password='123')
        self.otro_docente = Docente.objects.create(user=self.otro_user, nombre="Otro", apellido_paterno="Docente")
        
        self.tercer_user = User.objects.create_user(username='tercer')
        self.tercer_docente = Docente.objects.create(user=self.tercer_user, nombre="T")

        # 2. Alumnos con sus correspondientes usuarios vinculados (Evita IntegrityError)
        self.user_alumno1 = User.objects.create_user(username='alumno1')
        self.user_alumno2 = User.objects.create_user(username='alumno2')

        self.alumno1 = Alumno.objects.create(user=self.user_alumno1, matricula="220301", nombre="Alumno Uno")
        self.alumno2 = Alumno.objects.create(user=self.user_alumno2, matricula="220302", nombre="Alumno Dos")

        # 3. Comités válidos
        self.comite_tutor = Comite.objects.create(tutor=self.docente, miembro1=self.otro_docente, miembro2=self.tercer_docente)
        self.comite_miembro = Comite.objects.create(tutor=self.otro_docente, miembro1=self.docente, miembro2=self.tercer_docente)

        # 4. Objeto de calendario requerido en el contexto de la vista
        CalendarioGenerado.objects.create(
            nombre="Periodo Test", 
            fecha_inicio=date.today(), 
            fecha_fin=date.today() + timedelta(days=30)
        )

        # 5. Parche múltiple para aislar los métodos colaterales del save() de tu FormularioComite
        with patch.object(FormularioComite, '_firmas_cambiaron', create=True, return_value=False), \
             patch.object(FormularioComite, '_sincronizar_calificacion', create=True, return_value=None), \
             patch.object(FormularioComite, '_debe_generar_pdf', create=True, return_value=False), \
             patch.object(FormularioComite, '_promover_alumno_si_corresponde', create=True, return_value=None):
            
            self.sem_tutor = Seminario.objects.create(
                alumno=self.alumno1, comite=self.comite_tutor, fecha=date.today() + timedelta(days=2),
                hora=time(10, 0), numero=1, periodo=1
            )
            self.sem_miembro = Seminario.objects.create(
                alumno=self.alumno2, comite=self.comite_miembro, fecha=date.today() + timedelta(days=5),
                hora=time(11, 0), numero=2, periodo=1
            )
            
            self.form_tutor = FormularioComite.objects.create(seminario=self.sem_tutor, estado_general='pendiente')
            self.form_miembro = FormularioComite.objects.create(seminario=self.sem_miembro, estado_general='completo')

        # === CORRECCIÓN CLAVE: Forzar estados reales en la BD saltándonos el método save() ===
        FormularioComite.objects.filter(id=self.form_tutor.id).update(estado_general='pendiente')
        FormularioComite.objects.filter(id=self.form_miembro.id).update(estado_general='completo')

        # 6. URL utilizando el namespace correcto encontrado en tus urls.py
        self.url = reverse('lumat_app:docente_seminarios')

    def test_vista_protegida_usuario_anonimo(self):
        """Autenticación: Usuario anónimo es redirigido al login."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_vista_acceso_autorizado_y_contexto(self):
        """Código HTTP, Template correcto y Contexto Base."""
        self.client.login(username='docente', password='123')
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'docente_seminario.html')
        self.assertEqual(response.context['docente'], self.docente)

    def test_filtro_por_busqueda_matricula_flujo_a(self):
        """Filtros (Flujo A): Buscar por matrícula ignora filtros de rol/estado."""
        self.client.login(username='docente', password='123')
        response = self.client.get(self.url, {'q': '220301', 'rol': 'miembro', 'estado': 'completados'})
        
        seminarios_retornados = [item['seminario'] for item in response.context['seminarios']]
        self.assertIn(self.sem_tutor, seminarios_retornados)
        self.assertEqual(response.context['rol_activo'], 'todos')
        self.assertEqual(response.context['estado_activo'], 'todos')

    def test_filtro_por_rol_y_estado_flujo_b(self):
        """Filtros (Flujo B): Dropdowns de control en la pantalla."""
        self.client.login(username='docente', password='123')

        # Caso 1: Rol = miembro, Estado = completados (Debe encontrar sem_miembro ya que es 'completo')
        response = self.client.get(self.url, {'rol': 'miembro', 'estado': 'completados'})
        seminarios_retornados = [item['seminario'] for item in response.context['seminarios']]
        self.assertIn(self.sem_miembro, seminarios_retornados)
        self.assertNotIn(self.sem_tutor, seminarios_retornados)

        # Caso 2: Rol = tutor, Estado = pendientes (Debe encontrar sem_tutor ya que es 'pendiente')
        response = self.client.get(self.url, {'rol': 'tutor', 'estado': 'pendientes'})
        seminarios_retornados = [item['seminario'] for item in response.context['seminarios']]
        self.assertIn(self.sem_tutor, seminarios_retornados)
        self.assertNotIn(self.sem_miembro, seminarios_retornados)

    def test_proximos_seminarios_excluye_completados_y_pasados(self):
        """Seguridad/Lógica: Próximos seminarios solo incluye fechas >= hoy y estado 'pendiente'."""
        self.client.login(username='docente', password='123')
        
        with patch.object(FormularioComite, '_firmas_cambiaron', create=True, return_value=False), \
             patch.object(FormularioComite, '_sincronizar_calificacion', create=True, return_value=None), \
             patch.object(FormularioComite, '_debe_generar_pdf', create=True, return_value=False), \
             patch.object(FormularioComite, '_promover_alumno_si_corresponde', create=True, return_value=None):
             
            seminario_pasado = Seminario.objects.create(
                alumno=self.alumno1, comite=self.comite_tutor, fecha=date.today() - timedelta(days=1),
                hora=time(9, 0), numero=3, periodo=1
            )
            f_pasado = FormularioComite.objects.create(seminario=seminario_pasado, estado_general='pendiente')
            FormularioComite.objects.filter(id=f_pasado.id).update(estado_general='pendiente')

        response = self.client.get(self.url)
        proximos = [item['seminario'] for item in response.context['proximos_seminarios']]
        
        self.assertIn(self.sem_tutor, proximos)
        # sem_miembro: Completo (NO DEBE ESTAR)
        self.assertNotIn(self.sem_miembro, proximos)
        # seminario_pasado: Pasado (NO DEBE ESTAR)
        self.assertNotIn(seminario_pasado, proximos)