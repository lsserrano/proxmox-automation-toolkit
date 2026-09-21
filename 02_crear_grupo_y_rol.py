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

grupo_id = os.environ.get('GROUP_ID')
grupo_comentario = os.environ.get('GROUP_COMMENT', '')
acl_rol = os.environ.get('ACL_ROLE', 'PVEAuditor')  # rol ya existente en Proxmox
acl_path = os.environ.get('ACL_PATH', '/')

if not grupo_id:
    print("[!] Falta GROUP_ID en el .env. Abortando por seguridad.")
    input("\nPresiona Enter para salir...")
    exit(1)

try:
    proxmox.access.groups.post(groupid=grupo_id, comment=grupo_comentario)
    print(f"[+] Grupo '{grupo_id}' creado con éxito.")
except Exception as e:
    if "already exists" in str(e).lower():
        print(f"[!] El grupo '{grupo_id}' ya existía, saltando creación...")
    else:
        print(f"[-] Error al crear el grupo: {e}")
        input("\nPresiona Enter para salir...")
        exit(1)

try:
    proxmox.access.acl.put(path=acl_path, roles=acl_rol, groups=grupo_id, propagate=1)
    print(f"[+] Rol '{acl_rol}' asignado al grupo '{grupo_id}' sobre '{acl_path}'.")
except Exception as e:
    print(f"[-] Error al asignar permisos: {e}")

print("[+] Tarea de seguridad finalizada.")