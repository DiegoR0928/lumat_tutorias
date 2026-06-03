import datetime
from unittest.mock import patch
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User, Group  # <-- Importamos Group

from lumat_app.models import Alumno, Docente, Comite, Seminario, FormularioComite


class DocenteDescargarActaViewTest(TestCase):

    def setUp(self):
        self.client = Client()

        # 1. Crear el grupo 'Docente' requerido por el decorador @user_passes_test
        self.grupo_docente, _ = Group.objects.get_or_create(name='Docente')

        # 2. Crear alumnos y usuarios base
        self.user_alumno = User.objects.create_user(
            username='alumno_sga', password='123')
        self.alumno = Alumno.objects.create(
            user=self.user_alumno, nombre="Luis", apellido_paterno="Vega", correo="l@edu"
        )

        # 3. Crear los docentes y agregarlos al grupo de seguridad
        self.user_docente_autorizado = User.objects.create_user(
            username='docente_comite', password='123')
        self.user_docente_no_autorizado = User.objects.create_user(
            username='docente_ajeno', password='123')

        # Inyección crucial del rol de grupo
        self.user_docente_autorizado.groups.add(self.grupo_docente)
        self.user_docente_no_autorizado.groups.add(self.grupo_docente)

        self.docente_autorizado = Docente.objects.create(
            user=self.user_docente_autorizado, nombre="Dr. T",
            apellido_paterno="Pérez", correo="t@edu")
        self.docente_no_autorizado = Docente.objects.create(
            user=self.user_docente_no_autorizado, nombre="Dr. X",
            apellido_paterno="A", correo="x@edu")

        # Miembros adicionales para cumplir restricciones de unicidad en Comité
        u1 = User.objects.create(username='u1')
        u2 = User.objects.create(username='u2')
        d1 = Docente.objects.create(user=u1, nombre="M1", apellido_paterno="A")
        d2 = Docente.objects.create(user=u2, nombre="M2", apellido_paterno="B")

        # 4. Construir Comité y Seminario
        self.comite = Comite.objects.create(
            tutor=self.docente_autorizado, miembro1=d1, miembro2=d2)

        self.seminario = Seminario.objects.create(
            alumno=self.alumno, comite=self.comite, numero=1, periodo=1,
            fecha=datetime.date(2026, 6, 1), hora=datetime.time(10, 0)
        )

        # 5. Crear el Formulario del Comité
        self.formulario = FormularioComite.objects.create(
            seminario=self.seminario,
            el_comite_encuentra="Excelente progreso",
            estado_general="pendiente"
        )

        self.url_descarga = reverse('lumat_app:docente_descargar_acta', kwargs={
                                    'seminario_id': self.seminario.id})

    # ── CASO 1: DESCARGA EXITOSA (HTTP 200 + CABECERAS PDF) ──
    @patch('lumat_app.views_docente.generar_pdf_comite')
    def test_descargar_acta_exitoso_codigo_200(self, mock_generar_pdf):
        """Un docente autorizado descarga el acta: retorna HTTP 200, tipo PDF y adjunto."""
        self.client.force_login(self.user_docente_autorizado)

        # Simular que la función de utilerías retorna bytes de PDF válidos
        mock_generar_pdf.return_value = b"%PDF-1.4 contenido_falso_del_acta"

        response = self.client.get(self.url_descarga)

        # Verificaciones del flujo binario
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')

        nombre_esperado = 'attachment; filename="acta_seminario_1_periodo_1_Vega.pdf"'
        self.assertEqual(response['Content-Disposition'], nombre_esperado)
        self.assertEqual(response.content,
                         b"%PDF-1.4 contenido_falso_del_acta")

    # ── CASO 2: SEGURIDAD / AISLAMIENTO DE DATOS (HTTP 404) ──
    def test_docente_no_perteneciente_al_comite_da_error_404(self):
        """Si un docente intenta descargar el acta de un alumno que no es suyo, lanza Http404."""
        self.client.force_login(self.user_docente_no_autorizado)

        response = self.client.get(self.url_descarga)
        self.assertEqual(response.status_code, 404)

    # ── CASO 3: ID INEXISTENTE (HTTP 404) ──
    def test_seminario_inexistente_da_error_404(self):
        """Si el seminario_id no existe en el sistema, get_object_or_404 arroja un 404 directo."""
        self.client.force_login(self.user_docente_autorizado)

        url_falsa = reverse('lumat_app:docente_descargar_acta',
                            kwargs={'seminario_id': 9999})
        response = self.client.get(url_falsa)

        self.assertEqual(response.status_code, 404)
