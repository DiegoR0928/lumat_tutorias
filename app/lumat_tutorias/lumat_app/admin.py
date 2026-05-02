from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import Alumno, Docente, Comite, Seminario, CalifSeminario

@admin.register(Alumno)
class AlumnoAdmin(ModelAdmin):
    # Muestra estas columnas en la tabla principal
    list_display = ('matricula', 'nombre', 'apellido_paterno', 'apellido_materno', 'semestre', 'correo')
    # Añade una barra de búsqueda por estos campos
    search_fields = ('matricula', 'nombre', 'apellido_paterno', 'correo')
    # Añade un panel lateral para filtrar por semestre
    list_filter = ('semestre',)

@admin.register(Docente)
class DocenteAdmin(ModelAdmin):
    list_display = ('nombre', 'apellido_paterno', 'apellido_materno', 'correo')
    search_fields = ('nombre', 'apellido_paterno', 'correo')

@admin.register(Comite)
class ComiteAdmin(ModelAdmin):
    list_display = ('tutor', 'miembro1', 'miembro2')
    # Para buscar por el nombre del tutor (usando la relación ForeignKey)
    search_fields = ('tutor__nombre', 'tutor__apellido_paterno')

@admin.register(Seminario)
class SeminarioAdmin(ModelAdmin):
    list_display = ('alumno', 'fecha', 'hora', 'calificacion')
    list_filter = ('fecha', 'comite')
    # Para buscar por los datos del alumno relacionado
    search_fields = ('alumno__nombre', 'alumno__matricula')

@admin.register(CalifSeminario)
class CalifSeminarioAdmin(ModelAdmin):
    list_display = ('seminario', 'docente', 'calificacion')
    list_filter = ('docente',)