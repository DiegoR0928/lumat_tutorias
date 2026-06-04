# features/steps/iniciar_sesion.py

import os
from behave import given, when, then
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Uso del ecosistema Django para inyectar los datos requeridos por la prueba
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from lumat_app.models import Alumno

User = get_user_model()
BASE_URL = "http://app:8000"


@given('que ingreso en el sistema de tutorias')
def step_impl(context):
    # 1. Asegurar la infraestructura relacional del usuario en la base de datos de pruebas
    grupo_alumno, _ = Group.objects.get_or_create(name='Alumno')
    user_obj, _ = User.objects.get_or_create(username='amer')
    user_obj.set_password('amer1234')  # Contraseña requerida por el escenario exitoso
    user_obj.groups.add(grupo_alumno)
    user_obj.save()

    # Crear el perfil OneToOne de Alumno requerido por la redirección de CustomLoginView
    Alumno.objects.get_or_create(
        user=user_obj,
        defaults={
            'nombre': 'Amer',
            'apellido_paterno': 'Inaga',
            'matricula': '123456',
            'semestre': '4',
            'correo': 'amer@lumat.edu'
        }
    )

    # 2. Navegar a la página por UI
    context.driver.get(f'{BASE_URL}/login/')


@given('escribo mi usuario "{usuario}"')
def step_impl(context, usuario):
    # Usamos WebDriverWait preventivo para asegurar la renderización en headless chrome
    WebDriverWait(context.driver, 10).until(
        EC.presence_of_element_located((By.ID, 'id_usuario'))
    ).send_keys(usuario)


@given('escribo la contraseña "{contrasena}"')
def step_impl(context, contrasena):
    context.driver.find_element(By.ID, 'id_contrasena').send_keys(contrasena)


@when('presiono el botón "Entrar"')
def step_impl(context):
    boton = context.driver.find_element(By.ID, 'btn_login')
    # Usamos JS click para prevenir cualquier ElementClickInterceptedException por overlays
    context.driver.execute_script("arguments[0].click();", boton)


@then('puedo ver un mensaje de error indicando que las credenciales son incorrectas')
def step_impl(context):
    wait = WebDriverWait(context.driver, 10)
    
    # Se adapta para soportar tanto componentes alert de Bootstrap como textos del body
    error = wait.until(
        EC.visibility_of_element_located((By.TAG_NAME, "body"))
    )
    
    # Soporta variaciones del string del backend ("Credenciales inválidas" o "incorrectas")
    assert any(msg in error.text for msg in ["invalid", "inválidas", "incorrectas", "Error"]), \
        "No se visualizó el mensaje de error de autenticación en la UI."


@then(u'puedo ver la sección "{seccion}" del sistema')
def step_impl(context, seccion):
    # Espera óptima y asíncrona a que ocurra el cambio de URL del backend
    WebDriverWait(context.driver, 10).until(
        lambda d: '/login/' not in d.current_url
    )

    url = context.driver.current_url

    if seccion.lower() == 'docente':
        assert '/docente/' in url, f"Se esperaba la ruta de docente, pero se obtuvo: {url}"

    elif seccion.lower() == 'alumno':
        # Se adapta al comportamiento dinámico del LoginView de tu sistema
        assert '/alumno/' in url, f"Se esperaba la redirección académica del alumno, pero se obtuvo: {url}"

    else:
        raise AssertionError(f'Sección no soportada en la automatización: {seccion}')