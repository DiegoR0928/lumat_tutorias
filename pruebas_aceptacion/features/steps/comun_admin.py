from behave import given
from selenium.webdriver.common.by import By
from django.contrib.auth.models import User


@given(u'un usuario administrador autenticado')
@given(u'he iniciado sesión como superusuario')
def step_impl(context):
    User.objects.filter(username='diego').delete()
    User.objects.create_superuser('diego', 'admin@test.com', 'diego')
    context.driver.get('http://app:8000/admin/login/')
    context.driver.find_element(By.NAME, 'username').send_keys('diego')
    context.driver.find_element(By.NAME, 'password').send_keys('diego')
    context.driver.find_element(By.XPATH, '//*[@type="submit"]').click()