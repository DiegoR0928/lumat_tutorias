from django.test import TestCase
from django.contrib.auth.models import User
import datetime
from io import BytesIO
from lumat_app.models import Alumno, Docente, Comite, Seminario
from lumat_app.acta_generador import generar_acta_alumno


class ActaGeneratorTechnicalTest(TestCase):

    def setUp(self):
        # Crear la estructura de datos obligatoria para el acta
        self.user_alumno = User.objects.create_user(
            username='alumno_pdf', password='123')
        self.alumno = Alumno.objects.create(
            user=self.user_alumno, nombre="Ana", apellido_paterno="García",
            apellido_materno="Luna", matricula="87654321", semestre="2", correo="ana@lumat.edu"
        )

        user_t = User.objects.create_user(username='t_pdf')
        user_m1 = User.objects.create_user(username='m1_pdf')
        user_m2 = User.objects.create_user(username='m2_pdf')

        self.tutor = Docente.objects.create(
            user=user_t, nombre="T", apellido_paterno="P", correo="t@u")
        self.m1 = Docente.objects.create(
            user=user_m1, nombre="M1", apellido_paterno="A", correo="m1@u")
        self.m2 = Docente.objects.create(
            user=user_m2, nombre="M2", apellido_paterno="B", correo="m2@u")

        self.comite = Comite.objects.create(
            tutor=self.tutor, miembro1=self.m1, miembro2=self.m2)

        # La fecha del seminario define las etiquetas de semestre del encabezado del PDF
        self.seminario = Seminario.objects.create(
            alumno=self.alumno, comite=self.comite, numero=2,
            fecha=datetime.date(2026, 6, 1), hora=datetime.time(11, 0), calificacion=9.0
        )

        # Diccionario simulando el método .to_dict() de tu modelo ActaAlumnoData
        self.datos_form = {
            'actividad_principal': 'Desarrollo de simuladores cuánticos',
            'reuniones_tutor': 6, 'reuniones_comite': 2, 'coloquios': 2,
            'cursos': 'Física Estadística', 'articulos': 'Ninguno',
            'eventos': 'Congreso Nacional', 'plan_siguiente': 'Escritura',
            'comentarios': 'Ninguno'
        }

    def test_generar_pdf_retorna_buffer_valido(self):
        """Verifica que ReportLab compile el documento y retorne un flujo de bytes PDF válido."""
        resultado_buffer = generar_acta_alumno(
            seminario=self.seminario,
            alumno=self.alumno,
            comite=self.comite,
            datos_form=self.datos_form
        )

        # Validaciones de la respuesta técnica del generador
        self.assertIsInstance(resultado_buffer, BytesIO)

        pdf_bytes = resultado_buffer.read()
        self.assertTrue(len(pdf_bytes) > 0)

        # Todo archivo PDF válido debe iniciar con la cabecera estándar binaria %PDF
        self.assertTrue(pdf_bytes.startswith(b'%PDF'))
