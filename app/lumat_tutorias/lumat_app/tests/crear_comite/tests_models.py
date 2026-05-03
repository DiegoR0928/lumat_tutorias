from django.test import TestCase
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.contrib.auth.models import User
from lumat_app.models import Docente, Comite


class CrearComiteTestCase(TestCase):
    def setUp(self):
        # 1. Usuarios para probar permisos de creación
        self.superusuario = User.objects.create_superuser(
            username='admin', password='password123'
        )
        self.usuario_normal = User.objects.create_user(
            username='estudiante', password='password123'
        )

        # NUEVO: Creamos 3 usuarios base requeridos por la base de datos
        # para los docentes
        user_d1 = User.objects.create_user(
            username='docente_test1', password='123')
        user_d2 = User.objects.create_user(
            username='docente_test2', password='123')
        user_d3 = User.objects.create_user(
            username='docente_test3', password='123')

        # 2. Docentes necesarios para crear el comité asignando el campo
        # 'user'
        self.docente_a = Docente.objects.create(user=user_d1)
        self.docente_b = Docente.objects.create(user=user_d2)
        self.docente_c = Docente.objects.create(user=user_d3)

        # 3. URL de creación ajustada a tu aplicación lumat_app
        self.url_crear_comite = reverse('admin:lumat_app_comite_add')

    # --- PRUEBAS DE CREACIÓN A NIVEL MODELO (REGLAS DE NEGOCIO) ---

    def test_crear_comite_valido_exitoso(self):
        """Un comité con 3 docentes distintos debe crearse correctamente."""
        Comite.objects.create(
            tutor=self.docente_a,
            miembro1=self.docente_b,
            miembro2=self.docente_c
        )
        self.assertEqual(Comite.objects.count(), 1)

    def test_crear_comite_falla_por_docentes_repetidos(self):
        """No se debe permitir crear un comité si hay docentes duplicados en
        los roles."""
        comite = Comite(
            tutor=self.docente_a,
            miembro1=self.docente_a,  # Duplicado intencional
            miembro2=self.docente_b
        )
        # El método clean() debe interceptar la creación y lanzar el error
        with self.assertRaisesMessage(
            ValidationError,
            "Los tres docentes del comité deben ser distintos."
        ):
            comite.save()

        # Verificamos que efectivamente no se guardó nada en la BD
        self.assertEqual(Comite.objects.count(), 0)

    # --- PRUEBAS DE CREACIÓN A NIVEL VISTA (PERMISOS) ---

    def test_superusuario_puede_crear_comite(self):
        """El superusuario tiene permisos para enviar el formulario
        de creación."""
        self.client.login(username='admin', password='password123')

        datos = {
            'tutor': self.docente_a.id,
            'miembro1': self.docente_b.id,
            'miembro2': self.docente_c.id,
        }

        response = self.client.post(self.url_crear_comite, datos)

        # Redirección 302 indica creación exitosa en el admin
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Comite.objects.count(), 1)

    def test_usuario_normal_rechazado_al_crear_comite(self):
        """Un usuario sin privilegios no puede procesar la petición de
        creación."""
        self.client.login(username='estudiante', password='password123')

        datos = {
            'tutor': self.docente_a.id,
            'miembro1': self.docente_b.id,
            'miembro2': self.docente_c.id,
        }

        response = self.client.post(self.url_crear_comite, datos)

        # Redirige al login y la base de datos se mantiene en 0
        self.assertEqual(response.status_code, 302)
        self.assertIn('/admin/login/', response.url)
        self.assertEqual(Comite.objects.count(), 0)
