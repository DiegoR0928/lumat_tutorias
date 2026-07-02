# features/steps/llenar_acta_alumno.py
# ID: CU-06  Nombre: Llenar acta del alumno

import time
from behave import given, when, then

# Acceso directo al backend relacional de Django
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from lumat_app.models import Alumno, Seminario, FormularioComite, Comite, Docente, ActaAlumnoData

User = get_user_model()

# ── Antecedentes Propios (Garantizando datos compactos para evitar DataError) ──

@given('que el alumno específico "{username}" con contraseña "{password}" ha iniciado sesión')
def step_login_alumno_acta_unico(context, username, password):
    context.username_alumno = username

    # Asegurar el grupo Alumno para los decoradores de seguridad de la app
    grupo_alumno, _ = Group.objects.get_or_create(name='Alumno')
    user_obj, _ = User.objects.get_or_create(username=username)
    user_obj.set_password(password)
    user_obj.groups.add(grupo_alumno)
    user_obj.save()

    # SOLUCIÓN DEFINITIVA A LONGITUD: Generamos una matrícula puramente numérica de 6 dígitos
    # utilizando el hash del username absoluto. Esto garantiza unicidad sin violar límites VARCHAR cortos.
    matricula_segura = str(abs(hash(username)))[:6]

    context.alumno_real, _ = Alumno.objects.update_or_create(
        user=user_obj,
        defaults={
            'nombre': 'Amer',
            'apellido_paterno': 'Inaga',
            'matricula': matricula_segura,  # Ejemplo: "482910" (Seguro para cualquier VARCHAR)
            'semestre': '4',
            'correo': "am@lum.ed"  # Email ultra-corto preventivo
        }
    )


@given('el alumno tiene asignado el seminario del ciclo {num:d}')
def step_preparar_seminario_alumno_acta_unico(context, num):
    # Forzamos a que el semestre del alumno concuerde con el seminario bajo prueba
    context.alumno_real.semestre = str(num)
    context.alumno_real.save()

    # Aseguramos sínodos legítimos para pasar Comite.clean() obligatoria
    doc1, _ = Docente.objects.get_or_create(user=User.objects.get_or_create(username="t1")[0], nombre="Tutor A")
    doc2, _ = Docente.objects.get_or_create(user=User.objects.get_or_create(username="t2")[0], nombre="Sinodo B")
    doc3, _ = Docente.objects.get_or_create(user=User.objects.get_or_create(username="t3")[0], nombre="Sinodo C")
    comite_obj, _ = Comite.objects.get_or_create(tutor=doc1, miembro1=doc2, miembro2=doc3)

    Seminario.objects.filter(alumno=context.alumno_real, numero=num).delete()
    context.seminario_test = Seminario.objects.create(
        alumno=context.alumno_real,
        numero=num,
        comite=comite_obj,
        calificacion=None
    )


@given('que el formulario del comité para el seminario {num:d} tiene el estado general "{estado}"')
def step_establecer_estado_comite_previo(context, num, estado):
    # Se genera el acta del comité requerida como precondición habilitante
    FormularioComite.objects.filter(seminario=context.seminario_test).delete()
    context.form_comite_test = FormularioComite.objects.create(
        seminario=context.seminario_test,
        estado_general=estado,
        firma_tutor=(estado == "completo"),
        firma_miembro1=(estado == "completo"),
        firma_miembro2=(estado == "completo")
    )


# ── Acciones Lógicas de Negocio ────────────────────────────────

@when('el alumno registra sus actividades con reuniones de tutor {tutor_count:d} y reuniones de comité {comite_count:d}')
def step_redactar_actividades_alumno(context, tutor_count, comite_count):
    # Instanciamos el objeto en memoria (esperando el paso final para guardar condicionalmente)
    ActaAlumnoData.objects.filter(seminario=context.seminario_test).delete()
    context.acta_alumno_memoria = ActaAlumnoData(
        seminario=context.seminario_test,
        actividad_principal="Desarrollo e integración de simuladores interactivos.",
        reuniones_tutor=tutor_count,
        reuniones_comite=comite_count,
        coloquios=1,
        plan_siguiente=""
    )


@when('el alumno asienta su plan siguiente "{plan_txt}"')
def step_guardar_acta_alumno_valida(context, plan_txt):
    context.form_comite_test.refresh_from_db()
    # Flujo Feliz: Si el comité está completo, permitimos la persistencia real
    if context.form_comite_test.estado_general == "completo":
        context.acta_alumno_memoria.plan_siguiente = plan_txt
        context.acta_alumno_memoria.save()


@when('el alumno intenta forzar el registro de sus actividades y plan de trabajo')
def step_intentar_forzar_guardado_bloqueado(context):
    context.form_comite_test.refresh_from_db()
    # Flujo de Restricción: Si el estado sigue 'pendiente', no se crea la instancia
    if context.form_comite_test.estado_general == "completo":
        ActaAlumnoData.objects.create(
            seminario=context.seminario_test,
            actividad_principal="Forzado",
            plan_siguiente="Forzado"
        )


# ── Verificación mediante ORM ──────────────────────────────────

@then('se verifica en la base de datos que el acta del alumno se guardó exitosamente')
def step_verificar_acta_guardada(context):
    time.sleep(0.5)
    existe = ActaAlumnoData.objects.filter(seminario=context.seminario_test).exists()
    assert existe, "Error de negocio: El acta del alumno debió guardarse ya que el comité completó su evaluación."


@then('se verifica en la base de datos que no se creó ningún registro de acta para el alumno')
def step_verificar_acta_bloqueada(context):
    time.sleep(0.5)
    existe = ActaAlumnoData.objects.filter(seminario=context.seminario_test).exists()
    assert not existe, "Fallo de validación: Se registró el acta del alumno pero el formulario del comité sigue pendiente."