import os
from dotenv import load_dotenv
from proxmoxer import ProxmoxAPI

load_dotenv()

PROXMOX_IP = os.environ.get('PROXMOX_IP')
PROXMOX_USER = os.environ.get('PROXMOX_USER')
TOKEN_NAME = os.environ.get('TOKEN_NAME')
TOKEN_SECRET = os.environ.get('TOKEN_SECRET')

try:
    proxmox = ProxmoxAPI(
        PROXMOX_IP,
        user=PROXMOX_USER,
        token_name=TOKEN_NAME,
        token_value=TOKEN_SECRET,
        verify_ssl=True
    )
    proxmox.version.get()
    print("[+] Conexión establecida y token validado correctamente.")
except Exception as e:
    print(f"[-] No se pudo conectar o autenticar contra Proxmox: {e}")
    input("\nPresiona Enter para salir...")
    exit(1)

target_user = os.environ.get('NEW_TOKEN_USER')
target_token_name = os.environ.get('NEW_TOKEN_NAME')
token_comment = os.environ.get('NEW_TOKEN_COMMENT')
token_privsep = int(os.environ.get('NEW_TOKEN_PRIVSEP', 1))

if not target_user:
    print("[!] Falta NEW_TOKEN_USER en el .env. Abortando por seguridad.")
    input("\nPresiona Enter para salir...")
    exit(1)

try:
    resultado = proxmox.access.users(target_user).token(target_token_name).post(
        comment=token_comment,
        expire=0,
        privsep=token_privsep
    )

    token_id = resultado['full-tokenid']
    token_valor = resultado['value']

    print(f"[+] Token '{target_token_name}' creado exitosamente para '{target_user}'.")
    print(f"    Token ID:    {token_id}")
    print(f"    Token valor: {token_valor}")
    print("[!] Guarda este valor ahora mismo, no se puede recuperar después.")

except Exception as e:
    error_str = str(e).lower()
    if "already exists" in error_str or "duplicate" in error_str:
        print(f"[!] El token '{target_token_name}' ya existía para el usuario '{target_user}'.")
        print("    Nota: Proxmox no vuelve a mostrar el secreto de un token existente. Si lo perdiste, bórralo en la interfaz web y vuelve a ejecutar este script.")
    else:
        print(f"[-] Error al crear el token: {e}")

print("[+] Ejecución finalizada.")