from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import PasswordChangeForm
from .models import Alumno, FormularioComite, Docente, SolicitudCambioComite


class UserForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['username', 'email', 'password']


class AlumnoPerfilForm(forms.ModelForm):
    class Meta:
        model = Alumno
        exclude = [
            'user',
            'semestre',
            'periodo_inicio_estudios',
            'periodo_fin_estudios',
            'estado',
        ]
        widgets = {
            'matricula': forms.TextInput(attrs={'class': 'lumat-input'}),
            'nombre': forms.TextInput(attrs={'class': 'lumat-input'}),
            'apellido_paterno': forms.TextInput(attrs={'class': 'lumat-input'}),
            'apellido_materno': forms.TextInput(attrs={'class': 'lumat-input'}),
            'correo': forms.EmailInput(attrs={'class': 'lumat-input'}),
            'posgrado': forms.Select(attrs={'class': 'lumat-select'}),
            'linea_investigacion': forms.Select(attrs={'class': 'lumat-select'}),
            'nacionalidad': forms.TextInput(attrs={'class': 'lumat-input'}),
            'posgrado_o_universidad_anterior': forms.TextInput(attrs={'class': 'lumat-input'}),
            'proyecto_investigacion': forms.TextInput(attrs={'class': 'lumat-input'}),
            'acta_examen_titulacion': forms.ClearableFileInput(attrs={'class': 'lumat-file'}),
        }

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
        exclude = ['user']
        widgets = {
            'nombre':                    forms.TextInput(attrs={'class': 'lumat-input'}),
            'apellido_paterno':          forms.TextInput(attrs={'class': 'lumat-input'}),
            'apellido_materno':          forms.TextInput(attrs={'class': 'lumat-input'}),
            'correo':                    forms.EmailInput(attrs={'class': 'lumat-input'}),
            'telefono':                  forms.TextInput(attrs={'class': 'lumat-input'}),
            'ultimo_grado_estudio':      forms.TextInput(attrs={'class': 'lumat-input'}),
            'universidad_o_centro':      forms.TextInput(attrs={'class': 'lumat-input'}),
            'facultad_o_instituto':      forms.TextInput(attrs={'class': 'lumat-input'}),
            'red_social_investigacion':  forms.URLInput(attrs={
                'class': 'lumat-input',
                'placeholder': 'https://orcid.org/...'
            }),
            'firma':          forms.ClearableFileInput(attrs={'class': 'lumat-file'}),
            'nombramiento_sni': forms.ClearableFileInput(attrs={'class': 'lumat-file'}),
        }


class FormularioComiteForm(forms.ModelForm):
    """Sólo el tutor llena el contenido del informe."""

    dictamen = forms.ChoiceField(
        choices=[('aprobado', 'Aprobado'), ('reprobado', 'Reprobado')],
        widget=forms.RadioSelect(attrs={'class': 'radio-toggle-dictamen'}),
        initial='aprobado',
        label='Dictamen del Comité'
    )

    ratifica_plan = forms.TypedChoiceField(
        coerce=lambda x: x == 'True' or x is True,
        choices=[
            (True, 'Ratificar el plan de trabajo propuesto por el alumno'),
            (False, 'Modificar / Especificar nuevo plan de trabajo')
        ],
        widget=forms.RadioSelect(attrs={'class': 'radio-toggle-plan'}),
        initial=True,
        required=False,
        label='Plan de trabajo para el siguiente semestre'
    )

    class Meta:
        model = FormularioComite
        fields = [
            'dictamen',
            'el_comite_encuentra',
            'observaciones',
            'ratifica_plan',
            'propuestas',
        ]
        labels = {
            'el_comite_encuentra': 'El Comité encuentra que el estudiante',
            'observaciones': 'Otros aspectos observados por el Comité',
            'propuestas': 'Especificar modificaciones al plan de trabajo',
        }
        widgets = {
            'el_comite_encuentra': forms.Textarea(attrs={'rows': 3, 'class': 'form-control-custom'}),
            'observaciones': forms.Textarea(attrs={'rows': 3, 'class': 'form-control-custom'}),
            'propuestas': forms.Textarea(attrs={
                'rows': 3, 
                'class': 'form-control-custom',
                'placeholder': 'Describa las modificaciones o el plan de trabajo corregido...'
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        dictamen = cleaned_data.get('dictamen')
        ratifica_plan = cleaned_data.get('ratifica_plan')

        if dictamen == 'reprobado':
            # Si está reprobado, limpiamos las observaciones y propuestas
            cleaned_data['el_comite_encuentra'] = ''
            cleaned_data['observaciones'] = ''
            cleaned_data['propuestas'] = ''
        elif dictamen == 'aprobado' and ratifica_plan:
            # Si se ratifica el plan del alumno, no se necesitan modificaciones
            cleaned_data['propuestas'] = ''

        return cleaned_data


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
            "placeholder": (
                "Título de cada artículo, uno por línea. "
                "Si no tienes, déjalo en blanco."
            ),
        }),
    )

    eventos = forms.CharField(
        label="Eventos académicos / estancias de investigación",
        required=False,
        widget=forms.Textarea(attrs={
            "class": "acta-textarea",
            "rows": 3,
            "placeholder": (
                "Congresos, talleres, estancias, etc. Si no asististe, déjalo en blanco."
            ),
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

class RegistroDocenteForm(forms.Form):
    # ── Credenciales ──
    username = forms.CharField(
        max_length=150, label="Usuario",
        widget=forms.TextInput(attrs={'class': 'lumat-input', 'autocomplete': 'off'})
    )
    email = forms.EmailField(
        label="Correo electrónico",
        widget=forms.EmailInput(attrs={'class': 'lumat-input'})
    )
    password1 = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={'class': 'lumat-input'})
    )
    password2 = forms.CharField(
        label="Confirmar contraseña",
        widget=forms.PasswordInput(attrs={'class': 'lumat-input'})
    )

    # ── Datos personales ──
    nombre = forms.CharField(
        max_length=100, label="Nombre(s)",
        widget=forms.TextInput(attrs={'class': 'lumat-input'})
    )
    apellido_paterno = forms.CharField(
        max_length=100, label="Apellido paterno",
        widget=forms.TextInput(attrs={'class': 'lumat-input'})
    )
    apellido_materno = forms.CharField(
        max_length=100, label="Apellido materno",
        widget=forms.TextInput(attrs={'class': 'lumat-input'})
    )
    telefono = forms.CharField(
        max_length=20, label="Teléfono",
        widget=forms.TextInput(attrs={'class': 'lumat-input'})
    )

    # ── Datos académicos ──
    ultimo_grado_estudio = forms.CharField(
        max_length=100, label="Último grado de estudio",
        widget=forms.TextInput(attrs={'class': 'lumat-input'})
    )
    universidad_o_centro = forms.CharField(
        max_length=100, label="Universidad o centro",
        widget=forms.TextInput(attrs={'class': 'lumat-input'})
    )
    facultad_o_instituto = forms.CharField(
        max_length=100, label="Facultad o instituto",
        widget=forms.TextInput(attrs={'class': 'lumat-input'})
    )
    red_social_investigacion = forms.URLField(
        max_length=200, label="Perfil de investigación (URL)",
        widget=forms.URLInput(attrs={
            'class': 'lumat-input',
            'placeholder': 'https://orcid.org/...'
        })
    )

    # ── Archivos ──
    firma = forms.ImageField(
        label="Firma (imagen)",
        widget=forms.ClearableFileInput(attrs={'class': 'lumat-file'})
    )
    nombramiento_sni = forms.FileField(
        label="Nombramiento SNI (PDF)", required=False,
        widget=forms.ClearableFileInput(attrs={'class': 'lumat-file'}),
        help_text="Opcional"
    )

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Este nombre de usuario ya está en uso.")
        return username

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Ya existe una cuenta con este correo.")
        return email

    def clean_nombramiento_sni(self):
        archivo = self.cleaned_data.get('nombramiento_sni')
        if archivo and not archivo.name.endswith('.pdf'):
            raise forms.ValidationError("Solo se permiten archivos PDF.")
        return archivo

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get('password1')
        p2 = cleaned.get('password2')
        if p1 and p2 and p1 != p2:
            self.add_error('password2', "Las contraseñas no coinciden.")
        return cleaned

class SolicitudCambioComiteForm(forms.ModelForm):
    class Meta:
        model = SolicitudCambioComite
        fields = ['rol_solicitado', 'motivo']
        widgets = {
            'rol_solicitado': forms.Select(attrs={'class': 'lumat-select'}),
            'motivo': forms.Textarea(attrs={
                'class': 'lumat-input',
                'rows': 5,
                'placeholder': 'Describe el motivo de la solicitud...',
            }),
        }
        labels = {
            'rol_solicitado': 'Miembro a reemplazar',
            'motivo':         'Motivo de la solicitud',
        }

    def clean_motivo(self):
        motivo = self.cleaned_data.get('motivo', '').strip()
        if len(motivo) < 30:
            raise forms.ValidationError(
                "Por favor proporciona un motivo más detallado (mínimo 30 caracteres)."
            )
        return motivo