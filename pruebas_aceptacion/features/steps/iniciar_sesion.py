from behave import given, when, then
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


@given('que ingreso en el sistema de tutorias')
def step_impl(context):
    context.driver.get('http://app:8000/login/')


@given('escribo mi usuario "{usuario}"')
def step_impl(context, usuario):
    context.driver.find_element(
        By.ID,
        'id_usuario'
    ).send_keys(usuario)


@given('escribo la contraseña "{contrasena}"')
def step_impl(context, contrasena):
    context.driver.find_element(
        By.ID,
        'id_contrasena'
    ).send_keys(contrasena)


@when('presiono el botón "Entrar"')
def step_impl(context):
    context.driver.find_element(
        By.ID,
        'btn_login'
    ).click()


# @then('puedo ver la sección "{seccion}" del sistema')
# def step_impl(context, seccion):
#     wait = WebDriverWait(context.driver, 10)

#     wait.until(
#         EC.presence_of_element_located((By.TAG_NAME, "body"))
#     )

#     assert seccion in context.driver.page_source


@then(
    'puedo ver un mensaje de error indicando que las credenciales '
    'son incorrectas'
)
def step_impl(context):
    wait = WebDriverWait(context.driver, 10)

    error = wait.until(
        EC.visibility_of_element_located(
            (By.CLASS_NAME, "alert-danger")
        )
    )

    assert "Credenciales inválidas" in error.text


@then(u'puedo ver la sección "{seccion}" del sistema')
def step_impl(context, seccion):

    WebDriverWait(context.driver, 10).until(
        lambda d: '/login/' not in d.current_url
    )

    url = context.driver.current_url

    if seccion.lower() == 'docente':
        assert '/docente/' in url

    elif seccion.lower() == 'alumno':
        assert '/alumno/seminario/' in url

    else:
        raise AssertionError(
            f'Sección no soportada: {seccion}'
        )
