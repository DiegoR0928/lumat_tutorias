# lumat_app/middleware.py
from django.shortcuts import redirect
from django.urls import reverse

class CompletarPerfilMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # 1. Si el usuario no está autenticado, continuar normal
        if not request.user.is_authenticated:
            return self.get_response(request)

        # 2. Verificar si es un alumno
        if request.user.groups.filter(name='Alumno').exists():
            # Usamos getattr/hasattr para evitar excepciones si el objeto alumno no existe
            alumno = getattr(request.user, 'alumno', None)

            if alumno and not alumno.perfil_completado:
                # Rutas permitidas a las que sí puede acceder sin completar el perfil
                rutas_permitidas = [
                    reverse('lumat_app:perfil_alumno'),
                    reverse('lumat_app:logout'),  # O el name de tu vista de logout
                ]

                # Permitir archivos estáticos/media y las rutas autorizadas
                path = request.path
                if path not in rutas_permitidas and not path.startswith('/static/') and not path.startswith('/media/'):
                    return redirect('lumat_app:perfil_alumno')

        return self.get_response(request)