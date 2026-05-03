from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from . import views
from .views import CustomLoginView, CustomLogoutView

app_name = 'lumat_app'


urlpatterns = [
    path('registro/', views.registro, name='registro'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', CustomLogoutView.as_view(), name='logout'),
    path('alumno/', views.alumno_dashboard, name='alumno_dashboard'),
    path('docente/', views.docente_dashboard, name='docente_dashboard'),

    path('alumno/seminario/', views.seminario, name='seminario'),
    path('alumno/perfil/', views.perfil, name='perfil'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
