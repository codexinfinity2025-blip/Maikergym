from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import redirect, render
from django.core.exceptions import ValidationError
from .models import PerfilUsuario, EstadoAsignacionChoice, ModalidadRutinaChoice
from .services import crear_rutina_automatica


class PreferenciasForm(forms.ModelForm):
    peso = forms.DecimalField(label='Peso actual (kg)', min_value=1, max_value=500, max_digits=5, decimal_places=2)
    altura_cm = forms.DecimalField(label='Altura (cm)', min_value=50, max_value=250, max_digits=5, decimal_places=2)

    class Meta:
        model = PerfilUsuario
        fields = ['peso', 'altura_cm', 'genero', 'enfoque_corporal']
        labels = {'genero': 'Sexo / género del perfil', 'enfoque_corporal': 'Enfoque de entrenamiento'}
        widgets = {'enfoque_corporal': forms.RadioSelect}


@login_required
@transaction.atomic
def preferencias(request):
    perfil = PerfilUsuario.objects.select_for_update().get(user=request.user)
    asignacion = request.user.planes_asignados.filter(estado=EstadoAsignacionChoice.ACTIVO).first()
    iniciada = bool(asignacion and asignacion.sesiones.exists())
    form = PreferenciasForm(request.POST or None, instance=perfil)
    if request.method == 'POST' and form.is_valid():
        cambio = 'enfoque_corporal' in form.changed_data
        try:
            with transaction.atomic():
                nuevo = form.save(commit=False)
                nuevo.priorizar_tren_inferior = nuevo.enfoque_corporal == 'inferior'
                nuevo.save()
                # La rutina manual es propiedad del usuario: actualizar peso,
                # altura o enfoque no puede sustituirla por una recomendación.
                if (
                    cambio and asignacion and not iniciada
                    and perfil.modalidad_rutina == ModalidadRutinaChoice.AUTOMATICA
                ):
                    crear_rutina_automatica(request.user, perfil.objetivo, perfil.nivel_entrenamiento,
                        perfil.dias_entrenamiento, perfil.duracion_sesion_minutos,
                        perfil.descanso_preferido_segundos, minutos_por_dia=perfil.minutos_por_dia,
                        enfoque_corporal=perfil.enfoque_corporal)
        except ValidationError as error:
            form.add_error(None, error)
        else:
            messages.success(request, 'Datos guardados. Tu historial se conserva.' + (' El nuevo enfoque se aplicará al configurar tu próxima rutina.' if iniciada and cambio else ''))
            return redirect('preferencias')
    return render(request, 'preferencias.html', {'form': form, 'iniciada': iniciada, 'perfil': perfil})
