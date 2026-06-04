# features/steps/ver_calendario.py
# ID: CU-02  Nombre: Ver calendario semestral

import datetime
import time
from behave import given, when, then

# Acceso directo al backend relacional de Django
from django.core.files.base import ContentFile
from lumat_app.models import CalendarioGenerado

# NOTA: Los pasos "ha iniciado sesión" y "tiene asignado el seminario del ciclo"
# se eliminaron de este archivo porque Behave los hereda y reutiliza automáticamente 
# desde features/steps/llenar_acta_alumno.py para evitar colisiones globales.


# ── Preparación del Estado del Calendario (Precondiciones) ────

@given('que existe un calendario de actividades programado en la base de datos')
def step_inyectar_calendario_db(context):
    # Forzamos una tabla limpia para el escenario aislando los datos
    CalendarioGenerado.objects.all().delete()
    
    archivo_falso = ContentFile(b"%PDF-1.4 mock_data", name="calendario_test.pdf")
    context.calendario_creado = CalendarioGenerado.objects.create(
        nombre="Calendario Oficial de Tutorías",
        fecha_inicio=datetime.date(2026, 2, 1),
        fecha_fin=datetime.date(2026, 7, 15),
        archivo_pdf=archivo_falso
    )


@given('que no hay ningún calendario registrado en el sistema')
def step_vaciar_calendarios_db(context):
    CalendarioGenerado.objects.all().delete()


# ── Acciones Lógicas (Simulación de Consulta de la Vista) ─────

@when('el alumno solicita consultar el calendario semestral')
def step_simular_consulta_calendario(context):
    # Evaluamos la misma query exacta que ejecuta tu vista real en el backend
    context.objeto_calendario_retornado = CalendarioGenerado.objects.first()


# ── Verificaciones Mediante el ORM de Django ──────────────────

@then('se verifica el acceso correcto a los datos del calendario')
def step_verificar_calendario_existente(context):
    assert context.objeto_calendario_retornado is not None, \
        "Error: El sistema no recuperó el calendario semestral programado."
    
    assert context.objeto_calendario_retornado.nombre == "Calendario Oficial de Tutorías", \
        f"Error: El nombre del calendario recuperado no coincide. Encontrado: {context.objeto_calendario_retornado.nombre}"


@then('se confirma que el objeto retornado en la consulta es nulo')
def step_verificar_calendario_nulo(context):
    assert context.objeto_calendario_retornado is None, \
        f"Error de consistencia: Se recuperó un objeto calendario ({context.objeto_calendario_retornado}) cuando la tabla debía estar vacía."