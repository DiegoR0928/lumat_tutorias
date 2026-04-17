from django.contrib import admin
from .models import Alumno, Docente, Comite, Seminario, CalifSeminario  

# Register your models here.
admin.site.register(Alumno)
admin.site.register(Docente)
admin.site.register(Comite)
admin.site.register(Seminario)
admin.site.register(CalifSeminario)
