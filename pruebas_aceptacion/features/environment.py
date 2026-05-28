from selenium.webdriver.chrome.options import Options
from selenium import webdriver
import urllib.request
import time
import os
import sys
import django
from selenium.common.exceptions import WebDriverException

sys.path.insert(0, '/app/lumat_tutorias')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lumat_tutorias.settings')
django.setup()


def before_all(context):
    for _ in range(30):
        try:
            urllib.request.urlopen('http://app:8000/login/')
            break
        except Exception:
            time.sleep(1)


def before_scenario(context, scenario):
    _limpiar_datos(scenario.tags)

    chrome_options = Options()
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--headless')
    chrome_options.set_capability("browserName", "chrome")

    context.driver = webdriver.Remote(
        command_executor='http://selenium-hub:4444/wd/hub',
        options=chrome_options
    )


def after_scenario(context, scenario):
    try:
        context.driver.quit()
    except WebDriverException as e:
        print(f"⚠️  Error al cerrar el navegador: {e}")


def _limpiar_datos(tags):
    from django.contrib.auth.models import User
    from lumat_app.models import Alumno, Docente

    if 'limpiar_usuarios' in tags:
        User.objects.filter(is_superuser=False).delete()

    if 'limpiar_alumnos' in tags:
        Alumno.objects.all().delete()

    if 'limpiar_docentes' in tags:
        Docente.objects.all().delete()