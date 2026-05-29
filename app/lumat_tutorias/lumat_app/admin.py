from django import forms
from django.contrib import admin
from django.contrib.auth.models import User, Group
from unfold.admin import ModelAdmin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import Alumno, Docente, Comite, Seminario

# Función auxiliar para evitar repetir código


def asignar_grupo(user, nombre_grupo):
    grupo, _ = Group.objects.get_or_create(name=nombre_grupo)
    user.groups.add(grupo)

# ==========================================
# 1. FORMULARIOS PERSONALIZADOS
# ==========================================


# 1. Desregistramos el admin por defecto de Django para poder meter el nuestro
try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass

# 2. Creamos el nuevo administrador personalizado con Unfold


@admin.register(User)
class CustomUserAdmin(BaseUserAdmin, ModelAdmin):
    # Agregamos 'obtener_rol' al list_display para que aparezca como columna
    list_display = ("username", "email", "first_name",
                    "last_name", "obtener_rol", "is_staff")

    # Permitimos que se pueda filtrar la lista de usuarios por su rol/grupo
    list_filter = ("groups", "is_staff", "is_superuser", "is_active")

    def obtener_rol(self, obj):
        """
        Calcula dinámicamente el rol del usuario para mostrarlo en la tabla.
        """
        if obj.is_superuser:
            return "Administrador"

        # Verificamos por medio de los grupos de Django
        if obj.groups.filter(name='Docente').exists():
            return "Docente"
        elif obj.groups.filter(name='Alumno').exists():
            return "Alumno"

        return "Sin Rol / Personal"

    # Le ponemos un título bonito a la cabecera de la columna en el panel
    obtener_rol.short_description = "Tipo de Usuario"


class AlumnoForm(forms.ModelForm):
    username = forms.CharField(
        max_length=150, required=False, label="Usuario (Para iniciar sesión)")
    password = forms.CharField(widget=forms.PasswordInput, required=False,
                               label="Contraseña",
                               help_text="Déjalo en blanco al editar si no"
                               " deseas cambiarla.")

    class Meta:
        model = Alumno
        exclude = ['user']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        clases_input = (
            "border border-gray-300 rounded-md p-2 bg-white text-gray-900 "
            "focus:border-[#4a7c7a] focus:ring-1 focus:ring-[#4a7c7a] "
            "w-full block"
        )

        self.fields['username'].widget.attrs.update(
            {'class': clases_input, 'placeholder': 'Ej. dalba'})
        self.fields['password'].widget.attrs.update(
            {'class': clases_input, 'placeholder': '••••••••'})

        if self.instance and self.instance.pk:
            if self.instance.user:
                self.fields['username'].initial = self.instance.user.username
            self.fields['username'].widget.attrs['readonly'] = True
            self.fields['username'].widget.attrs['class'] = clases_input + \
                " bg-gray-100 cursor-not-allowed"

    def clean(self):
        cleaned_data = super().clean()
        if not self.instance.pk:
            username = cleaned_data.get('username')
            if not username:
                self.add_error(
                    'username', 'El nombre de usuario es obligatorio.')
            elif User.objects.filter(username=username).exists():
                self.add_error(
                    'username', 'Este nombre de usuario ya está ocupado.')

            if not cleaned_data.get('password'):
                self.add_error('password', 'La contraseña es obligatoria.')
        return cleaned_data

    def save(self, commit=True):
        alumno = super().save(commit=False)

        if not alumno.pk:
            # Creación del usuario
            user = User.objects.create_user(
                username=self.cleaned_data['username'],
                password=self.cleaned_data['password'],
                email=self.cleaned_data.get('correo', '')
            )
            # ASIGNACIÓN AUTOMÁTICA AL GRUPO ALUMNO
            asignar_grupo(user, "Alumno")
            alumno.user = user
        else:
            if self.cleaned_data.get('password'):
                alumno.user.set_password(self.cleaned_data['password'])
                alumno.user.save()

        if commit:
            alumno.save()
        return alumno


class DocenteForm(forms.ModelForm):
    username = forms.CharField(
        max_length=150, required=False, label="Usuario (Para iniciar sesión)")
    password = forms.CharField(widget=forms.PasswordInput, required=False,
                               label="Contraseña",
                               help_text="Déjalo en blanco al editar si no "
                               "deseas cambiarla.")

    class Meta:
        model = Docente
        exclude = ['user']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        clases_input = (
            "border border-gray-300 rounded-md p-2 bg-white text-gray-900 "
            "focus:border-[#4a7c7a] focus:ring-1 focus:ring-[#4a7c7a] "
            "w-full block"
        )

        self.fields['username'].widget.attrs.update(
            {'class': clases_input, 'placeholder': 'Ej. dalba'})
        self.fields['password'].widget.attrs.update(
            {'class': clases_input, 'placeholder': '••••••••'})

        if self.instance and self.instance.pk:
            if self.instance.user:
                self.fields['username'].initial = self.instance.user.username
            self.fields['username'].widget.attrs['readonly'] = True
            self.fields['username'].widget.attrs['class'] = clases_input + \
                " bg-gray-100 cursor-not-allowed"

    def clean(self):
        cleaned_data = super().clean()
        if not self.instance.pk:
            username = cleaned_data.get('username')
            if not username:
                self.add_error(
                    'username', 'El nombre de usuario es obligatorio.')
            elif User.objects.filter(username=username).exists():
                self.add_error(
                    'username', 'Este nombre de usuario ya está en uso.')

            if not cleaned_data.get('password'):
                self.add_error('password', 'La contraseña es obligatoria.')
        return cleaned_data

    def save(self, commit=True):
        docente = super().save(commit=False)
        if not docente.pk:
            # Creación del usuario
            user = User.objects.create_user(
                username=self.cleaned_data['username'],
                password=self.cleaned_data['password'],
                email=self.cleaned_data.get('correo', '')
            )
            # ASIGNACIÓN AUTOMÁTICA AL GRUPO DOCENTE
            asignar_grupo(user, "Docente")
            docente.user = user
        else:
            if self.cleaned_data.get('password'):
                docente.user.set_password(self.cleaned_data['password'])
                docente.user.save()
        if commit:
            docente.save()
        return docente

# ==========================================
# 2. REGISTRO EN EL PANEL (UNFOLD)
# ==========================================


@admin.register(Alumno)
class AlumnoAdmin(ModelAdmin):
    form = AlumnoForm
    list_display = ('matricula', 'nombre', 'apellido_paterno',
                    'apellido_materno', 'user', 'semestre', 'correo')
    search_fields = ('matricula', 'nombre', 'apellido_paterno', 'correo')
    list_filter = ('semestre',)

    def save_model(self, request, obj, form, change):
        """
        Detecta cuando el Administrador guarda o edita un Alumno
        y fuerza la sincronización de nombres en la tabla auth_user.
        """
        super().save_model(request, obj, form, change)

        # 2. Si el alumno tiene un usuario de Django asociado,
        # actualizamos sus nombres
        if obj.user:
            user = obj.user

            # Sacamos los datos de los campos correspondientes de tu
            # modelo Alumno
            # Asegúrate de que coincidan exactamente con los nombres
            # de tus campos
            # en models.py
            user.first_name = obj.nombre if hasattr(obj, 'nombre') else ""
            user.last_name = obj.apellido_paterno if hasattr(
                obj, 'apellido_paterno') else ""

            # Forzamos el guardado directamente en la base de datos
            # (tabla auth_user)
            user.save(update_fields=['first_name', 'last_name'])

    def delete_model(self, request, obj):
        """Al borrar un Alumno, elimina primero su cuenta en auth_user."""
        user = obj.user
        # Primero borramos el alumno
        super().delete_model(request, obj)
        # Si tenía un usuario asignado, lo eliminamos de auth_user
        if user:
            user.delete()

    def delete_queryset(self, request, queryset):
        """
            Maneja el borrado en lote desde la lista del panel de
            administración.
        """
        # Almacenamos una lista de los usuarios vinculados antes de romper
        # la relación
        usuarios_a_borrar = [obj.user for obj in queryset if obj.user]

        # Ejecutamos el borrado en lote de los Alumnos
        super().delete_queryset(request, queryset)

        # Ahora eliminamos todos los usuarios correspondientes en auth_user
        for user in usuarios_a_borrar:
            user.delete()


@admin.register(Docente)
class DocenteAdmin(ModelAdmin):
    # Ajusta estas columnas según los campos reales de tu modelo Docente
    list_display = ("nombre", "apellido_paterno", "user", "correo")

    # === 1. Sincronización al guardar/editar desde el Admin ===
    def save_model(self, request, obj, form, change):
        """Sincroniza el nombre del Docente con la tabla
        auth_user al crear/editar."""
        super().save_model(request, obj, form, change)

        if obj.user:
            user = obj.user
            # Sacamos los datos de los campos de tu modelo Docente
            user.first_name = obj.nombre if hasattr(obj, 'nombre') else ""
            user.last_name = obj.apellido_paterno if hasattr(
                obj, 'apellido_paterno') else ""
            user.save(update_fields=['first_name', 'last_name'])

    # === 2. Borrado individual ===
    def delete_model(self, request, obj):
        """Al borrar un Docente, elimina también su cuenta
        de usuario asociada."""
        user = obj.user
        super().delete_model(request, obj)
        if user:
            user.delete()

    # === 3. Borrado en lote (Selección múltiple) ===
    def delete_queryset(self, request, queryset):
        """Maneja el borrado de múltiples docentes y limpia sus
        cuentas en auth_user."""
        # Guardamos los usuarios antes de que el queryset de docentes
        # sea eliminado
        usuarios_a_borrar = [obj.user for obj in queryset if obj.user]

        # Eliminamos los registros de la tabla Docente
        super().delete_queryset(request, queryset)

        # Eliminamos de forma segura las cuentas de usuario huérfanas
        for user in usuarios_a_borrar:
            user.delete()


@admin.register(Comite)
class ComiteAdmin(ModelAdmin):
    list_display = ('id', 'tutor', 'miembro1', 'miembro2')
    search_fields = ('tutor__nombre', 'tutor__apellido_paterno')


@admin.register(Seminario)
class SeminarioAdmin(ModelAdmin):
    list_display = ('alumno', 'fecha', 'hora', 'calificacion')
    list_filter = ('fecha', 'comite')
    search_fields = ('alumno__nombre', 'alumno__matricula')



# QUITAR GRUPOS DE ADMIN
admin.site.unregister(Group)
