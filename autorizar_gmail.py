"""Local-only sender authorization. Never prints tokens or changes production."""
import argparse
import json
import os
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('credentials', type=Path)
    args = parser.parse_args()
    from google_auth_oauthlib.flow import InstalledAppFlow
    scope = 'https://www.googleapis.com/auth/gmail.send'
    data = json.loads(args.credentials.read_text(encoding='utf-8'))
    if 'installed' not in data:
        raise ValueError('Se requiere el cliente de escritorio.')
    output = Path(os.environ['LOCALAPPDATA']) / 'MaikerGym' / 'gmail-oauth.json'
    if output.exists():
        raise ValueError('Ya existe una autorización local. No se sobrescribió.')
    flow = InstalledAppFlow.from_client_config(data, [scope], autogenerate_code_verifier=True)
    print('Se abrirá Google. Selecciona codexinfinity2025@gmail.com y revisa el permiso de envío.', flush=True)
    credentials = flow.run_local_server(host='127.0.0.1', port=0,
        open_browser=True, timeout_seconds=300, prompt='consent',
        login_hint='codexinfinity2025@gmail.com',
        authorization_prompt_message='Esperando tu autorización en el navegador...',
        success_message='Autorización recibida. Puedes cerrar esta pestaña y volver a Codex.')
    if not credentials.refresh_token:
        raise ValueError('Google no entregó autorización offline.')
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('x', encoding='utf-8') as stream:
        json.dump({'GMAIL_CLIENT_ID': credentials.client_id,
                   'GMAIL_CLIENT_SECRET': credentials.client_secret,
                   'GMAIL_REFRESH_TOKEN': credentials.refresh_token}, stream)
    print('Autorización guardada fuera del repositorio. No se ha enviado ningún correo.', flush=True)


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        # Provider errors may contain tokens or codes. Never print their details.
        print('No se completó la autorización (' + type(error).__name__ + '). No compartas claves.')
        raise SystemExit(1)
