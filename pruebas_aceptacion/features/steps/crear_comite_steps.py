from behave import given, when, then
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from django.contrib.auth.models import User
from lumat_app.models import Docente


@given(u'que existen tres docentes en el sistema')
def step_impl(context):
    User.objects.filter(username__in=['u_am', 'u_di', 'u_mo']).delete()
    u1 = User.objects.create_user(username='u_am')
    u2 = User.objects.create_user(username='u_di')
    u3 = User.objects.create_user(username='u_mo')
    Docente.objects.get_or_create(
        user=u1, nombre='America', apellido_paterno='Blanco'
    )
    Docente.objects.get_or_create(
        user=u2, nombre='Diego', apellido_paterno='Gomez'
    )
    Docente.objects.get_or_create(
        user=u3, nombre='Montserrat', apellido_paterno='Marquez'
    )


@when(u'navego a la página de crear comité')
def step_impl(context):
    context.driver.get('http://app:8000/admin/lumat_app/comite/add/')


@when(u'selecciono a los tres docentes')
def step_impl(context):
    sel_tutor = Select(context.driver.find_element(By.NAME, 'tutor'))
    sel_tutor.select_by_visible_text('America Blanco')
    
    sel_m1 = Select(context.driver.find_element(By.NAME, 'miembro1'))
    sel_m1.select_by_visible_text('Diego Gomez')
    
    sel_m2 = Select(context.driver.find_element(By.NAME, 'miembro2'))
    sel_m2.select_by_visible_text('Montserrat Marquez')


@when(u'hago clic en guardar')
def step_impl(context):
    context.driver.find_element(By.NAME, '_save').click()


@then(u'debería ver el mensaje de éxito en la pantalla')
def step_impl(context):
    wait = WebDriverWait(context.driver, 10)
    msg = wait.until(EC.visibility_of_element_located((By.CLASS_NAME, "bg-green-100")))
    assert "se agregó correctamente" in msg.text.lower()


@when(u'selecciono a "{nombre}" como tutor')
def step_impl(context, nombre):
    dropdown = Select(context.driver.find_element(By.NAME, 'tutor'))
    for option in dropdown.options:
        if nombre in option.text:
            dropdown.select_by_visible_text(option.text)
            break


@when(u'dejo los campos de miembros vacíos')
def step_impl(context):
    pass


@then(u'el sistema debería resaltar los campos obligatorios y no guardar el comité')
def step_impl(context):
    assert "add" in context.driver.current_url
    try:
        wait = WebDriverWait(context.driver, 3)
        err_note = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "errornote")))
        campo_err = context.driver.find_element(By.CSS_SELECTOR, ".errors")
        assert err_note.is_displayed()
        assert campo_err.is_displayed()
    except (TimeoutException, NoSuchElementException):
        m1 = context.driver.find_element(By.NAME, "miembro1")
        assert m1.get_attribute("required") is not None