from io import BytesIO, StringIO
import os
import subprocess
import sys
from tempfile import TemporaryDirectory
from unittest.mock import patch

from PIL import Image
from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.management import call_command, CommandError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.files.storage import default_storage
from django.db import OperationalError
from django.test import TestCase, SimpleTestCase, override_settings
from django.urls import reverse

from .models import PerfilUsuario, Ejercicio, PlanEntrenamiento
from .profile_validation import normalizar_foto, validar_medida


def foto_valida():
    datos = BytesIO()
    Image.new('RGB', (32, 32), 'orange').save(datos, 'PNG')
    return SimpleUploadedFile('foto.png', datos.getvalue(), content_type='image/png')


class CuentaSeguraTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('auditoria', password='Segura-prueba-784!')
        self.perfil = self.user.perfil
        self.perfil.objetivo = 'salud'
        self.perfil.nivel_entrenamiento = 'principiante'
        self.perfil.nivel_declarado = 'principiante'
        self.perfil.prueba_nivel_completada = True
        self.perfil.configuracion_entrenamiento_completa = True
        self.perfil.orientacion_nutricional_vista = True
        self.perfil.datos_completos = True
        self.perfil.peso = 75
        self.perfil.save()
        self.client.force_login(self.user)
        temporal = TemporaryDirectory()
        self.addCleanup(temporal.cleanup)
        opciones = override_settings(MEDIA_ROOT=temporal.name)
        opciones.enable()
        self.addCleanup(opciones.disable)

    def test_rechaza_medidas_invalidas_sin_guardado_parcial(self):
        for campo in ('peso', 'peso_inicial', 'altura_cm'):
            for valor in ('-1', 'abc', 'NaN', 'Infinity', '99999', '75.555'):
                with self.subTest(campo=campo, valor=valor):
                    respuesta = self.client.post(reverse('cuenta'), {
                        'accion': 'actualizar_cuenta', campo: valor, 'nombre': 'NoGuardar'})
                    self.assertEqual(respuesta.status_code, 400)
                    self.user.refresh_from_db()
                    self.assertEqual(self.user.first_name, '')
                    self.perfil.refresh_from_db()
                    self.assertEqual(self.perfil.peso, 75)

    def test_guarda_medidas_validas(self):
        response = self.client.post(reverse('cuenta'), {'accion': 'actualizar_cuenta',
            'peso': '76.50', 'peso_inicial': '80', 'altura_cm': '175.25'})
        self.assertEqual(response.status_code, 302)
        self.perfil.refresh_from_db()
        self.assertEqual(str(self.perfil.peso), '76.50')
        self.assertEqual(str(self.perfil.altura_cm), '175.25')

    def test_rechaza_html_disfrazado_de_foto(self):
        response = self.client.post(reverse('cuenta'), {'accion': 'actualizar_foto',
            'foto': SimpleUploadedFile('foto.jpg', b'<script>alert(1)</script>', content_type='image/jpeg')})
        self.assertEqual(response.status_code, 400)
        self.perfil.refresh_from_db()
        self.assertFalse(self.perfil.foto)

    def test_onboarding_rechaza_medida_o_foto_invalida(self):
        self.perfil.datos_completos = False
        self.perfil.save(update_fields=['datos_completos'])
        datos = {'genero': 'masculino', 'peso': '75', 'altura_cm': '175', 'fecha_nacimiento': '2000-01-01'}
        respuesta = self.client.post(reverse('datos_personales'), dict(datos, peso='75.555'))
        self.assertEqual(respuesta.status_code, 400)
        respuesta = self.client.post(reverse('datos_personales'), dict(datos,
            foto=SimpleUploadedFile('fake.jpg', b'<html>fake</html>', content_type='image/jpeg')))
        self.assertEqual(respuesta.status_code, 400)
        self.perfil.refresh_from_db()
        self.assertFalse(self.perfil.datos_completos)

    def test_modelo_tambien_rechaza_html(self):
        self.perfil.foto = SimpleUploadedFile('archivo.html', b'<h1>HTML</h1>')
        with self.assertRaises(ValidationError):
            self.perfil.save()

    def test_foto_normalizada_y_servida_como_imagen(self):
        respuesta = self.client.post(reverse('cuenta'), {'accion': 'actualizar_foto', 'foto': foto_valida()})
        self.assertEqual(respuesta.status_code, 302)
        self.perfil.refresh_from_db()
        self.assertTrue(self.perfil.foto.name.endswith('.jpg'))
        response = self.client.get(self.perfil.foto.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'image/jpeg')
        self.assertEqual(response['X-Content-Type-Options'], 'nosniff')
        self.assertTrue(b''.join(response.streaming_content).startswith(b'\xff\xd8'))
        # El cliente de Django cierra la respuesta al consumir el iterador.
        # Cerrarla otra vez emite request_finished fuera de su protección y
        # cierra la conexión MySQL dentro de la transacción de TestCase.

    def test_archivos_antiguos_activos_no_se_publican(self):
        for ruta in ('perfiles/antiguo.html', 'perfiles/falso.jpg', 'otro.html'):
            nombre = default_storage.save(ruta, SimpleUploadedFile('antiguo', b'<script>alert(1)</script>'))
            self.assertEqual(self.client.get('/media/' + nombre).status_code, 404)

    def test_perfil_inactivo_bloquea_login_y_sesion_existente(self):
        self.perfil.activo = False
        self.perfil.save(update_fields=['activo'])
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)
        self.assertIsNone(authenticate(username='auditoria', password='Segura-prueba-784!'))
        self.assertEqual(self.client.get(reverse('cuenta')).status_code, 302)

    def test_estado_se_sincroniza_en_ambos_sentidos(self):
        self.user.is_active = False
        self.user.save(update_fields=['is_active'])
        self.perfil.refresh_from_db()
        self.assertFalse(self.perfil.activo)
        self.perfil.activo = True
        self.perfil.save(update_fields=['activo'])
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active)

    def test_estado_legado_incoherente_tambien_bloquea(self):
        PerfilUsuario.objects.filter(pk=self.perfil.pk).update(activo=False)
        self.assertIsNone(authenticate(username='auditoria', password='Segura-prueba-784!'))

    def test_health_comprueba_base(self):
        self.assertEqual(self.client.get('/health/').status_code, 200)
        with patch('gym_project.urls.connection.cursor', side_effect=OperationalError('secreto')):
            respuesta = self.client.get('/health/')
        self.assertEqual(respuesta.status_code, 503)
        self.assertNotIn(b'secreto', respuesta.content)


class ConfiguracionSeguraTest(SimpleTestCase):
    def test_foto_excesiva(self):
        with self.assertRaises(ValidationError):
            normalizar_foto(SimpleUploadedFile('grande.png', b'x' * (5 * 1024 * 1024 + 1)))

    def test_foto_elimina_contenido_anadido(self):
        archivo = foto_valida()
        archivo = SimpleUploadedFile('foto.png', archivo.read() + b'<script>ataque</script>')
        resultado = normalizar_foto(archivo)
        self.assertNotIn(b'<script>', resultado.read())

    def test_limites_medidas(self):
        for campo, limites in [('peso', (1, 500)), ('altura_cm', (50, 250))]:
            for valor in limites:
                self.assertEqual(validar_medida(str(valor), campo), valor)

    def test_mysql_es_obligatorio(self):
        entorno = dict(os.environ, DEBUG='False', MYSQL_DATABASE=' ', MYSQLDATABASE=' ',
                       SECRET_KEY='clave-de-prueba-no-utilizable-en-produccion', PYTHONIOENCODING='utf-8')
        resultado = subprocess.run([sys.executable, '-c', 'import gym_project.settings'],
            cwd=settings.BASE_DIR, env=entorno, capture_output=True, text=True, encoding='utf-8', timeout=20)
        self.assertNotEqual(resultado.returncode, 0)
        self.assertIn('MySQL es obligatorio', resultado.stderr)
        entorno['DEBUG'] = 'True'
        resultado = subprocess.run([sys.executable, '-c', 'import gym_project.settings'],
            cwd=settings.BASE_DIR, env=entorno, capture_output=True, text=True, encoding='utf-8', timeout=20)
        self.assertNotEqual(resultado.returncode, 0)
        self.assertIn('MySQL es obligatorio', resultado.stderr)

    def test_arranque_no_sobrescribe_catalogo(self):
        docker = (settings.BASE_DIR / 'Dockerfile').read_text(encoding='utf-8-sig')
        comando = next(linea for linea in docker.splitlines() if linea.startswith('CMD'))
        self.assertNotIn('cargar_ejercicios', comando)
        self.assertNotIn('cargar_plan_hipertrofia', comando)

    def test_base_no_carga_bootstrap_js_sin_jquery(self):
        base = (settings.BASE_DIR / 'gym_project/gym_app/templates/base.html').read_text(encoding='utf-8-sig')
        self.assertNotIn('bootstrap.bundle.min.js', base)


class CatalogoInicialTest(TestCase):
    def test_inicializacion_y_rechazo_de_sobrescritura(self):
        call_command('inicializar_catalogo', stdout=StringIO())
        self.assertEqual(Ejercicio.objects.count(), 42)
        self.assertEqual(PlanEntrenamiento.objects.count(), 4)
        ejercicio = Ejercicio.objects.first()
        ejercicio.descripcion = 'Edición del administrador que debe conservarse'
        ejercicio.save()
        with self.assertRaises(CommandError):
            call_command('inicializar_catalogo', stdout=StringIO())
        ejercicio.refresh_from_db()
        self.assertEqual(ejercicio.descripcion, 'Edición del administrador que debe conservarse')
