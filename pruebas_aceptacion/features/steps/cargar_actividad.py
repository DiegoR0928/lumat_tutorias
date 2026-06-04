# features/steps/cargar_actividad.py
# ID: CU-03  Nombre: Cargar actividades

import os
import time
import tempfile
from behave import given, when, then
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Uso directo de los modelos de Django
from django.contrib.auth import get_user_model
from lumat_app.models import Alumno, Seminario, FormularioComite, Comite, Docente, Evidencia
from django.contrib.auth.models import Group

User = get_user_model()
BASE_URL = "http://app:8000"


def esperar(context, segundos=10):
    return WebDriverWait(context.driver, segundos)


def crear_archivo_temporal(nombre):
    ext = os.path.splitext(nombre)[1].lower()
    tmp = tempfile.NamedTemporaryFile(suffix=ext, delete=False)
    if ext == ".pdf":
        tmp.write(b"%PDF-1.4\n" + b"0" * 512)
    else:
        tmp.write(b"contenido binario simulado")
    tmp.close()
    return tmp.name


# ── Antecedentes ─────────────────────────────────────────────

@given('que el alumno "{username}" con contraseña "{password}" ha iniciado sesión')
def step_login(context, username, password):
    context.username_sesion = username
    context.password_sesion = password

    grupo_alumno, _ = Group.objects.get_or_create(name='Alumno')
    user_obj, _ = User.objects.get_or_create(username=username)
    user_obj.set_password(password)
    user_obj.groups.add(grupo_alumno)
    user_obj.save()

    Alumno.objects.filter(user=user_obj).delete()
    context.alumno_obj = Alumno.objects.create(
        user=user_obj,
        nombre='Amer',
        apellido_paterno='Inaga',
        matricula='123456',
        semestre='4',
        correo='amer@lumat.edu'
    )


@given('el alumno tiene asignado el seminario número {num:d}')
def step_asegurar_seminario_bd(context, num):
    context.alumno_obj.semestre = str(num)
    context.alumno_obj.save()

    doc1, _ = Docente.objects.get_or_create(
        user=User.objects.get_or_create(username="t1")[0], nombre="Tutor A")
    doc2, _ = Docente.objects.get_or_create(
        user=User.objects.get_or_create(username="t2")[0], nombre="Sinodo B")
    doc3, _ = Docente.objects.get_or_create(
        user=User.objects.get_or_create(username="t3")[0], nombre="Sinodo C")
    comite_obj, _ = Comite.objects.get_or_create(
        tutor=doc1, miembro1=doc2, miembro2=doc3)

    Seminario.objects.filter(alumno=context.alumno_obj, numero=num).delete()
    context.seminario_test = Seminario.objects.create(
        alumno=context.alumno_obj,
        numero=num,
        comite=comite_obj,
        periodo=1,
        calificacion=None
    )

    context.driver.get(f"{BASE_URL}/login/")
    esperar(context).until(
        EC.presence_of_element_located((By.NAME, "username")))
    context.driver.find_element(
        By.NAME, "username").send_keys(context.username_sesion)
    context.driver.find_element(
        By.NAME, "password").send_keys(context.password_sesion)
    context.driver.find_element(By.CSS_SELECTOR, "[type='submit']").click()
    esperar(context).until(EC.url_contains("/alumno/"))


@given('el formulario del comité para el seminario {num:d} tiene el estado general "{estado}"')
def step_set_estado_formulario_comite(context, num, estado):
    form_comite, _ = FormularioComite.objects.get_or_create(
        seminario=context.seminario_test,
        defaults={'estado_general': estado}
    )
    if form_comite.estado_general != estado:
        form_comite.estado_general = estado
        form_comite.save()


@given('el alumno navega al panel del seminario {num:d}')
def step_navegar_seminario(context, num):
    context.driver.get(f"{BASE_URL}/alumno/seminario/{num}/")
    esperar(context).until(
        EC.presence_of_element_located((By.ID, "ev-nombre")))


# ── Acciones ─────────────────────────────────────────────────

@when('el alumno escribe "{texto}" en el campo nombre')
def step_escribir_nombre(context, texto):
    campo = context.driver.find_element(By.ID, "ev-nombre")
    campo.clear()
    campo.send_keys(texto)


@when('el alumno adjunta el archivo "{nombre_archivo}"')
def step_adjuntar_archivo(context, nombre_archivo):
    filepath = crear_archivo_temporal(nombre_archivo)
    file_input = context.driver.find_element(By.ID, "ev-archivo")
    context.driver.execute_script(
        "arguments[0].style.display='block'; arguments[0].style.opacity='1';", file_input)
    file_input.send_keys(filepath)


@when('el alumno hace clic en el botón "Cargar actividad"')
def step_clic_boton(context):
    boton = context.driver.find_element(By.ID, "ev-submit")
    context.driver.execute_script(
        "arguments[0].removeAttribute('disabled')", boton)
    context.driver.execute_script("arguments[0].click();", boton)


# ── Evaluación Directa vía Base de Datos ──────────────────────

@then('se verifica que la actividad "{nombre_evidencia}" quedó registrada en la base de datos')
def step_verificar_persistencia_ok(context, nombre_evidencia):
    # Espera corta para asegurar que el ciclo de vida del Request de Daphne/Gunicorn terminó
    time.sleep(1.5)

    existe = Evidencia.objects.filter(
        seminario=context.seminario_test,
        nombre=nombre_evidencia
    ).exists()

    assert existe, f"Fallo de negocio: La evidencia '{nombre_evidencia}' debió guardarse con éxito."


@then('se verifica que la actividad "{nombre_evidencia}" no fue guardada en la base de datos')
def step_verificar_persistencia_fail(context, nombre_evidencia):
    time.sleep(1.5)

    existe = Evidencia.objects.filter(
        seminario=context.seminario_test,
        nombre=nombre_evidencia
    ).exists()

    assert not existe, f"Fallo de validación: La evidencia '{nombre_evidencia}' rompe las reglas MIME y NO debió ser guardada."
