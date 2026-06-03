from datetime import date, time
from behave import given, when, then
from selenium.webdriver.common.by import By
from django.contrib.auth.models import User
from lumat_app.models import Alumno, Docente, Comite, Seminario, SolicitudCambioTutor


@given('existe una solicitud de cambio de tutor pendiente')
def step_impl(context):
    u_d1 = User.objects.create_user(username='tutor_old')
    u_d2 = User.objects.create_user(username='vocal1')
    u_d3 = User.objects.create_user(username='vocal2')
    u_d4 = User.objects.create_user(username='elegible_new')
    
    d1 = Docente.objects.create(user=u_d1, nombre="Tutor", apellido_paterno="Viejo")
    d2 = Docente.objects.create(user=u_d2, nombre="V1", apellido_paterno="X")
    d3 = Docente.objects.create(user=u_d3, nombre="V2", apellido_paterno="Y")
    context.doc_elegible = Docente.objects.create(
        user=u_d4, nombre="Docente", apellido_paterno="Elegible"
    )
    
    comite = Comite.objects.create(tutor=d1, miembro1=d2, miembro2=d3)
    u_a = User.objects.create_user(username='alumno_cambio')
    al = Alumno.objects.create(matricula="20269999", user=u_a)
    
    Seminario.objects.create(
        alumno=al, comite=comite, fecha=date(2026, 6, 2),
        hora=time(10, 0), numero=1
    )
    context.solicitud = SolicitudCambioTutor.objects.create(
        alumno=al, motivo="Exceso de carga laboral del docente."
    )


@when('ingreso a la gestion de cambio de tutor')
def step_impl(context):
    context.driver.get('http://app:8000/admin/cambio-tutor/')


@when('selecciono un nuevo docente elegible')
def step_impl(context):
    select = context.driver.find_element(By.NAME, 'docente_id')
    for option in select.find_elements(By.TAG_NAME, 'option'):
        if "Elegible" in option.text:
            option.click()
            break


@when('presiono el boton aprobar cambio de tutor')
def step_impl(context):
    context.driver.find_element(By.XPATH, "//button[@value='aprobar']").click()


@then('la solicitud cambia a estado aprobada')
def step_impl(context):
    context.solicitud.refresh_from_db()
    assert context.solicitud.estado == "aprobada"


@when('presiono el boton rechazar cambio de tutor')
def step_impl(context):
    context.driver.find_element(By.XPATH, "//button[@value='rechazar']").click()


@then('la solicitud cambia a estado rechazada')
def step_impl(context):
    context.solicitud.refresh_from_db()
    assert context.solicitud.estado == "rechazada"


@then('veo un mensaje de error indicando elegir un tutor')
def step_impl(context):
    assert "Debe seleccionar un nuevo tutor" in context.driver.page_source


@when('selecciono un docente que ya pertenece al comite')
def step_impl(context):
    select = context.driver.find_element(By.NAME, 'docente_id')
    for option in select.find_elements(By.TAG_NAME, 'option'):
        if "V1" in option.text:
            option.click()
            break


@then('veo un mensaje de error por miembro activo en comite')
def step_impl(context):
    assert "ya es miembro activo" in context.driver.page_source