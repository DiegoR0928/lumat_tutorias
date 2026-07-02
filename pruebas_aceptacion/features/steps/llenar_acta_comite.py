# features/steps/llenar_acta_comite.py
# ID: CU-05  Nombre: Llenar acta del comite

import time
from behave import given, when, then

# Acceso directo al backend relacional de Django
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from lumat_app.models import Alumno, Seminario, FormularioComite, Comite, Docente

User = get_user_model()


# ── Antecedentes ─────────────────────────────────────────────

@given('que el tutor "{username}" con contraseña "{password}" ha iniciado sesión en la plataforma')
def step_login_tutor_acta(context, username, password):
    context.username_tutor = username

    # Asegurar el grupo Docente para consistencia de roles de usuario
    grupo_docente, _ = Group.objects.get_or_create(name='Docente')
    user_obj, _ = User.objects.get_or_create(username=username)
    user_obj.set_password(password)
    user_obj.groups.add(grupo_docente)
    user_obj.save()

    Docente.objects.filter(user=user_obj).delete()
    context.tutor_real = Docente.objects.create(
        user=user_obj,
        nombre="Carlos",
        apellido_paterno="Lopez"
    )


@given('existe un seminario activo número {num:d} para el alumno "{alumno_user}" con un comité asignado')
def step_preparar_seminario_e_infraestructura(context, num, alumno_user):
    grupo_alumno, _ = Group.objects.get_or_create(name='Alumno')
    user_al, _ = User.objects.get_or_create(username=alumno_user)
    user_al.groups.add(grupo_alumno)
    user_al.save()

    # Perfil del Alumno sincronizado en el semestre bajo evaluación
    Alumno.objects.filter(user=user_al).delete()
    alumno_obj = Alumno.objects.create(
        user=user_al, nombre="Pedro", apellido_paterno="Infante", matricula="ACTA04", semestre=str(num)
    )

    # Requerimos sínodos complementarios distintos para pasar Comite.clean()
    u_m1, _ = User.objects.get_or_create(username="docente_m1")
    u_m2, _ = User.objects.get_or_create(username="docente_m2")
    m1, _ = Docente.objects.get_or_create(user=u_m1, defaults={'nombre': 'Maria', 'apellido_paterno': 'Gomez'})
    m2, _ = Docente.objects.get_or_create(user=u_m2, defaults={'nombre': 'Jose', 'apellido_paterno': 'Sanz'})

    comite_sinodal, _ = Comite.objects.get_or_create(tutor=context.tutor_real, miembro1=m1, miembro2=m2)

    Seminario.objects.filter(alumno=alumno_obj, numero=num).delete()
    context.seminario_test = Seminario.objects.create(
        alumno=alumno_obj,
        numero=num,
        comite=comite_sinodal,
        calificacion=None
    )


@given('el panel tiene un formulario de acta en estado "{estado}"')
def step_inicializar_acta_vacia(context, estado):
    FormularioComite.objects.filter(seminario=context.seminario_test).delete()
    context.formulario_test = FormularioComite.objects.create(
        seminario=context.seminario_test,
        estado_general=estado,
        el_comite_encuentra="",
        observaciones="",
        dictamen="",
        propuestas=""
    )


# ── Acciones Lógicas de Negocio ────────────────────────────────

@when('el tutor redacta el reporte con encuentra "{encuentra_txt}" y observaciones "{obs_txt}"')
def step_redactar_reporte(context, encuentra_txt, obs_txt):
    context.formulario_test.el_comite_encuentra = encuentra_txt
    context.formulario_test.observaciones = obs_txt


@when('el tutor asienta el dictamen "{dictamen_txt}"')
def step_asentar_dictamen(context, dictamen_txt):
    context.formulario_test.dictamen = dictamen_txt
    context.formulario_test.save()  # Persistencia directa


@when('el tutor deja el campo dictamen vacío al guardar')
def step_guardar_vacio(context):
    context.formulario_test.dictamen = ""
    context.formulario_test.save()


# ── Verificación mediante ORM ──────────────────────────────────

@then('se verifica en la base de datos que el informe del comité guardó el dictamen correctamente')
def step_verificar_guardado_ok(context):
    time.sleep(0.5)
    context.formulario_test.refresh_from_db()
    
    assert "Aprobado" in context.formulario_test.dictamen, \
        f"Error de persistencia: El dictamen guardado está vacío o es incorrecto: {context.formulario_test.dictamen}"


@then('se verifica en la base de datos que el dictamen en el formulario sigue estando vacío')
def step_verificar_vacio_db(context):
    time.sleep(0.5)
    context.formulario_test.refresh_from_db()
    
    assert context.formulario_test.dictamen == "", \
        f"Error de validación: Se guardó un valor en el dictamen cuando debía permanecer vacío. Valor: {context.formulario_test.dictamen}"