from behave import given, when, then
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


# ---------------------------------------------------------------------------
# Givens
# ---------------------------------------------------------------------------

@given(u'que estoy en la página de registro de alumno')
def step_impl(context):
    context.driver = webdriver.Chrome()
    context.driver.get('http://localhost:8000/registro/')


@given(u'el usuario "{username}" ya existe en el sistema')
def step_impl(context, username):
    """
    Crea el usuario llenando el formulario con un username distinto al del
    escenario real, para evitar conflictos entre escenarios.
    """
    driver = context.driver
    wait = WebDriverWait(driver, 10)

    driver.get('http://localhost:8000/registro/')

    wait.until(EC.presence_of_element_located(
        (By.NAME, 'username'))).send_keys(username)
    driver.find_element(By.NAME, 'email').send_keys('previo@escuela.mx')
    driver.find_element(By.NAME, 'password').send_keys('Temporal#123')
    driver.find_element(By.NAME, 'nombre').send_keys('Previo')
    driver.find_element(By.NAME, 'apellido_paterno').send_keys('Previo')
    driver.find_element(By.NAME, 'apellido_materno').send_keys('Previo')
    driver.find_element(By.CSS_SELECTOR, '.btn-guardar').click()

    # Esperamos el mensaje de éxito para confirmar que se creó correctamente
    try:
        wait.until(
            EC.visibility_of_element_located(
                (By.CLASS_NAME, 'alert-success-custom'))
        )
    except Exception:
        raise AssertionError(
            f"No se pudo crear el usuario previo '{username}'. "
            "Verifica que el servidor esté corriendo y el username no exista ya."
        )

    # Regresamos a la página de registro limpia para el escenario real
    driver.get('http://localhost:8000/registro/')
    wait.until(EC.presence_of_element_located((By.NAME, 'username')))


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

@then(u'debo ver el mensaje "Alumno registrado con éxito"')
def step_impl(context):
    wait = WebDriverWait(context.driver, 10)
    mensaje = wait.until(
        EC.visibility_of_element_located(
            (By.CLASS_NAME, 'alert-success-custom'))
    )
    assert 'Alumno registrado con éxito' in mensaje.text, (
        f"Mensaje esperado no encontrado. Texto visible: '{mensaje.text}'"
    )


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
    # Damos un momento al DOM para estabilizarse
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
