from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import PasswordChangeForm
from .models import Alumno, FormularioComite


class UserForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['username', 'email', 'password']


class AlumnoForm(forms.ModelForm):

    class Meta:
        model = Alumno
        fields = [
            'nombre',
            'apellido_paterno',
            'apellido_materno',
        ]


class AlumnoEditForm(forms.ModelForm):

    class Meta:
        model = Alumno
        fields = [
            'matricula',
            'nombre',
            'apellido_paterno',
            'apellido_materno',
            'correo',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'alumno-input'})


class PasswordChangeCustomForm(PasswordChangeForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'alumno-input'})


class FormularioComiteForm(forms.ModelForm):
    """Sólo el tutor llena el contenido del informe."""
    class Meta:
        model = FormularioComite
        fields = [
            'el_comite_encuentra',
            'observaciones',
            'dictamen',
            'propuestas',
        ]
        labels = {
            'el_comite_encuentra': 'El Comité encuentra que el estudiante',
            'observaciones': 'Otros aspectos observados por el Comité',
            'dictamen': 'Dictamen',
            'propuestas': 'Plan de trabajo propuesto',
        }
        widgets = {
            'el_comite_encuentra': forms.Textarea(attrs={'rows': 3}),
            'observaciones': forms.Textarea(attrs={'rows': 3}),
            'dictamen': forms.Textarea(attrs={'rows': 2}),
            'propuestas': forms.Textarea(attrs={'rows': 3}),
        }


class FirmaCalificacionForm(forms.Form):
    """Cada miembro del comité firma y asigna su calificación."""
    calificacion = forms.DecimalField(
        max_digits=4,
        decimal_places=2,
        min_value=0,
        max_value=10,
        label='Calificación (0 – 10)',
    )
    confirmar_firma = forms.BooleanField(
        label='Confirmo mi firma y calificación',
        required=True,
    )
