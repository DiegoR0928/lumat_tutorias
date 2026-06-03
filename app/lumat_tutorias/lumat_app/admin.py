from django import forms
from django.contrib import admin
from django.contrib.auth.models import User, Group
from unfold.admin import ModelAdmin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import Alumno, Docente, Comite, Seminario


def asignar_grupo(user, nombre_grupo):
    grupo, _ = Group.objects.get_or_create(name=nombre_grupo)
    user.groups.add(grupo)


try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass


@admin.register(User)
class CustomUserAdmin(BaseUserAdmin, ModelAdmin):
    list_display = (
        "username", "email", "first_name",
        "last_name", "obtener_rol", "is_staff"
    )
    list_filter = ("groups", "is_staff", "is_superuser", "is_active")

    def obtener_rol(self, obj):
        if obj.is_superuser:
            return "Administrador"
        if obj.groups.filter(name='Docente').exists():
            return "Docente"
        elif obj.groups.filter(name='Alumno').exists():
            return "Alumno"
        return "Sin Rol / Personal"

    obtener_rol.short_description = "Tipo de Usuario"

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class AlumnoForm(forms.ModelForm):
    username = forms.CharField(
        max_length=150, required=False, label="Usuario (Para iniciar sesión)"
    )
    password = forms.CharField(
        widget=forms.PasswordInput, required=False, label="Contraseña",
        help_text="Déjalo en blanco al editar si no deseas cambiarla."
    )

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
            {'class': clases_input, 'placeholder': 'Ej. dalba'}
        )
        self.fields['password'].widget.attrs.update(
            {'class': clases_input, 'placeholder': '••••••••'}
        )

        if self.instance and self.instance.pk:
            if self.instance.user:
                self.fields['username'].initial = self.instance.user.username
            self.fields['username'].widget.attrs['readonly'] = True
            self.fields['username'].widget.attrs['class'] = (
                clases_input + " bg-gray-100 cursor-not-allowed"
            )

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
            user = User.objects.create_user(
                username=self.cleaned_data['username'],
                password=self.cleaned_data['password'],
                email=self.cleaned_data.get('correo', '')
            )
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
        max_length=150, required=False, label="Usuario (Para iniciar sesión)"
    )
    password = forms.CharField(
        widget=forms.PasswordInput, required=False, label="Contraseña",
        help_text="Déjalo en blanco al editar si no deseas cambiarla."
    )

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
            {'class': clases_input, 'placeholder': 'Ej. dalba'}
        )
        self.fields['password'].widget.attrs.update(
            {'class': clases_input, 'placeholder': '••••••••'}
        )

        if self.instance and self.instance.pk:
            if self.instance.user:
                self.fields['username'].initial = self.instance.user.username
            self.fields['username'].widget.attrs['readonly'] = True
            self.fields['username'].widget.attrs['class'] = (
                clases_input + " bg-gray-100 cursor-not-allowed"
            )

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
            user = User.objects.create_user(
                username=self.cleaned_data['username'],
                password=self.cleaned_data['password'],
                email=self.cleaned_data.get('correo', '')
            )
            asignar_grupo(user, "Docente")
            docente.user = user
        else:
            if self.cleaned_data.get('password'):
                docente.user.set_password(self.cleaned_data['password'])
                docente.user.save()
        if commit:
            docente.save()
        return docente


@admin.register(Alumno)
class AlumnoAdmin(ModelAdmin):
    form = AlumnoForm
    list_display = (
        'matricula', 'nombre', 'apellido_paterno',
        'apellido_materno', 'user', 'semestre', 'correo'
    )
    search_fields = ('matricula', 'nombre', 'apellido_paterno', 'correo')
    list_filter = ('semestre',)

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if obj.user:
            user = obj.user
            user.first_name = obj.nombre if hasattr(obj, 'nombre') else ""
            user.last_name = obj.apellido_paterno if hasattr(
                obj, 'apellido_paterno') else ""
            user.save(update_fields=['first_name', 'last_name'])

    def delete_model(self, request, obj):
        user = obj.user
        super().delete_model(request, obj)
        if user:
            user.delete()

    def delete_queryset(self, request, queryset):
        usuarios_a_borrar = [obj.user for obj in queryset if obj.user]
        super().delete_queryset(request, queryset)
        for user in usuarios_a_borrar:
            user.delete()


@admin.register(Docente)
class DocenteAdmin(ModelAdmin):
    form = DocenteForm
    list_display = ("nombre", "apellido_paterno", "user", "correo")

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if obj.user:
            user = obj.user
            user.first_name = obj.nombre if hasattr(obj, 'nombre') else ""
            user.last_name = obj.apellido_paterno if hasattr(
                obj, 'apellido_paterno') else ""
            user.save(update_fields=['first_name', 'last_name'])

    def delete_model(self, request, obj):
        user = obj.user
        super().delete_model(request, obj)
        if user:
            user.delete()

    def delete_queryset(self, request, queryset):
        usuarios_a_borrar = [obj.user for obj in queryset if obj.user]
        super().delete_queryset(request, queryset)
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
    exclude = ('fecha', 'hora')


admin.site.unregister(Group)
