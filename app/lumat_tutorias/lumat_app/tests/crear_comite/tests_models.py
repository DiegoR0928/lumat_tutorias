from django.test import TestCase
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.contrib.auth.models import User
from lumat_app.models import Docente, Comite
from django.core.files.uploadedfile import SimpleUploadedFile


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


class ComiteModelTestCase(TestCase):

    def setUp(self):
        # Usuarios obligatorios para relaciones OneToOne
        u_t = User.objects.create_user(
            username='tutor_str_test', password='pwd')
        u_m1 = User.objects.create_user(username='m1_str_test', password='pwd')
        u_m2 = User.objects.create_user(username='m2_str_test', password='pwd')

        # Firma dummie para pasar el ImageField obligatorio de Docente
        firma_mock = SimpleUploadedFile(
            name="firma.png",
            content=b"\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\x3b",
            content_type="image/png"
        )

        # Los tres docentes deben ser distintos para cumplir con Comite.clean()
        self.tutor = Docente.objects.create(
            user=u_t, nombre="Carlos", apellido_paterno="Lopez", firma=firma_mock)
        self.m1 = Docente.objects.create(
            user=u_m1, nombre="Maria", apellido_paterno="Gomez", firma=firma_mock)
        self.m2 = Docente.objects.create(
            user=u_m2, nombre="Jose", apellido_paterno="Sanz", firma=firma_mock)

    def test_comite_str_guardado_en_base_de_datos(self):
        """Verifica que el __str__ devuelva 'Comité <id>' si ya está persistido."""
        comite = Comite.objects.create(
            tutor=self.tutor, miembro1=self.m1, miembro2=self.m2)
        self.assertEqual(str(comite), f"Comité {comite.id}")

    def test_comite_str_nuevo_en_memoria(self):
        """
        CUBRE RAMA PARCIAL 61 ↛ 63: Si el id es None, el condicional da False
        y se obliga al flujo a retornar 'Comité Nuevo'.
        """
        comite_nuevo = Comite(
            tutor=self.tutor, miembro1=self.m1, miembro2=self.m2)
        self.assertIsNone(comite_nuevo.id)
        self.assertEqual(str(comite_nuevo), "Comité Nuevo")
