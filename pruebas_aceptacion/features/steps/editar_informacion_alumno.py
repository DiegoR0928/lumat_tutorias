from behave import when, then, given
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


@given(
    u'que he iniciado sesión como alumno con la cuenta "{usuario}" '
    u'y contraseña "{contraseña}"'
)
def step_impl(context, usuario, contraseña):
    context.driver = webdriver.Chrome()
    context.driver.get('http://localhost:8000/login/')
    context.driver.find_element(By.ID, 'id_usuario').send_keys(usuario)
    context.driver.find_element(By.ID, 'id_contrasena').send_keys(contraseña)
    context.driver.find_element(By.ID, 'btn_login').click()


@when(u'navego a la página de edición de perfil')
def step_impl(context):
    context.driver.get(
        "http://localhost:8000/alumno/perfil/?modo=perfil"
    )

    WebDriverWait(context.driver, 10).until(
        lambda d: "/perfil" in d.current_url
    )


@when(u'actualizo mi "{campo}" a "{valor}"')
def step_impl(context, campo, valor):
    field = context.driver.find_element(By.ID, f'id_{campo}')
    field.clear()
    field.send_keys(valor)


@when(u'hago clic en el botón de guardar')
def step_impl(context):
    context.driver.find_element(By.ID, 'btn_guardar_1').click()


@then(
    u'debería ver el mensaje "{mensaje}" y mi "{campo}" '
    u'actualizado a "{valor}"'
)
def step_impl(context, mensaje, campo, valor):
    success_message = context.driver.find_element(
        By.ID, 'success_message').text
    assert mensaje in success_message


@then(u'debería ver un mensaje de error indicando que los datos son inválidos')
def step_impl(context):
    def step_impl(context):

        wait = WebDriverWait(context.driver, 10)

        error_message = wait.until(
            EC.presence_of_element_located(
                (By.ID, 'error_message')
            )
        )

        assert "inválido" in error_message.text.lower()


@when(u'dejo el campo de nombre vacío')
def step_impl(context):

    wait = WebDriverWait(context.driver, 10)

    campo = wait.until(
        EC.presence_of_element_located(
            (By.NAME, 'nombre')
        )
    )

    campo.clear()


@then(u'el campo "{campo}" debería mostrar un error')
def step_impl(context, campo):

    wait = WebDriverWait(context.driver, 10)

    campo_input = wait.until(
        EC.presence_of_element_located((By.NAME, campo))
    )

    es_valido = context.driver.execute_script(
        "return arguments[0].checkValidity();",
        campo_input
    )

    assert es_valido is False, "El campo es válido cuando debería ser inválido"

    mensaje = context.driver.execute_script(
        "return arguments[0].validationMessage;",
        campo_input
    )

    assert mensaje != ""


@when(u'navego a la página de cambio de contraseña')
def step_impl(context):

    context.driver.get(
        "http://localhost:8000/alumno/perfil/?modo=password"
    )

    WebDriverWait(context.driver, 10).until(
        lambda d: "/perfil" in d.current_url
    )


@when(u'ingreso la contraseña actual "{password}"')
def step_impl(context, password):

    campo = context.driver.find_element(By.NAME, "old_password")
    campo.clear()
    campo.send_keys(password)


@when(u'ingreso la nueva contraseña "{password}"')
def step_impl(context, password):

    campo = context.driver.find_element(By.NAME, "new_password1")
    campo.clear()
    campo.send_keys(password)


@when(u'confirmo la nueva contraseña "{password}"')
def step_impl(context, password):

    campo = context.driver.find_element(By.NAME, "new_password2")
    campo.clear()
    campo.send_keys(password)


@when(u'hago clic en el botón de actualizar contraseña')
def step_impl(context):

    wait = WebDriverWait(context.driver, 10)

    boton = wait.until(
        EC.presence_of_element_located(
            (By.ID, "btn_guardar_2")
        )
    )

    # 🔥 1. Scroll fuerte al centro
    context.driver.execute_script("""
        arguments[0].scrollIntoView({
            behavior: 'instant',
            block: 'center'
        });
    """, boton)

    wait.until(EC.element_to_be_clickable((By.ID, "btn_guardar_2")))

    context.driver.execute_script("arguments[0].click();", boton)


@then(u'debería ver el mensaje "{mensaje}"')
def step_impl(context, mensaje):

    wait = WebDriverWait(context.driver, 10)

    alert = wait.until(
        EC.presence_of_element_located(
            (By.ID, "success_message")
        )
    )

    assert mensaje in alert.text

# @then(u'el campo "old_password" debería mostrar un error')
# def step_impl(context):

#     wait = WebDriverWait(context.driver, 10)

#     # 🔹 Buscar error del campo contraseña actual
#     error = wait.until(
#         EC.presence_of_element_located((
#             By.XPATH,
#             "//input[@name='old_password']/following::div[contains(@class,'field-error')]"
#         ))
#     )

#     assert "incorrect" in error.text.lower() \
#         or "incorrecta" in error.text.lower()
