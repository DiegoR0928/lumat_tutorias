from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.messages import get_messages
from django.core.files.uploadedfile import SimpleUploadedFile

# Asegúrate de importar tus modelos correctamente desde tu aplicación
from lumat_app.models import Docente


class EditarPerfilDocenteViewSimpleTest(TestCase):

    def setUp(self):
        """Configuración inicial para las pruebas de la vista de perfil docente."""
        self.client = Client()

        # Declaración exacta de las URLs de tu aplicación basadas en tu urls.py
        self.url_perfil = reverse('lumat_app:perfil_docente')
        self.url_seminarios = reverse('lumat_app:docente_seminarios')

        # 1. Crear un usuario Docente con su perfil OneToOne vinculado correctamente
        self.user_docente = User.objects.create_user(
            username='docente_sga',
            password='password123'
        )
        self.docente = Docente.objects.create(
            user=self.user_docente,
            nombre="Juan",
            apellido_paterno="Pérez",
            apellido_materno="López",
            correo="juan@lumat.edu"
        )

        # 2. Crear un usuario sin perfil docente asociado (para probar restricciones)
        self.user_sin_perfil = User.objects.create_user(
            username='externo_sga',
            password='password123'
        )

        # 3. Crear una firma en bytes falsa reutilizable para peticiones POST válidas
        self.imagen_simulada = SimpleUploadedFile(
            name="firma_docente.png",
            content=(
                b"\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00"
                b"\x00\x00\x00\xff\xff\xff\x21\xf9\x04\x01\x00\x00\x00"
                b"\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02"
                b"\x4c\x01\x00\x3b"
            ),
            content_type="image/png",
        )

    # ── 1. PRUEBAS DE AUTENTICACIÓN Y ROLES ──

    def test_usuario_anonimo_es_redirigido_a_login(self):
        """Un usuario sin sesión activa es rebotado (Redirección HTTP 302)."""
        response = self.client.get(self.url_perfil)
        self.assertEqual(response.status_code, 302)

    def test_usuario_sin_perfil_docente_redirige_a_seminarios_200(self):
        """Si un usuario no tiene el modelo Docente, lanza un mensaje de error y redirige."""
        self.client.force_login(self.user_sin_perfil)

        # Evitamos usar follow=True para no requerir permisos en la vista destino
        response = self.client.get(self.url_perfil, follow=False)

        # Valida que la redirección inicial apunta correctamente a los seminarios
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, self.url_seminarios)

        # Comprobar la inyección de la alerta de Django Messages en la sesión
        mensajes = list(get_messages(response.wsgi_request))
        self.assertEqual(
            str(mensajes[0]), "No tienes un perfil de docente asignado.")

    # ── 2. PRUEBAS DE PETICIONES GET ──

    def test_get_perfil_exitoso_codigo_200(self):
        """Un GET correcto renderiza el template con código 200 y variables nulas."""
        self.client.force_login(self.user_docente)
        response = self.client.get(self.url_perfil)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'docente_perfil.html')
        self.assertEqual(response.context['docente'], self.docente)
        self.assertIsNone(response.context['editando'])

    def test_get_perfil_captura_modo_edicion_codigo_200(self):
        """Verifica que el parámetro 'modo' de la URL inicialice la variable editando."""
        self.client.force_login(self.user_docente)
        response = self.client.get(self.url_perfil + '?modo=perfil')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['editando'], 'perfil')

    # ── 3. PRUEBAS DE PETICIONES POST (CRUD) ──

    def test_post_actualizar_perfil_exitoso_con_redireccion_200(self):
        """Un envío válido actualiza la BD y la redirección al perfil finaliza con 200."""
        self.client.force_login(self.user_docente)

        payload = {
            'accion': 'perfil',
            'nombre': 'Juan Modificado',
            'apellido_paterno': 'Pérez',
            'apellido_materno': 'López',
            'correo': 'juan_nuevo@lumat.edu',
            'firma': self.imagen_simulada
        }
        response = self.client.post(self.url_perfil, data=payload)

        # Valida que redirige a sí misma (302) y que el destino final responda exitosamente (200)
        self.assertRedirects(response, self.url_perfil,
                             status_code=302, target_status_code=200)

        # Sincronizar el objeto físico en la BD de pruebas para asegurar consistencia
        self.docente.refresh_from_db()
        self.assertEqual(self.docente.nombre, 'Juan Modificado')

        mensajes = list(get_messages(response.wsgi_request))
        self.assertEqual(
            str(mensajes[0]), "Información personal actualizada correctamente.")

    def test_post_actualizar_perfil_fallido_mantiene_modo_edicion_200(self):
        """Un envío incompleto no procesa cambios y recarga la misma página con errores (200)."""
        self.client.force_login(self.user_docente)

        payload = {
            'accion': 'perfil',
            'nombre': '',  # Inválido: campo obligatorio vacío
            'correo': 'correo_malo_sin_formato'
        }
        response = self.client.post(self.url_perfil, data=payload)

        # Al no redirigir, la respuesta directa debe devolver HTTP 200
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['editando'], 'perfil')
        self.assertFalse(response.context['docente_form'].is_valid())

    def test_post_cambiar_password_exitoso_con_redireccion_200(self):
        """Un cambio de contraseña válido actualiza al usuario y la redirección responde con 200."""
        self.client.force_login(self.user_docente)

        payload = {
            'accion': 'password',
            'old_password': 'password123',
            'new_password1': 'nueva_clave_2026',
            'new_password2': 'nueva_clave_2026'
        }
        response = self.client.post(self.url_perfil, data=payload)

        # Verifica la redirección (302) y que la página destino responda exitosamente (200)
        self.assertRedirects(response, self.url_perfil,
                             status_code=302, target_status_code=200)

        # Verificar que el mensaje de éxito se haya guardado
        mensajes = list(get_messages(response.wsgi_request))
        self.assertEqual(str(mensajes[0]), "Contraseña actualizada con éxito.")

    def test_post_cambiar_password_fallido_mantiene_modo_edicion_200(self):
        """
        Un cambio de contraseña inválido (no coinciden) recarga la página
        con código 200 en modo password.
        """
        self.client.force_login(self.user_docente)

        payload = {
            'accion': 'password',
            'old_password': 'password123',
            'new_password1': 'clave_nueva_1',
            'new_password2': 'clave_diferente_2'  # <-- Provoca el fallo de validación
        }
        response = self.client.post(self.url_perfil, data=payload)

        # Al fallar, la vista no redirige sino que vuelve a renderizar el formulario (HTTP 200)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['editando'], 'password')

        # Aseguramos que el formulario de contraseñas tiene errores internos
        self.assertFalse(response.context['password_form'].is_valid())
