#!/usr/bin/env python

import os
import sys
from pathlib import Path

import django
from decouple import config


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gym_project.settings")
sys.path.insert(0, str(Path(__file__).resolve().parent))

django.setup()

from django.contrib.auth.models import User
from gym_project.gym_app.models import PerfilUsuario, RolChoice


def obtener_password(nombre_variable):
    """
    Obtiene una contraseña desde el archivo .env.

    No utiliza contraseñas predeterminadas porque podrían terminar
    publicadas accidentalmente.
    """
    password = config(nombre_variable, default="").strip()

    if not password:
        raise RuntimeError(
            f"Falta configurar {nombre_variable} en el archivo .env."
        )

    if len(password) < 12:
        raise RuntimeError(
            f"{nombre_variable} debe tener al menos 12 caracteres."
        )

    return password


def crear_usuario_prueba(
    username,
    email,
    variable_password,
    nombre,
    apellido,
    rol,
    objetivo=None,
):
    """
    Crea una cuenta de desarrollo únicamente cuando todavía no existe.
    """
    if User.objects.filter(email=email).exists():
        print(f"[OK] El usuario {email} ya existe.")
        return

    password = obtener_password(variable_password)

    usuario = User.objects.create_user(
        username=username,
        email=email,
        password=password,
        first_name=nombre,
        last_name=apellido,
    )

    perfil = usuario.perfil
    perfil.rol = rol

    if objetivo:
        perfil.objetivo = objetivo

    perfil.save()

    print(f"[OK] Usuario de desarrollo creado: {email}")


def crear_usuarios_prueba():
    crear_usuario_prueba(
        username="admin",
        email="admin@maiker.test",
        variable_password="TEST_ADMIN_PASSWORD",
        nombre="Admin",
        apellido="MaikerGym",
        rol=RolChoice.ADMIN,
    )

    crear_usuario_prueba(
        username="moderador",
        email="mod@maiker.test",
        variable_password="TEST_MODERATOR_PASSWORD",
        nombre="Moderador",
        apellido="MaikerGym",
        rol=RolChoice.MODERADOR,
    )

    crear_usuario_prueba(
        username="usuario",
        email="usuario@maiker.test",
        variable_password="TEST_USER_PASSWORD",
        nombre="Usuario",
        apellido="Prueba",
        rol=RolChoice.USUARIO,
        objetivo="estetico",
    )


if __name__ == "__main__":
    print("Preparando cuentas locales de desarrollo...")

    try:
        crear_usuarios_prueba()
    except RuntimeError as error:
        print(f"ERROR: {error}")
        sys.exit(1)

    print("[OK] Inicialización completada.")
    print("Las contraseñas no se muestran ni están escritas en el código.")