from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User, Group
import datetime
from datetime import time
from lumat_app.models import Alumno, Docente, Comite, Seminario


class GenerarActaRedireccionesTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.url = reverse('lumat_app:generar_acta', kwargs={'num': 1})
        self.url_detalle = reverse(
            'lumat_app:seminario_detalle', kwargs={'num': 1})

        # 1. Crear el grupo 'Alumno' requerido por tus validaciones y asignarlo
        self.grupo_alumno, _ = Group.objects.get_or_create(name='Alumno')

        self.user_alumno = User.objects.create_user(
            username='alumno_sga', password='password123')
        # <-- Crucial para simular el rol
        self.user_alumno.groups.add(self.grupo_alumno)

        # 2. Configurar el alumno con semestre='1' (por defecto en tu modelo)
        self.alumno = Alumno.objects.create(
            user=self.user_alumno, nombre="Luis", apellido_paterno="Vega",
            apellido_materno="Mora", matricula="12345", correo="luis@lumat.edu"
        )

        # 3. Crear docentes y comité
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

        # 4. Configurar el Seminario con numero=1 (para que machee con el semestre del alumno y no dé 404)
        self.seminario_incompleto = Seminario.objects.create(
            alumno=self.alumno,
            numero=1,             # <-- Debe coincidir con el num del request
            periodo=20261,
            calificacion=None,    # <-- Provoca que tu vista procesadora redirija al detalle
            comite=self.comite,
            fecha=datetime.date(2026, 6, 1),
            hora=time(10, 0)
        )

    def test_redireccion_automatica_valida_302_y_target_200(self):
        """assertRedirects comprueba internamente el 302 inicial y el 200 del destino."""
        self.client.force_login(self.user_alumno)

        payload = {'actividad_principal': 'Intento en seminario incompleto'}
        response = self.client.post(self.url, data=payload)

        # Al estar el grupo asignado y existir el seminario_detalle/1/, devolverá 200 éxito
        self.assertRedirects(response, self.url_detalle,
                             status_code=302, target_status_code=200)

    def test_verificacion_manual_de_estados_en_redireccion(self):
        """Prueba manual siguiendo la cadena de peticiones paso a paso sin seguir el redireccionamiento."""
        self.client.force_login(self.user_alumno)

        payload = {'actividad_principal': 'Intento en seminario incompleto'}
        response = self.client.post(self.url, data=payload, follow=False)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, self.url_detalle)

        # Comprobar la carga exitosa de la plantilla del detalle
        response_destino = self.client.get(response.url)
        self.assertEqual(response_destino.status_code, 200)
