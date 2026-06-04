from behave import given, when, then
from django.contrib.auth.models import User
from lumat_app.models import Alumno, Docente


@given('existen {alumnos:d} alumnos y {docentes:d} docentes registrados')
def step_impl(context, alumnos, docentes):
    for i in range(docentes):
        u = User.objects.create_user(username=f'doc_st_{i}')
        Docente.objects.create(user=u)
    for i in range(alumnos):
        u = User.objects.create_user(username=f'al_st_{i}')
        Alumno.objects.create(matricula=f'MS{i}', user=u)


@when('ingreso al panel de estadisticas')
def step_impl(context):
    context.driver.get('http://app:8000/admin/estadisticas/')


@then('el dashboard muestra "{alumnos}" alumnos y "{docentes}" docentes')
def step_impl(context, alumnos, docentes):
    source = context.driver.page_source
    assert alumnos in source
    assert docentes in source
