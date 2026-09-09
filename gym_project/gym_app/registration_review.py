from datetime import date
from django import forms
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db import transaction, IntegrityError
from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods
from django.views.decorators.debug import sensitive_post_parameters
from .models import PerfilUsuario


class RevisionRegistroForm(forms.Form):
    nombre = forms.CharField(max_length=150)
    apellido = forms.CharField(max_length=150)
    email = forms.EmailField(label='Correo electrónico')
    fecha_nacimiento = forms.DateField(label='Fecha de nacimiento', widget=forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'))
    telefono = forms.CharField(label='Teléfono', max_length=20, required=False)
    direccion = forms.CharField(label='Dirección', max_length=200, required=False)
    enfoque_corporal = forms.ChoiceField(label='¿Dónde quieres enfocar tu entrenamiento?', choices=PerfilUsuario._meta.get_field('enfoque_corporal').choices)
    password_actual = forms.CharField(label='Contraseña actual (solo si cambias el correo)', required=False, widget=forms.PasswordInput(attrs={'autocomplete': 'current-password'}))

    def __init__(self, *args, user, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_fecha_nacimiento(self):
        value = self.cleaned_data['fecha_nacimiento']
        if value > date.today():
            raise forms.ValidationError('La fecha no puede estar en el futuro.')
        return value

    def clean(self):
        data = super().clean()
        email = data.get('email', '').lower()
        data['email'] = email
        if email and email != self.user.email.lower():
            if not self.user.check_password(data.get('password_actual', '')):
                self.add_error('password_actual', 'Confirma tu contraseña actual para cambiar el correo.')
            if User.objects.exclude(pk=self.user.pk).filter(email__iexact=email).exists() or User.objects.exclude(pk=self.user.pk).filter(username__iexact=email).exists():
                self.add_error('email', 'Ese correo no está disponible.')
        return data


@login_required
@require_http_methods(['GET', 'POST'])
@sensitive_post_parameters('password_actual')
def revisar_registro(request):
    perfil = PerfilUsuario.objects.get(user=request.user)
    initial = {key: getattr(perfil, key) for key in ('fecha_nacimiento', 'telefono', 'direccion', 'enfoque_corporal')}
    initial.update(nombre=request.user.first_name, apellido=request.user.last_name, email=request.user.email)
    form = RevisionRegistroForm(request.POST if request.method == 'POST' else None, initial=initial, user=request.user)
    if request.method == 'POST' and form.is_valid():
        try:
            with transaction.atomic():
                user = User.objects.select_for_update().get(pk=request.user.pk)
                perfil = PerfilUsuario.objects.select_for_update().get(user=user)
                data = form.cleaned_data
                user.first_name, user.last_name = data['nombre'], data['apellido']
                if user.email.lower() != data['email']:
                    user.email = user.username = data['email']
                user.save(update_fields=['first_name', 'last_name', 'email', 'username'])
                for key in ('fecha_nacimiento', 'telefono', 'direccion', 'enfoque_corporal'):
                    setattr(perfil, key, data[key])
                today, birth = date.today(), data['fecha_nacimiento']
                perfil.edad = today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))
                perfil.priorizar_tren_inferior = data['enfoque_corporal'] == 'inferior'
                perfil.save(update_fields=['fecha_nacimiento', 'telefono', 'direccion', 'enfoque_corporal', 'edad', 'priorizar_tren_inferior'])
        except IntegrityError:
            form.add_error('email', 'Ese correo no está disponible.')
        else:
            return redirect('objetivo')
    return render(request, 'revisar_registro.html', {'form': form})
