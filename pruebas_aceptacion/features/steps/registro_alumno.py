from behave import given, when, then
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


# ---------------------------------------------------------------------------
# Givens
# ---------------------------------------------------------------------------

@given(u'que estoy en la página de registro de alumno')
def step_impl(context):
    context.driver.get('http://app:8000/registro/')


@given(u'el usuario "{username}" ya existe en el sistema')
def step_impl(context, username):
    """
    Crea el usuario directamente en BD, sin usar el navegador.
    Más rápido y no depende del comportamiento del formulario.
    """
    from django.contrib.auth.models import User
    from lumat_app.models import Alumno

    user = User.objects.create_user(
        username=username,
        password='Temporal#123',
        email='previo@escuela.mx'
    )
    Alumno.objects.create(
        user=user,
        nombre='Previo',
        apellido_paterno='Previo',
        apellido_materno='Previo',
    )

    # Dejamos el navegador en la página de registro lista para el escenario
    context.driver.get('http://app:8000/registro/')
    WebDriverWait(context.driver, 10).until(
        EC.presence_of_element_located((By.NAME, 'username'))
    )


# ---------------------------------------------------------------------------
# Whens
# ---------------------------------------------------------------------------

@when(u'ingreso "{valor}" en el campo "usuario"')
def step_impl(context, valor):
    wait = WebDriverWait(context.driver, 10)
    campo = wait.until(EC.presence_of_element_located((By.NAME, 'username')))
    campo.clear()
    campo.send_keys(valor)


@when(u'ingreso "{valor}" en el campo "email"')
def step_impl(context, valor):
    campo = context.driver.find_element(By.NAME, 'email')
    campo.clear()
    campo.send_keys(valor)


@when(u'ingreso "{valor}" en el campo "contraseña"')
def step_impl(context, valor):
    campo = context.driver.find_element(By.NAME, 'password')
    campo.clear()
    campo.send_keys(valor)


@when(u'ingreso "{valor}" en el campo "nombre"')
def step_impl(context, valor):
    campo = context.driver.find_element(By.NAME, 'nombre')
    campo.clear()
    campo.send_keys(valor)


@when(u'ingreso "{valor}" en el campo "apellido paterno"')
def step_impl(context, valor):
    campo = context.driver.find_element(By.NAME, 'apellido_paterno')
    campo.clear()
    campo.send_keys(valor)


@when(u'ingreso "{valor}" en el campo "apellido materno"')
def step_impl(context, valor):
    campo = context.driver.find_element(By.NAME, 'apellido_materno')
    campo.clear()
    campo.send_keys(valor)


@when(u'hago clic en el botón "Guardar"')
def step_impl(context):
    context.driver.find_element(By.CSS_SELECTOR, '.btn-guardar').click()


# ---------------------------------------------------------------------------
# Thens
# ---------------------------------------------------------------------------

@then(u'debo ser redirigido al login')
def step_impl(context):
    wait = WebDriverWait(context.driver, 10)
    wait.until(lambda d: 'login' in d.current_url)
    assert 'login' in context.driver.current_url


@then(u'el formulario debe mostrarse vacío nuevamente')
def step_impl(context):
    wait = WebDriverWait(context.driver, 10)
    campo = wait.until(EC.presence_of_element_located((By.NAME, 'username')))
    valor = campo.get_attribute('value')
    assert valor == '', (
        f"El campo usuario no está vacío, contiene: '{valor}'"
    )


@then(u'no debo ver el mensaje "Alumno registrado con éxito"')
def step_impl(context):
    import time
    time.sleep(1)
    elementos = context.driver.find_elements(
        By.CLASS_NAME, 'alert-success-custom')
    assert len(elementos) == 0, (
        "Se encontró el mensaje de éxito cuando no debería aparecer."
    )


@then(u'debo ver un error en el campo "usuario"')
def step_impl(context):
    wait = WebDriverWait(context.driver, 10)

    # Buscamos todos los field-error y filtramos el que tiene texto
    errores = wait.until(
        EC.presence_of_all_elements_located((By.CLASS_NAME, 'field-error'))
    )
    textos = [e.text.strip() for e in errores if e.text.strip() != '']

    assert len(textos) > 0, (
        "No se encontró ningún mensaje de error visible en el formulario."
    )
