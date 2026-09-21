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

nuevo_userid = os.environ.get('NEW_USER_ID')
nuevo_password = os.environ.get('NEW_USER_PASSWORD')
comentario = 'Creado automaticamente desde el ejecutable Python'

if not nuevo_userid or not nuevo_password:
    print("[!] Falta NEW_USER_ID o NEW_USER_PASSWORD en el .env. Abortando por seguridad.")
    input("\nPresiona Enter para salir...")
    exit(1)

datos_nuevo_usuario = {
    "userid": nuevo_userid,
    "password": nuevo_password,
    "comment": comentario,
    "enable": 1
}

print(f"\n[+] Intentando crear el usuario: {datos_nuevo_usuario['userid']}...")

try:
    proxmox.access.users.post(**datos_nuevo_usuario)
    print(f"[+] El usuario '{datos_nuevo_usuario['userid']}' fue creado correctamente.")
except Exception as e:
    if "already exists" in str(e).lower():
        print(f"[!] El usuario '{datos_nuevo_usuario['userid']}' ya existía en el sistema.")
    else:
        print(f"[-] Ocurrió un error al hablar con Proxmox: {e}")

input("\nPresiona Enter para salir...")