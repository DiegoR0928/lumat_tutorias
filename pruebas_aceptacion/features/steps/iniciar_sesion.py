from behave import  when, then, given
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

@given(u'que ingreso en el sistema de tutorias')
def step_impl(context):
    context.driver = webdriver.Chrome()
    context.driver.get('http://localhost:8000/login/')


@given(u'escribo mi usuario "{usuario}"')
def step_impl(context, usuario):
    context.driver.find_element(By.ID, 'id_usuario').send_keys(usuario)


@given(u'escribo la contraseña "{contraseña}"')
def step_impl(context, contraseña):
    context.driver.find_element(By.ID, 'id_contrasena').send_keys(contraseña)


@when(u'presiono el botón "Entrar"')
def step_impl(context):
    context.driver.find_element(By.ID, 'btn_login').click()


@then(u'puedo ver la sección "" del sistema')
def step_impl(context):
    pass

@then(u'puedo ver un mensaje de error indicando que las credenciales son incorrectas')
def step_impl(context):
    wait = WebDriverWait(context.driver, 10)
    
    error = wait.until(
        EC.visibility_of_element_located((By.CLASS_NAME, "alert-danger"))
    )
    
    assert "Credenciales inválidas" in error.text