#!/usr/bin/env python
import os
import sys

from decouple import config
import pymysql


def create_database():
    db_name = config('MYSQL_DATABASE', default='').strip()
    if not db_name:
        print('ERROR: MYSQL_DATABASE no está configurado en .env')
        return False

    user = config('MYSQL_USER', default='root')
    password = config('MYSQL_PASSWORD', default='')
    host = config('MYSQL_HOST', default='127.0.0.1')
    port = config('MYSQL_PORT', default='3306')

    print(f'Conectando a MySQL en {host}:{port} con usuario "{user}"...')
    try:
        connection = pymysql.connect(
            host=host,
            user=user,
            password=password,
            port=int(port),
            charset='utf8mb4',
            cursorclass=pymysql.cursors.Cursor,
            autocommit=True,
        )
    except Exception as exc:
        print('ERROR: No se pudo conectar a MySQL.')
        print(exc)
        return False

    try:
        with connection.cursor() as cursor:
            sql = (
                f"CREATE DATABASE IF NOT EXISTS `{db_name}` "
                "DEFAULT CHARACTER SET utf8mb4 "
                "DEFAULT COLLATE utf8mb4_spanish_ci;"
            )
            cursor.execute(sql)
            print(f'Base de datos "{db_name}" creada o ya existente.')
    except Exception as exc:
        print('ERROR: No se pudo crear la base de datos.')
        print(exc)
        return False
    finally:
        connection.close()

    return True


if __name__ == '__main__':
    ok = create_database()
    sys.exit(0 if ok else 1)
