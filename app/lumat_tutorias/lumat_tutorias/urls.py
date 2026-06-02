"""
URL configuration for lumat_tutorias project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.urls import include
from django.conf import settings
from django.conf.urls.static import static

from lumat_app.views import admin_calendario_formulario_view, admin_cambio_tutor_view
from lumat_app.views import admin_calendario_generar_pdf_view
from lumat_app.views import admin_estadisticas_view


urlpatterns = [
    path(
        'admin/calendar-generator/',
        admin.site.admin_view(admin_calendario_formulario_view),
        name='calendar_form'
    ),
    path(
        'admin/calendar-generator/generate/',
        admin.site.admin_view(admin_calendario_generar_pdf_view),
        name='calendar_pdf'
    ),
    path('admin/estadisticas/', admin.site.admin_view(admin_estadisticas_view),
         name='admin_estadisticas'),
    path('admin/cambio-tutor/', admin.site.admin_view(admin_cambio_tutor_view),
         name='admin_cambio_tutor'),
    path('admin/', admin.site.urls),
    path('', include('lumat_app.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
