from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from . import views, views_docente
from .views import CustomLoginView, CustomLogoutView

app_name = 'lumat_app'


urlpatterns = [
     path('registro/', views.registro, name='registro'),
     path('login/', CustomLoginView.as_view(), name='login'),
     path('logout/', CustomLogoutView.as_view(), name='logout'),
     #     path('alumno/', views.alumno_dashboard, name='alumno_dashboard'),
     #     path('docente/', views.docente_dashboard, name='docente_dashboard'),
     path('docente/seminarios/', views_docente.docente_seminarios,
          name='docente_seminarios'),
     path('docente/seminarios/<int:seminario_id>/',
          views_docente.docente_seminario_detalle,
          name='docente_seminario_detalle',
          ),
     path('docente/seminarios/<int:seminario_id>/firmar/',
          views_docente.docente_firmar_seminario,
          name='docente_firmar_seminario'),

     path('docente/seminarios/<int:seminario_id>/acta/',
          views_docente.docente_descargar_acta,
          name='docente_descargar_acta'),

     path(
          'docente/seminarios/<int:seminario_id>/descargar-evidencias/',
          views_docente.descargar_evidencias_zip,
          name='docente_descargar_evidencias_zip'
     ),

     #   path('alumno/seminario/', views.seminario, name='seminario'),
     path('alumno/seminario/<int:num>/',
          views.seminario_detalle, name='seminario_detalle'),
     path('alumno/seminario/<int:seminario_id>/evidencia/',
          views.subir_evidencia, name='subir_evidencia'),

     path('alumno/seminario/<int:num>/acta/', views.generar_acta_view, name='generar_acta'),

     path('alumno/tutor/cambio/', views.cambio_tutor, name='cambio_tutor'),

     path('alumno/perfil/', views.perfil_alumno, name='perfil_alumno'),
     ]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
