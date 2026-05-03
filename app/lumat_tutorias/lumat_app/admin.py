from django import forms
from django.contrib import admin
from django.contrib.auth.models import User
from unfold.admin import ModelAdmin
from .models import Alumno, Docente, Comite, Seminario, CalifSeminario

# ==========================================
# 1. FORMULARIOS PERSONALIZADOS
# ==========================================


class AlumnoForm(forms.ModelForm):
    username = forms.CharField(
        max_length=150, required=False, label="Usuario (Para iniciar sesión)")
    password = forms.CharField(widget=forms.PasswordInput, required=False,
                               label="Contraseña",
                               help_text="Déjalo en blanco al editar si no "
                               "deseas cambiarla.")

    class Meta:
        model = Alumno
        exclude = ['user']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['username'].initial = self.instance.user.username
            self.fields['username'].widget.attrs['readonly'] = True

    def clean(self):
        cleaned_data = super().clean()
        if not self.instance.pk:
            username = cleaned_data.get('username')
            if not username:
                self.add_error(
                    'username', 'El nombre de usuario es obligatorio para '
                    'registrar la cuenta.')
            elif User.objects.filter(username=username).exists():
                self.add_error(
                    'username', 'Este nombre de usuario ya está ocupado. '
                    'Elige otro.')

            if not cleaned_data.get('password'):
                self.add_error(
                    'password', 'La contraseña es obligatoria para nuevos '
                    'alumnos.')
        return cleaned_data

    def save(self, commit=True):
        alumno = super().save(commit=False)

        if not alumno.pk:
            user = User.objects.create_user(
                username=self.cleaned_data['username'],
                password=self.cleaned_data['password'],
                email=self.cleaned_data.get('correo', '')
            )
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
        if self.instance and self.instance.pk:
            self.fields['username'].initial = self.instance.user.username
            self.fields['username'].widget.attrs['readonly'] = True

    def clean(self):
        cleaned_data = super().clean()
        if not self.instance.pk:
            username = cleaned_data.get('username')
            if not username:
                self.add_error(
                    'username', 'El nombre de usuario es obligatorio para '
                    'registrar la cuenta.')
            elif User.objects.filter(username=username).exists():
                self.add_error(
                    'username', 'Este nombre de usuario ya está en uso.')

            if not cleaned_data.get('password'):
                self.add_error(
                    'password', 'La contraseña es obligatoria para nuevos '
                    'docentes.')
        return cleaned_data

    def save(self, commit=True):
        docente = super().save(commit=False)
        if not docente.pk:
            user = User.objects.create_user(
                username=self.cleaned_data['username'],
                password=self.cleaned_data['password'],
                email=self.cleaned_data.get('correo', '')
            )
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
                    'apellido_materno', 'semestre', 'correo')
    search_fields = ('matricula', 'nombre', 'apellido_paterno', 'correo')
    list_filter = ('semestre',)


@admin.register(Docente)
class DocenteAdmin(ModelAdmin):
    form = DocenteForm
    list_display = ('nombre', 'apellido_paterno', 'apellido_materno',
                    'correo')
    search_fields = ('nombre', 'apellido_paterno', 'correo')


@admin.register(Comite)
class ComiteAdmin(ModelAdmin):
    list_display = ('tutor', 'miembro1', 'miembro2')
    search_fields = ('tutor__nombre', 'tutor__apellido_paterno')


@admin.register(Seminario)
class SeminarioAdmin(ModelAdmin):
    list_display = ('alumno', 'fecha', 'hora', 'calificacion')
    list_filter = ('fecha', 'comite')
    search_fields = ('alumno__nombre', 'alumno__matricula')


@admin.register(CalifSeminario)
class CalifSeminarioAdmin(ModelAdmin):
    list_display = ('seminario', 'docente', 'calificacion')
    list_filter = ('docente',)
