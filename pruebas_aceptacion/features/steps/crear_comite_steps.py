from behave import given, when, then
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

@given(u'que existen tres docentes en el sistema')
def step_impl(context):
    pass

@given(u'he iniciado sesión como superusuario')
def step_impl(context):
    # Inicializamos el navegador
    context.driver = webdriver.Chrome()
    context.driver.get('http://localhost:8000/admin/login/')
    
    # Asumimos que ya tienes una cuenta de admin creada en tu BD
    context.driver.find_element(By.NAME, 'username').send_keys('diego')
    # Pon aquí la contraseña real de tu admin local
    context.driver.find_element(By.NAME, 'password').send_keys('diego') 
    context.driver.find_element(By.XPATH, '//*[@type="submit"]').click()

@when(u'navego a la página de crear comité')
def step_impl(context):
    context.driver.get('http://localhost:8000/admin/lumat_app/comite/add/')

@when(u'selecciono a los tres docentes')
def step_impl(context):
    # ¡LA MAGIA!: En lugar de usar IDs de base de datos, usamos select_by_visible_text
    # Pon aquí los nombres EXACTOS de 3 docentes que sepas que existen en tu sistema
    
    dropdown_tutor = Select(context.driver.find_element(By.NAME, 'tutor'))
    dropdown_tutor.select_by_visible_text('America Blanco')
    
    dropdown_miembro1 = Select(context.driver.find_element(By.NAME, 'miembro1'))
    dropdown_miembro1.select_by_visible_text('Diego Gomez')
    
    dropdown_miembro2 = Select(context.driver.find_element(By.NAME, 'miembro2'))
    dropdown_miembro2.select_by_visible_text('Montserrat Marquez')

@when(u'hago clic en guardar') 
def step_impl(context):
    context.driver.find_element(By.NAME, '_save').click()

@then(u'debería ver el mensaje de éxito en la pantalla')
def step_impl(context):
    wait = WebDriverWait(context.driver, 10)
    
    mensaje_exito = wait.until(
        EC.visibility_of_element_located((By.CLASS_NAME, "bg-green-100"))
    )
    
    assert "se agregó correctamente" in mensaje_exito.text.lower()
    
    context.driver.quit()

# Segundo escenario - Validación de campos obligatorios

@when(u'selecciono a "{nombre}" como tutor')
def step_impl(context, nombre):
    # Buscamos el dropdown de tutor y seleccionamos al docente por texto parcial
    dropdown = Select(context.driver.find_element(By.NAME, 'tutor'))
    
    # Buscamos la opción que coincida con el nombre
    for opcion in dropdown.options:
        if nombre in opcion.text:
            dropdown.select_by_visible_text(opcion.text)
            break

@when(u'dejo los campos de miembros vacíos')
def step_impl(context):
    pass

@then(u'el sistema debería resaltar los campos obligatorios y no guardar el comité')
def step_impl(context):
    # 1. Verificamos que NO nos hayamos movido de la página de creación.
    assert "add" in context.driver.current_url, "El sistema redirigió, lo que indica que el comité se guardó por error."

    try:
        # Esperamos a que aparezca la nota de error de Django
        wait = WebDriverWait(context.driver, 3)
        error_note = wait.until(
            EC.presence_of_element_located((By.CLASS_NAME, "errornote"))
        )
        
        campo_error = context.driver.find_element(By.CSS_SELECTOR, ".errors")
        
        assert error_note.is_displayed()
        assert campo_error.is_displayed()
        
    except:
        miembro1 = context.driver.find_element(By.NAME, "miembro1")
        
        # Verificamos si el campo es obligatorio según el HTML
        is_required = miembro1.get_attribute("required")
        assert is_required is not None, "El campo no tiene el atributo 'required' ni se mostró error de Django."

    finally:
        context.driver.quit()