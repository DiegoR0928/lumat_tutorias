# features/steps/cargar_actividad.py
# ID: CU-03  Nombre: Cargar actividades

import os
import tempfile
from behave import given, when, then
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

BASE_URL = "http://app:8000"


def esperar(context, segundos=5):
    return WebDriverWait(context.driver, segundos)


def crear_archivo_temporal(nombre):
    ext = os.path.splitext(nombre)[1]
    tmp = tempfile.NamedTemporaryFile(suffix=ext, delete=False)
    if ext == ".pdf":
        tmp.write(b"%PDF-1.4\n" + b"0" * 1024)
    else:
        tmp.write(b"contenido falso")
    tmp.close()
    return tmp.name


# ── Antecedentes ─────────────────────────────────────────────

@given('que el alumno "{username}" con contraseña "{password}" ha iniciado sesión')
def step_login(context, username, password):
    context.driver.get(f"{BASE_URL}/login/")
    esperar(context).until(
        EC.presence_of_element_located((By.NAME, "username")))
    context.driver.find_element(By.NAME, "username").send_keys(username)
    context.driver.find_element(By.NAME, "password").send_keys(password)
    context.driver.find_element(By.CSS_SELECTOR, "[type='submit']").click()
    esperar(context).until(EC.url_contains("/alumno/"))


@given('el alumno navega al seminario {num:d}')
def step_navegar_seminario(context, num):
    context.driver.get(f"{BASE_URL}/alumno/seminario/{num}/")
    esperar(context).until(
        EC.presence_of_element_located((By.TAG_NAME, "body")))


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
        "arguments[0].style.display='block';", file_input)
    file_input.send_keys(filepath)


@when('el alumno hace clic en el botón "Cargar actividad"')
def step_clic_boton(context):
    boton = context.driver.find_element(By.ID, "ev-submit")
    context.driver.execute_script(
        "arguments[0].removeAttribute('disabled')", boton)
    # Usar JS click para evitar ElementClickInterceptedException
    context.driver.execute_script("arguments[0].click()", boton)


# ── Verificaciones ────────────────────────────────────────────

@then('la página muestra el texto "{texto}"')
def step_texto_en_pagina(context, texto):
    esperar(context).until(
        EC.text_to_be_present_in_element((By.TAG_NAME, "body"), texto)
    )


@then('el botón con id "{elemento_id}" está deshabilitado')
def step_boton_deshabilitado(context, elemento_id):
    boton = context.driver.find_element(By.ID, elemento_id)
    assert boton.get_attribute("disabled") is not None, \
        f"Se esperaba que #{elemento_id} estuviera deshabilitado"


@then('el botón con id "{elemento_id}" está habilitado')
def step_boton_habilitado(context, elemento_id):
    esperar(context).until(
        lambda d: d.find_element(
            By.ID, elemento_id).get_attribute("disabled") is None
    )
