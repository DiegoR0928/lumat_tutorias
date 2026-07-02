# features/steps/llenar_formulario_comite.py
import datetime
from behave import given, when, then
from django.contrib.auth.models import User
from lumat_app.models import Alumno, Docente, Comite, Seminario
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


@given('que existe un docente registrado como tutor y dos como miembros')
def step_impl(context):
    u_tutor, _ = User.objects.get_or_create(
        username='tutor_inf', defaults={'email': 't@u.com'})
    u_tutor.set_password('password123')
    u_tutor.save()

    u_m1, _ = User.objects.get_or_create(
        username='m1_inf', defaults={'email': 'm1@u.com'})
    u_m1.set_password('password123')
    u_m1.save()

    u_m2, _ = User.objects.get_or_create(
        username='m2_inf', defaults={'email': 'm2@u.com'})
    u_m2.set_password('password123')
    u_m2.save()

    context.tutor, _ = Docente.objects.get_or_create(
        user=u_tutor, defaults={'nombre': 'Tutor', 'apellido_paterno': 'García'})
    context.miembro1, _ = Docente.objects.get_or_create(
        user=u_m1, defaults={'nombre': 'M1', 'apellido_paterno': 'López'})
    context.miembro2, _ = Docente.objects.get_or_create(
        user=u_m2, defaults={'nombre': 'M2', 'apellido_paterno': 'Martínez'})

    context.comite, _ = Comite.objects.get_or_create(
        tutor=context.tutor, miembro1=context.miembro1, miembro2=context.miembro2)


@given('existe un estudiante en el semestre 4 con un seminario pendiente')
def step_impl(context):
    u_al, _ = User.objects.get_or_create(
        username='alumno_inf', defaults={'email': 'al@u.com'})
    u_al.set_password('password123')
    u_al.save()

    context.alumno, _ = Alumno.objects.get_or_create(
        user=u_al,
        defaults={'nombre': 'Luis', 'apellido_paterno': 'Pérez',
                  'semestre': 4, 'matricula': '3001'}
    )

    context.seminario, _ = Seminario.objects.get_or_create(
        alumno=context.alumno,
        numero=4,
        defaults={'comite': context.comite,
                  'fecha': datetime.date.today(), 'hora': datetime.time(10, 0)}
    )


@given('que el tutor ha iniciado sesión en el sistema')
def step_impl(context):
    context.driver.get('http://app:8000/login/')
    context.driver.find_element(By.NAME, 'username').send_keys('tutor_inf')
    context.driver.find_element(By.NAME, 'password').send_keys('password123')
    context.driver.find_element(By.XPATH, "//button[@type='submit']").click()


@given('se encuentra en la pantalla de "Mis Seminarios"')
def step_impl(context):
    context.driver.get('http://app:8000/docente/seminarios/')


@when('hace clic en el seminario del estudiante Luis Pérez')
def step_impl(context):
    wait = WebDriverWait(context.driver, 10)

    # ── CORREGIDO: Usamos element_to_be_clickable ──
    input_busqueda = wait.until(
        EC.element_to_be_clickable((By.ID, 'search-input')))
    input_busqueda.clear()
    input_busqueda.send_keys(context.alumno.matricula)

    form_busqueda = context.driver.find_element(By.ID, 'search-form')
    form_busqueda.submit()

    fila = wait.until(EC.element_to_be_clickable(
        (By.XPATH,
         f"//a[contains(@href, '/docente/seminarios/{context.seminario.id}/')]")
    ))
    fila.click()


@when('completa los campos de observaciones, dictamen, encuentros y propuestas')
def step_impl(context):
    wait = WebDriverWait(context.driver, 10)
    # ── CORREGIDO: Usamos element_to_be_clickable ──
    wait.until(EC.element_to_be_clickable(
        (By.ID, 'id_el_comite_encuentra'))).send_keys('Buen desempeño.')
    context.driver.find_element(
        By.ID, 'id_observaciones').send_keys('Ninguna.')
    context.driver.find_element(By.ID, 'id_dictamen').send_keys('Aprobado.')
    context.driver.find_element(By.ID, 'id_propuestas').send_keys(
        'Continuar con la tesis.')


@when('hace clic en el botón "Guardar informe"')
def step_impl(context):
    context.driver.find_element(
        By.XPATH, "//button[contains(text(), 'Guardar informe')]").click()


@then('el sistema debe mostrar el mensaje de éxito "{mensaje}"')
def step_impl(context, mensaje):
    wait = WebDriverWait(context.driver, 10)
    # ── CORREGIDO: Usamos presence_of_element_located para el contenedor del mensaje ──
    msg_box = wait.until(EC.presence_of_element_located(
        (By.CLASS_NAME, 'success-box')))
    assert mensaje in msg_box.text


@given('se encuentra en el detalle del seminario de Luis Pérez')
def step_impl(context):
    context.driver.get(
        f'http://app:8000/docente/seminarios/{context.seminario.id}/?rol=tutor')


@when('borra o deja vacíos los campos del informe')
def step_impl(context):
    wait = WebDriverWait(context.driver, 10)
    # ── CORREGIDO: Usamos element_to_be_clickable ──
    encuentra = wait.until(EC.element_to_be_clickable(
        (By.ID, 'id_el_comite_encuentra')))
    encuentra.clear()


@then('el sistema debe denegar el guardado mostrando un mensaje de error o validación')
def step_impl(context):
    wait = WebDriverWait(context.driver, 10)
    # ── CORREGIDO: Usamos presence_of_element_located ──
    error_p = wait.until(EC.presence_of_element_located(
        (By.XPATH, "//*[contains(@style, 'color:#c0392b') or contains(@class, 'errorlist') or contains(@class, 'info-box')]")
    ))
    assert error_p.is_displayed()
