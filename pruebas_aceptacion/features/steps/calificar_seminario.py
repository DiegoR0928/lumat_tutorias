# features/steps/calificar_seminario.py
# ID: CU-04  Nombre: Calificar seminario

import time
from decimal import Decimal
from behave import given, when, then

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from lumat_app.models import Alumno, Seminario, FormularioComite, Comite, Docente

User = get_user_model()
BASE_URL = "http://app:8000"


# ── Antecedentes ─────────────────────────────────────────────

@given('que el docente "{username}" con contraseña "{password}" ha iniciado sesión')
def step_login_docente(context, username, password):
    context.username_docente = username
    
    grupo_docente, _ = Group.objects.get_or_create(name='Docente')
    user_obj, _ = User.objects.get_or_create(username=username)
    user_obj.set_password(password)
    user_obj.groups.add(grupo_docente)
    user_obj.save()

    Docente.objects.filter(user=user_obj).delete()
    context.tutor_obj = Docente.objects.create(
        user=user_obj,
        nombre="Carlos",
        apellido_paterno="Lopez"
    )


@given('existe el seminario número {num:d} asignado al alumno "{alumno_user}"')
def step_preparar_seminario_calif(context, num, alumno_user):
    grupo_alumno, _ = Group.objects.get_or_create(name='Alumno')
    user_al, _ = User.objects.get_or_create(username=alumno_user)
    user_al.set_password('pass1234')
    user_al.groups.add(grupo_alumno)
    user_al.save()

    Alumno.objects.filter(user=user_al).delete()
    alumno_obj = Alumno.objects.create(
        user=user_al, nombre="Juan", apellido_paterno="Perez", matricula="CALIF05", semestre=str(num)
    )

    u_m1, _ = User.objects.get_or_create(username="sinodo_m1")
    u_m2, _ = User.objects.get_or_create(username="sinodo_m2")
    m1, _ = Docente.objects.get_or_create(user=u_m1, defaults={'nombre': 'Maria', 'apellido_paterno': 'Gomez'})
    m2, _ = Docente.objects.get_or_create(user=u_m2, defaults={'nombre': 'Jose', 'apellido_paterno': 'Sanz'})

    comite_obj, _ = Comite.objects.get_or_create(tutor=context.tutor_obj, miembro1=m1, miembro2=m2)

    Seminario.objects.filter(alumno=alumno_obj, numero=num).delete()
    context.seminario_test = Seminario.objects.create(
        alumno=alumno_obj,
        numero=num,
        comite=comite_obj,
        periodo=1,
        calificacion=None
    )


@given('el panel de evaluación está listo con calificaciones pendientes')
def step_inicializar_formulario_comite(context):
    FormularioComite.objects.filter(seminario=context.seminario_test).delete()
    context.formulario_test = FormularioComite.objects.create(
        seminario=context.seminario_test,
        estado_general='pendiente',
        firma_tutor=False,
        firma_miembro1=False,
        firma_miembro2=False
    )


# ── Acciones ─────────────────────────────────────────────────

@when('el comite asienta las notas individuales {nota1:f}, {nota2:f} y {nota3:f}')
def step_asentar_notas_completas(context, nota1, nota2, nota3):
    context.formulario_test.calificacion_tutor = Decimal(str(nota1))
    context.formulario_test.calificacion_miembro1 = Decimal(str(nota2))
    context.formulario_test.calificacion_miembro2 = Decimal(str(nota3))


@when('el tutor asienta una nota individual de {nota:f} y los demás quedan vacíos')
def step_asentar_nota_parcial(context, nota):
    context.formulario_test.calificacion_tutor = Decimal(str(nota))
    context.formulario_test.calificacion_miembro1 = None
    context.formulario_test.calificacion_miembro2 = None


@when('todos los miembros del comite firman el formulario')
def step_firmar_todo(context):
    context.formulario_test.firma_tutor = True
    context.formulario_test.firma_miembro1 = True
    context.formulario_test.firma_miembro2 = True
    context.formulario_test.save()


@when('solo firma el tutor original')
def step_firmar_parcial(context):
    context.formulario_test.firma_tutor = True
    context.formulario_test.firma_miembro1 = False
    context.formulario_test.firma_miembro2 = False
    context.formulario_test.save()


# ── Verificaciones ────────────────────────────────────────────

@then('se verifica en la base de datos que la calificación final del seminario es {calif_esperada:f}')
def step_verificar_calificacion_sincronizada(context, calif_esperada):
    time.sleep(1)
    context.seminario_test.refresh_from_db()
    nota_real = context.seminario_test.calificacion
    
    expected_decimal = Decimal(str(calif_esperada)).quantize(Decimal('0.01'))
    assert nota_real == expected_decimal, \
        f"Error de negocio: Se esperaba promedio {expected_decimal}, pero el seminario guardó {nota_real}"