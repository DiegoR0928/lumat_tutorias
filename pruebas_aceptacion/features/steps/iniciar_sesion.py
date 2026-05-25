from behave import when, then, given
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import urllib.request


@given(u'que ingreso en el sistema de tutorias')
def step_impl(context):
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')

    context.driver = webdriver.Remote(
        command_executor='http://selenium-hub:4444/wd/hub',
        options=options
    )

    # Espera hasta 30s a que Django esté respondiendo antes de navegar
    for _ in range(30):
        try:
            urllib.request.urlopen('http://app:8000/login/')
            break
        except Exception:
            time.sleep(1)

    context.driver.get('http://app:8000/login/')


@given(u'escribo mi usuario "{usuario}"')
def step_impl(context, usuario):
    wait = WebDriverWait(context.driver, 10)
    campo_usuario = wait.until(
        EC.presence_of_element_located((By.ID, 'id_usuario'))
    )
    campo_usuario.send_keys(usuario)


@given(u'escribo la contraseña "{contraseña}"')
def step_impl(context, contraseña):
    wait = WebDriverWait(context.driver, 10)
    campo_pass = wait.until(
        EC.presence_of_element_located((By.ID, 'id_contrasena'))
    )
    campo_pass.send_keys(contraseña)


@when(u'presiono el botón "Entrar"')
def step_impl(context):
    wait = WebDriverWait(context.driver, 10)
    boton = wait.until(
        EC.element_to_be_clickable((By.ID, 'btn_login'))
    )
    boton.click()


@then(u'puedo ver la sección "" del sistema')
def step_impl(context):
    # Valida que después del login exitoso ya no estamos en /login/
    wait = WebDriverWait(context.driver, 10)
    wait.until(lambda d: '/login/' not in d.current_url)
    assert '/login/' not in context.driver.current_url


@then(
    u'puedo ver un mensaje de error indicando que las credenciales '
    u'son incorrectas'
)
def step_impl(context):
    wait = WebDriverWait(context.driver, 10)
    error = wait.until(
        EC.visibility_of_element_located((By.CLASS_NAME, 'alert-danger'))
    )
    assert 'Credenciales inválidas' in error.text