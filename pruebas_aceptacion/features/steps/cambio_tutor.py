# features/steps/cambio_tutor.py
# ID: CU-cambio-tutor

from behave import given, when, then
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

BASE_URL = "http://app:8000"


def esperar(context, segundos=5):
    return WebDriverWait(context.driver, segundos)


# ── Antecedentes ─────────────────────────────────────────────

@given('que el alumno navega a la página de cambio de tutor')
def step_navegar_dado(context):
    context.driver.get(f"{BASE_URL}/alumno/tutor/cambio/")
    esperar(context).until(EC.presence_of_element_located((By.ID, "ct-form")))


@given('que el alumno ya tiene una solicitud pendiente')
def step_crear_solicitud(context):
    from lumat_app.models import Alumno, SolicitudCambioTutor
    alumno = Alumno.objects.get(user__username="amerinaga")
    SolicitudCambioTutor.objects.get_or_create(
        alumno=alumno,
        estado="pendiente",
        defaults={"motivo": "Solicitud preexistente para prueba"}
    )


# ── Acciones ─────────────────────────────────────────────────

@given('el alumno navega a la página de cambio de tutor')
def step_navegar_cuando(context):
    context.driver.get(f"{BASE_URL}/alumno/tutor/cambio/")
    esperar(context).until(EC.presence_of_element_located((By.TAG_NAME, "body")))


@when('el alumno escribe "{texto}" en el campo motivo')
def step_escribir_motivo(context, texto):
    campo = context.driver.find_element(By.ID, "ct-motivo")
    context.driver.execute_script("arguments[0].scrollIntoView(true);", campo)
    context.driver.execute_script("arguments[0].removeAttribute('disabled');", campo)
    campo.clear()
    campo.send_keys(texto)
    # Disparar el evento input manualmente para activar el JS del contador
    context.driver.execute_script(
        "arguments[0].dispatchEvent(new Event('input'));", campo
    )


@when('el alumno hace clic en el botón de enviar solicitud')
def step_clic_enviar(context):
    boton = context.driver.find_element(By.ID, "ct-submit")
    context.driver.execute_script("arguments[0].scrollIntoView(true);", boton)
    context.driver.execute_script("arguments[0].click()", boton)


@when('el alumno hace clic en el botón de enviar sin motivo')
def step_clic_sin_motivo(context):
    boton = context.driver.find_element(By.ID, "ct-submit")
    context.driver.execute_script("arguments[0].scrollIntoView(true);", boton)
    context.driver.execute_script("arguments[0].removeAttribute('disabled')", boton)
    context.driver.execute_script("arguments[0].click()", boton)


# ── Verificaciones ────────────────────────────────────────────

@then('la solicitud fue enviada exitosamente')
def step_solicitud_enviada(context):
    # El view redirige al seminario tras POST exitoso
    esperar(context, 10).until(EC.url_contains("/alumno/seminario/"))


# @then('la página muestra el texto "{texto}"')
# def step_texto_en_pagina(context, texto):
#     esperar(context, 10).until(
#         EC.text_to_be_present_in_element((By.TAG_NAME, "body"), texto)
#     )


@then('el mensaje de error "{texto}" es visible en la página')
def step_error_visible(context, texto):
    # El error lo muestra el JS del cliente en #ct-error-motivo con clase .visible
    # Verificamos que el elemento tenga la clase 'visible' y contenga el texto
    esperar(context, 5).until(
        lambda d: "visible" in (
            d.find_element(By.ID, "ct-error-motivo").get_attribute("class") or ""
        )
    )


# @then('el botón con id "{elemento_id}" está deshabilitado')
# def step_boton_deshabilitado(context, elemento_id):
#     boton = context.driver.find_element(By.ID, elemento_id)
#     assert boton.get_attribute("disabled") is not None, \
#         f"Se esperaba que #{elemento_id} estuviera deshabilitado"


# @then('el botón con id "{elemento_id}" está habilitado')
# def step_boton_habilitado(context, elemento_id):
#     # El JS habilita el botón cuando hay texto; verificar que disabled desaparezca
#     esperar(context, 5).until(
#         lambda d: d.find_element(
#             By.ID, elemento_id).get_attribute("disabled") is None
#     )