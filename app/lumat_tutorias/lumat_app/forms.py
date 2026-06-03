from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import PasswordChangeForm
from .models import Alumno, FormularioComite, Docente 
from .models import ActaAlumnoData


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


class DocenteForm(forms.ModelForm):
    class Meta:
        model = Docente
        fields = ['nombre', 'apellido_paterno', 'apellido_materno', 'correo', 'firma']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'apellido_paterno': forms.TextInput(attrs={'class': 'form-control'}),
            'apellido_materno': forms.TextInput(attrs={'class': 'form-control'}),
            'correo': forms.EmailInput(attrs={'class': 'form-control'}),
            'firma': forms.FileInput(attrs={'class': 'form-control-file'}),
        }

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

class ActaAlumnoForm(forms.Form):
    """Formulario para que el alumno llene su informe semestral."""

    actividad_principal = forms.CharField(
        label="Actividad principal durante el semestre",
        widget=forms.TextInput(attrs={
            "class": "acta-input",
            "placeholder": "Ej: Investigación, Redacción de tesis, Cursos...",
            "maxlength": 200,
        }),
    )

    reuniones_tutor = forms.IntegerField(
        label="Reuniones con tutor principal",
        min_value=0,
        max_value=99,
        initial=0,
        widget=forms.NumberInput(attrs={
            "class": "acta-input acta-input--sm",
            "min": 0,
            "max": 99,
        }),
    )

    reuniones_comite = forms.IntegerField(
        label="Reuniones con comité tutor",
        min_value=0,
        max_value=99,
        initial=0,
        widget=forms.NumberInput(attrs={
            "class": "acta-input acta-input--sm",
            "min": 0,
            "max": 99,
        }),
    )

    coloquios = forms.IntegerField(
        label="Asistencias al coloquio",
        min_value=0,
        max_value=99,
        initial=0,
        widget=forms.NumberInput(attrs={
            "class": "acta-input acta-input--sm",
            "min": 0,
            "max": 99,
        }),
    )

    cursos = forms.CharField(
        label="Cursos inscritos",
        required=False,
        widget=forms.Textarea(attrs={
            "class": "acta-textarea",
            "rows": 3,
            "placeholder": "Lista los cursos que inscribiste este semestre, o escribe 'Ninguno'.",
        }),
    )

    articulos = forms.CharField(
        label="Artículos enviados / publicados",
        required=False,
        widget=forms.Textarea(attrs={
            "class": "acta-textarea",
            "rows": 4,
            "placeholder": "Título de cada artículo, uno por línea. Si no tienes, déjalo en blanco.",
        }),
    )

    eventos = forms.CharField(
        label="Eventos académicos / estancias de investigación",
        required=False,
        widget=forms.Textarea(attrs={
            "class": "acta-textarea",
            "rows": 3,
            "placeholder": "Congresos, talleres, estancias, etc. Si no asististe, déjalo en blanco.",
        }),
    )

    plan_siguiente = forms.CharField(
        label="Plan de actividades para el siguiente semestre",
        widget=forms.Textarea(attrs={
            "class": "acta-textarea",
            "rows": 3,
            "placeholder": "Describe brevemente qué planeas realizar el próximo semestre.",
        }),
    )

    comentarios = forms.CharField(
        label="Comentarios adicionales",
        required=False,
        widget=forms.Textarea(attrs={
            "class": "acta-textarea",
            "rows": 3,
            "placeholder": "Cualquier observación adicional (opcional).",
        }),
    )