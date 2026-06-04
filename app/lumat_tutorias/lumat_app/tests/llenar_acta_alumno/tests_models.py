import datetime
from django.test import TestCase
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile

from lumat_app.models import Alumno, Docente, Comite, Seminario, ActaAlumnoData


class ActaAlumnoDataModelTestCase(TestCase):

    def setUp(self):
        # 1. Configurar los usuarios base necesarios para las relaciones OneToOne
        u_a = User.objects.create_user(
            username='alumno_actadata_test', password='pwd')
        u_t = User.objects.create_user(
            username='tutor_actadata_test', password='pwd')
        u_m1 = User.objects.create_user(
            username='m1_actadata_test', password='pwd')
        u_m2 = User.objects.create_user(
            username='m2_actadata_test', password='pwd')

        # Firma dummy obligatoria para cumplir con las restricciones del modelo Docente
        firma_mock = SimpleUploadedFile(
            name="firma.png",
            content=b"\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\x3b",
            content_type="image/png"
        )

        # 2. Instanciar Alumno y Docentes con sínodos únicos (para pasar Comite.clean())
        self.alumno = Alumno.objects.create(
            user=u_a, nombre="Luis", apellido_paterno="Vega", matricula="ACTADATA01"
        )
        tutor = Docente.objects.create(
            user=u_t, nombre="Carlos", apellido_paterno="Lopez", firma=firma_mock)
        m1 = Docente.objects.create(
            user=u_m1, nombre="Maria", apellido_paterno="Gomez", firma=firma_mock)
        m2 = Docente.objects.create(
            user=u_m2, nombre="Jose", apellido_paterno="Sanz", firma=firma_mock)

        comite = Comite.objects.create(tutor=tutor, miembro1=m1, miembro2=m2)

        # 3. Crear el Seminario correspondiente
        self.seminario = Seminario.objects.create(
            alumno=self.alumno,
            comite=comite,
            numero=1,
            periodo=1,
            fecha=datetime.date.today(),
            hora=datetime.time(10, 0)
        )

    def test_acta_alumno_data_str_retorna_formato_correcto(self):
        """Verifica que el método __str__ ensamble correctamente el prefijo junto al string del seminario."""
        acta_data = ActaAlumnoData.objects.create(
            seminario=self.seminario,
            actividad_principal="Desarrollo de un Simulador Interactivo de Física",
            reuniones_tutor=5,
            reuniones_comite=2,
            coloquios=1,
            plan_siguiente="Escritura de conclusiones finales",
            comentarios="Progreso óptimo en el ciclo."
        )

        # La cadena esperada debe unirse utilizando la representación del seminario asociada
        expected_str = f"Acta — {self.seminario}"

        # Validamos que coincida perfectamente al 100%
        self.assertEqual(str(acta_data), expected_str)
