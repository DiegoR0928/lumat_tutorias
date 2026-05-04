from django.shortcuts import render, redirect
from django.contrib.auth.models import Group
from django.contrib.auth import update_session_auth_hash
from .forms import UserForm, AlumnoForm
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.decorators import user_passes_test
# from django.http import HttpResponse
from django.contrib import messages
from .forms import AlumnoEditForm, PasswordChangeCustomForm


def registro(request):
    if request.method == 'POST':
        user_form = UserForm(request.POST)
        alumno_form = AlumnoForm(request.POST)

        if user_form.is_valid() and alumno_form.is_valid():
            user = user_form.save(commit=False)
            user.set_password(user_form.cleaned_data['password'])
            user.save()

            grupo = Group.objects.get(name='Alumno')
            user.groups.add(grupo)

            alumno = alumno_form.save(commit=False)
            alumno.user = user
            alumno.save()

            messages.success(
                request,
                "Alumno registrado con éxito"
            )

            return redirect('lumat_app:registro')
    else:
        user_form = UserForm()
        alumno_form = AlumnoForm()

    return render(request, 'registro.html', {
        'user_form': user_form,
        'alumno_form': alumno_form
    })


class CustomLoginView(LoginView):
    template_name = 'login.html'

    def get_success_url(self):
        user = self.request.user

        if user.groups.filter(name='Docente').exists():
            return '/docente/'
        elif user.groups.filter(name='Alumno').exists():
            return '/alumno/'

        return '/'


class CustomLogoutView(LogoutView):
    next_page = 'lumat_app:login'


def es_docente(user):
    return user.groups.filter(name='Docente').exists()


def es_alumno(user):
    return user.groups.filter(name='Alumno').exists()


@user_passes_test(es_docente)
def docente_dashboard(request):
    return render(request, 'docente_dashboard.html')


@user_passes_test(es_alumno)
def alumno_dashboard(request):
    return render(request, 'alumno_dashboard.html')


def seminario(request):
    return render(request, 'alumno_seminario.html', {
        'fecha_seminario': '15 de mayo de 2026'
    })


# @login_required(login_url='/login/')
def perfil_alumno(request):
    alumno = request.user.alumno
    editando = request.GET.get('modo')  # 'perfil' | 'password' | None

    if request.method == 'GET':
        return _render_perfil(
            request, alumno,
            editando=editando,
            alumno_form=AlumnoEditForm(instance=alumno),
            password_form=PasswordChangeCustomForm(user=request.user),
        )

    accion = request.POST.get('accion')

    if accion == 'perfil':
        return _guardar_perfil(request, alumno)

    if accion == 'password':
        return _cambiar_password(request, alumno)

    return redirect('lumat_app:perfil_alumno')


def _render_perfil(request, alumno, editando, alumno_form, password_form):
    return render(request, 'alumno_perfil.html', {
        'alumno': alumno,
        'alumno_form': alumno_form,
        'password_form': password_form,
        'editando': editando,
    })


def _guardar_perfil(request, alumno):
    alumno_form = AlumnoEditForm(request.POST, instance=alumno)
    password_form = PasswordChangeCustomForm(user=request.user)

    if alumno_form.is_valid():
        alumno_form.save()
        messages.success(request, 'Perfil actualizado exitosamente')
        return redirect('lumat_app:perfil_alumno')

    messages.error(
        request, 'Datos inválidos, por favor verifica la información')

    return _render_perfil(
        request, alumno, editando='perfil',
        alumno_form=alumno_form,
        password_form=password_form,
    )


def _cambiar_password(request, alumno):
    alumno_form = AlumnoEditForm(instance=alumno)
    password_form = PasswordChangeCustomForm(
        user=request.user, data=request.POST)

    if password_form.is_valid():
        password_form.save()
        update_session_auth_hash(request, password_form.user)
        messages.success(request, 'Contraseña actualizada exitosamente')
        return redirect('lumat_app:perfil_alumno')

    return _render_perfil(
        request, alumno, editando='password',
        alumno_form=alumno_form,
        password_form=password_form,
    )
