from django.contrib.auth import get_user_model
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lumat_tutorias.settings')
django.setup()


User = get_user_model()

username = 'admin'
email = 'admin@example.com'
password = 'admin1234'

if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(
        username=username, email=email, password=password)
    print(f'Superusuario "{username}" creado.')
else:
    print(f'El usuario "{username}" ya existe.')
