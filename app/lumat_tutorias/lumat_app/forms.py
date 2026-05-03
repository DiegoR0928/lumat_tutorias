from django import forms
from django.contrib.auth.models import User
from .models import Alumno


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
