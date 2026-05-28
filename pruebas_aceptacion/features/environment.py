# # -- FILE: features/environment.py
# # from behave import fixture, use_fixture
# from selenium.webdriver.chrome.options import Options
# from selenium import webdriver
# import urllib.request
# import time
# from selenium.common.exceptions import WebDriverException

# def before_all(context):
#     # Espera hasta que Django esté respondiendo (máx 30 segundos)
#     for _ in range(30):
#         try:
#             urllib.request.urlopen('http://localhost:8000/login/')
#             break
#         except Exception:
#             time.sleep(1)

# def before_scenario(context, scenario):
#     chrome_options = Options()
#     chrome_options.add_argument('--no-sandbox')
#     chrome_options.add_argument('--disable-dev-shm-usage')
#     chrome_options.add_argument('--headless')  # opcional
#     chrome_options.set_capability("browserName", "chrome")

#     context.driver = webdriver.Remote(
#         command_executor='http://localhost:4444/wd/hub',
#         options=chrome_options
#     )
#     # context.driver = webdriver.Chrome()


# def after_scenario(context, scenario):
#     try:
#         context.driver.quit()
#     except WebDriverException as e:
#         print(f"⚠️  Error al cerrar el navegador: {e}")
