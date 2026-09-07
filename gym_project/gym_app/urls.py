from django.urls import path
from gym_project.gym_app import views
from gym_project.gym_app import social_views
from django.contrib.auth import views as auth_views
from .password_reset import RecuperarPassword, ConfirmarPassword

urlpatterns = [
    path('recuperar-contrasena/', RecuperarPassword.as_view(), name='password_reset'),
    path('recuperar-contrasena/enviado/', auth_views.PasswordResetDoneView.as_view(template_name='password_reset_done.html'), name='password_reset_done'),
    path('restablecer/<uidb64>/<token>/', ConfirmarPassword.as_view(), name='password_reset_confirm'),
    path('restablecer/completado/', auth_views.PasswordResetCompleteView.as_view(template_name='password_reset_complete.html'), name='password_reset_complete'),
    path('cuenta/cambiar-contrasena/', views.cambiar_password_view, name='cambiar_password'),
    path('amigos/', social_views.amigos, name='amigos'),
    path('amigos/rutina/nueva/', social_views.rutina_grupal, name='nueva_rutina_grupal'),
    path('amigos/rutina/<int:pk>/', social_views.rutina_grupal, name='rutina_grupal'),
    path('', views.inicio, name='inicio'),
    path('escogenos/', views.escogenos, name='escogenos'),
    path('precios/', views.precios, name='precios'),
    path('registrarse/', views.registrarse, name='registrarse'),
    path('rutinas/', views.rutinas, name='rutinas'),
    path('salud/', views.salud, name='salud'),
    path('hipertrofia/', views.hipertrofia, name='hipertrofia'),
    path('estetico/', views.estetico, name='estetico'),
    path('nutricion/', views.nutricion, name='nutricion'),
    path('objetivo/', views.objetivo, name='objetivo'),
    path('nivel/', views.nivel_entrenamiento_view, name='nivel_entrenamiento'),
    path('prueba-nivel/', views.prueba_nivel_view, name='prueba_nivel'),
    path('configurar-rutina/', views.configurar_rutina_view, name='configurar_rutina'),
    path('crear-rutina/', views.crear_rutina_view, name='crear_rutina'),
    path('dieta/', views.dieta_view, name='dieta'),
    path('notificaciones/', views.notificaciones_view, name='notificaciones'),
    path('notificaciones/siguiente/', views.siguiente_mensaje_view, name='siguiente_mensaje'),
    path('datos-personales/', views.datos_personales_view, name='datos_personales'),
    path('contacto/', views.contacto, name='contacto'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('cuenta/', views.cuenta_view, name='cuenta'),
    path(
    'mi-entrenamiento/',
    views.mi_entrenamiento_view,
    name='mi_entrenamiento',
),
    path(
        'entrenamiento/sesion/<int:sesion_id>/',
        views.reproductor_entrenamiento_view,
        name='reproductor_entrenamiento',
    ),
    path('panel-moderador/', views.panel_moderador_view, name='panel_moderador'),
    path('panel-admin/', views.panel_admin_view, name='panel_admin'),
]
