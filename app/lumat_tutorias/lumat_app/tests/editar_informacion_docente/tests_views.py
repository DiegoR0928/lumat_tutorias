import datetime
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.messages import get_messages
from django.core.files.uploadedfile import SimpleUploadedFile

from lumat_app.models import Docente
from lumat_app.forms import DocenteForm, PasswordChangeCustomForm


class PerfilDocenteFormulariosYVistasTestCase(TestCase):

    def setUp(self):
        """Configuración inicial compartida para formularios y pruebas de la vista."""
        self.client = Client()

        # URLs del ecosistema declaradas en tu urls.py
        self.url_perfil = reverse('lumat_app:perfil_docente')
        self.url_seminarios = reverse('lumat_app:docente_seminarios')

        # 1. Crear un usuario Docente con su perfil OneToOne vinculado correctamente
        # IMPORTANTE: Guardamos la contraseña como 'password123' para usarla en el test de fallo
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

        # 2. Crear un usuario sin perfil docente asociado (para restricciones)
        self.user_sin_perfil = User.objects.create_user(
            username='externo_sga',
            password='password123'
        )

        # 3. Crear una firma reutilizable en bytes transparentes para validaciones
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

    # ── SECTION 1: PRUEBAS UNITARIAS DE FORMULARIOS ──

    def test_formulario_docente_datos_validos(self):
        """El formulario es válido si cuenta con datos correctos y la firma simulada."""
        datos = {
            'nombre': 'María',
            'apellido_paterno': 'Espinoza',
            'apellido_materno': 'Sanz',
            'correo': 'maria@lumat.edu'
        }
        form = DocenteForm(data=datos, files={'firma': self.imagen_simulada})
        self.assertTrue(form.is_valid())

    def test_inyeccion_clase_css_campos_password(self):
        """El constructor personalizado debe agregar 'alumno-input' a todos los widgets."""
        form = PasswordChangeCustomForm(user=self.user_docente)
        for field in form.fields.values():
            self.assertEqual(field.widget.attrs.get('class'), 'alumno-input')

    # ── SECTION 2: PRUEBAS DE AUTENTICACIÓN Y SEGURIDAD DE LA VISTA ──

    def test_usuario_anonimo_es_redirigido_a_login(self):
        """Un usuario sin sesión activa es rebotado (Redirección HTTP 302)."""
        response = self.client.get(self.url_perfil)
        self.assertEqual(response.status_code, 302)

    def test_usuario_sin_perfil_docente_redirige_a_seminarios(self):
        """Si un usuario no cuenta con el perfil Docente ligado, lanza error y lo redirige."""
        self.client.force_login(self.user_sin_perfil)
        response = self.client.get(self.url_perfil, follow=False)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, self.url_seminarios)

        mensajes = list(get_messages(response.wsgi_request))
        self.assertEqual(
            str(mensajes[0]), "No tienes un perfil de docente asignado.")

    # ── SECTION 3: PRUEBAS DE PETICIONES GET ──

    def test_get_perfil_exitoso_codigo_200(self):
        """Un GET correcto renderiza el formulario de perfil docente por defecto (editando = None)."""
        self.client.force_login(self.user_docente)
        response = self.client.get(self.url_perfil)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'docente_perfil.html')
        self.assertEqual(response.context['docente'], self.docente)
        self.assertIsNone(response.context['editando'])

    def test_get_perfil_captura_modo_edicion_codigo_200(self):
        """Verifica que el parámetro 'modo' por URL inicialice correctamente el contexto en modo perfil."""
        self.client.force_login(self.user_docente)
        response = self.client.get(self.url_perfil + '?modo=perfil')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['editando'], 'perfil')

    # ── SECTION 4: PRUEBAS DE PETICIONES POST ──

    def test_post_actualizar_perfil_exitoso_con_redireccion(self):
        """Un envío válido de datos personales persiste los cambios en la BD y redirige."""
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

        self.assertRedirects(response, self.url_perfil,
                             status_code=302, target_status_code=200)

        # Confirmar persistencia e integridad de datos en el motor SQL
        self.docente.refresh_from_db()
        self.assertEqual(self.docente.nombre, 'Juan Modificado')

        mensajes = list(get_messages(response.wsgi_request))
        self.assertEqual(
            str(mensajes[0]), "Información personal actualizada correctamente.")

    def test_post_actualizar_perfil_fallido_mantiene_modo_edicion(self):
        """Un envío de perfil incompleto recarga la pantalla en modo perfil con errores (HTTP 200)."""
        self.client.force_login(self.user_docente)

        payload = {
            'accion': 'perfil',
            'nombre': '',  # Inválido: campo requerido vacío
            'correo': 'correo_sin_formato_correcto'
        }
        response = self.client.post(self.url_perfil, data=payload)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['editando'], 'perfil')
        self.assertFalse(response.context['docente_form'].is_valid())

    def test_post_cambiar_password_exitoso_con_redireccion(self):
        """Un cambio de contraseña válido actualiza credenciales de sesión y redirige."""
        self.client.force_login(self.user_docente)

        payload = {
            'accion': 'password',
            'old_password': 'password123',
            'new_password1': 'nueva_clave_2026',
            'new_password2': 'nueva_clave_2026'
        }
        response = self.client.post(self.url_perfil, data=payload)

        self.assertRedirects(response, self.url_perfil,
                             status_code=302, target_status_code=200)

        mensajes = list(get_messages(response.wsgi_request))
        self.assertEqual(str(mensajes[0]), "Contraseña actualizada con éxito.")

    # ── PRUEBA SOLUCIÓN DEFINITIVA A LA RAMA PARCIAL (55 ↛ 72) ──
    def test_post_cambiar_password_fallido_mantiene_modo_edicion_password(self):
        """
        Envía la contraseña actual correcta para pasar el primer filtro de Django,
        pero envía contraseñas nuevas discrepantes para forzar el else del is_valid.
        """
        self.client.force_login(self.user_docente)

        # En Django, PasswordChangeForm mapea sus campos como:
        # 'old_password', 'new_password1' y 'new_password2'
        payload = {
            'accion': 'password',
            'old_password': 'password123',               # Contraseña del setUp correcta
            'new_password1': 'ContrasenaSeguraNueva123',
            # Provoca el error de coincidencia
            'new_password2': 'UnaCompletamenteDiferente456'
        }
        response = self.client.post(self.url_perfil, data=payload)

        # 1. Al fallar la validación de coincidencia, no redirige, devuelve HTTP 200
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'docente_perfil.html')

        # 2. COMPROBACIÓN EXIGIDA POR COVERAGE: Entra a la línea 72 e inyecta 'password'
        self.assertEqual(response.context['editando'], 'password')

        # 3. Validar que el formulario capturó los errores de validación nativos
        self.assertFalse(response.context['password_form'].is_valid())

    # ── PRUEBA SOLUCIÓN DEFINITIVA A LA RAMA PARCIAL (55 ↛ 72) ──
    def test_post_cambiar_password_fallido_mantiene_modo_edicion_password(self):
        """
        Envía contraseñas que cumplen perfectamente con los validadores de settings.py
        (usando el mismo formato del test de éxito), pero alterando el segundo campo
        para forzar que is_valid() sea False y ejecute el bloque else (línea 72).
        """
        self.client.force_login(self.user_docente)

        # Usamos exactamente la misma estructura de claves que tu test de éxito,
        # pero cambiamos el último carácter de 'new_password2' para romper la coincidencia.
        payload = {
            'accion': 'password',
            'old_password': 'password123',  # Contraseña correcta asignada en el setUp
            'new_password1': 'nueva_clave_2026',
            'new_password2': 'nueva_clave_2026_ERROR'  # <-- Mismo formato, pero no coincide
        }
        response = self.client.post(self.url_perfil, data=payload)

        # 1. Al fallar la coincidencia, la vista no redirige, renderiza con un código HTTP 200
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'docente_perfil.html')

        # 2. VALIDACIÓN EXIGIDA POR COVERAGE: El flujo entró al 'else' e inyectó 'password'
        self.assertEqual(response.context['editando'], 'password')

        # 3. Validar que el formulario capturó los errores de discrepancia de contraseñas
        self.assertFalse(response.context['password_form'].is_valid())

        # Opcional: Verificamos que el error sea explícitamente por no coincidir y no por contraseña incorrecta
        self.assertIn('password_mismatch',
                      response.context['password_form'].errors.get('__all__', []))

# ── PRUEBA SOLUCIÓN ABSOLUTA A LA RAMA PARCIAL (55 ↛ 72) ──
    def test_post_cambiar_password_fallido_mantiene_modo_edicion_password(self):
        """
        Obliga a la vista a ejecutar el bloque else de la línea 72, 
        verificando la consistencia e integridad de todas las variables 
        del contexto de renderizado posterior.
        """
        self.client.force_login(self.user_docente)

        # Enviamos un payload idéntico en formato al de éxito para saltar validadores de settings,
        # pero alterando deliberadamente el campo final de confirmación.
        payload = {
            'accion': 'password',
            'old_password': 'password123',  # Contraseña correcta mapeada en el setUp
            'new_password1': 'nueva_clave_2026',
            'new_password2': 'nueva_clave_2026_DISCREPANTE'  # Forzar el password_mismatch
        }
        response = self.client.post(self.url_perfil, data=payload)

        # 1. Comprobar que la validación falló y la vista volvió a pintar el template (HTTP 200)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'docente_perfil.html')

        # 2. VALIDACIÓN EXIGIDA POR COVERAGE: El flujo pisó la línea 72 e inyectó 'password'
        self.assertEqual(response.context['editando'], 'password')

        # 3. COMPROBACIÓN DE CONTROL DE BIFURCACIÓN: Asegurar que password_form no es válido
        self.assertFalse(response.context['password_form'].is_valid())

        # 4. ALINEACIÓN DE RAMAS PARCIALES: Validar que docente_form se instanció de forma
        # segura y limpia en la línea 55 para acompañar el contexto de la respuesta sin colapsar
        self.assertIn('docente_form', response.context)
        self.assertEqual(
            response.context['docente_form'].instance, self.docente)
