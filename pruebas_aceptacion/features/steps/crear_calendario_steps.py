from datetime import date, time
from behave import given, when, then
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from django.contrib.auth.models import User
from lumat_app.models import Alumno, Docente, Comite, Seminario


@given('existen {num:d} seminarios registrados')
def step_impl(context, num):
    User.objects.filter(username__in=['doc_1', 'doc_2', 'doc_3']).delete()
    u_d1 = User.objects.create_user(username='doc_1', password='123')
    u_d2 = User.objects.create_user(username='doc_2', password='123')
    u_d3 = User.objects.create_user(username='doc_3', password='123')
    
    d1 = Docente.objects.create(user=u_d1, nombre="D1", apellido_paterno="A1")
    d2 = Docente.objects.create(user=u_d2, nombre="D2", apellido_paterno="A2")
    d3 = Docente.objects.create(user=u_d3, nombre="D3", apellido_paterno="A3")
    
    comite = Comite.objects.create(tutor=d1, miembro1=d2, miembro2=d3)
    for i in range(num):
        u_a = User.objects.create_user(username=f'al_{i}', password='123')
        al = Alumno.objects.create(matricula=f'M{i}', user=u_a)
        Seminario.objects.create(
            alumno=al, comite=comite, fecha=date(2026, 6, 2),
            hora=time(9, 0), numero=1
        )


@when('ingreso al formulario de calendario')
def step_impl(context):
    context.driver.get('http://app:8000/admin/calendar-generator/')


@when('selecciono la fecha inicial "{inicio}" y final "{fin}"')
def step_impl(context, inicio, fin):
    input_inicio = context.driver.find_element(By.NAME, 'fecha_inicial')
    input_fin = context.driver.find_element(By.NAME, 'fecha_final')
    
    context.driver.execute_script("arguments[0].value = arguments[1];", input_inicio, inicio)
    context.driver.execute_script("arguments[0].value = arguments[1];", input_fin, fin)


@when('presiono el boton de generar calendario')
def step_impl(context):
    # Apuntamos estrictamente al boton que esta dentro de tu formulario de generacion
    xpath_btn = "//form[contains(@action, 'calendar-generator')]//button[@type='submit']"
    boton = context.driver.find_element(By.XPATH, xpath_btn)
    context.driver.execute_script("arguments[0].click();", boton)


@then('soy redirigido al formulario con un mensaje de exito')
def step_impl(context):
    wait = WebDriverWait(context.driver, 10)
    try:
        alerta = wait.until(EC.visibility_of_element_located((By.CLASS_NAME, "msg-success")))
        assert alerta.is_displayed()
    except TimeoutException:
        raise AssertionError(
            f"Timeout esperando msg-success. "
            f"URL actual: {context.driver.current_url}. "
            f"HTML de respuesta: {context.driver.page_source[:400]}"
        )


@then('se muestra el nuevo calendario publicado')
def step_impl(context):
    assert "Calendarios Publicados" in context.driver.page_source


@then('soy redirigido al formulario con un mensaje de error')
def step_impl(context):
    wait = WebDriverWait(context.driver, 10)
    try:
        alerta = wait.until(EC.visibility_of_element_located((By.CLASS_NAME, "msg-error")))
        assert alerta.is_displayed()
    except TimeoutException:
        raise AssertionError(
            f"Timeout esperando msg-error. "
            f"URL actual: {context.driver.current_url}. "
            f"HTML de respuesta: {context.driver.page_source[:400]}"
        )