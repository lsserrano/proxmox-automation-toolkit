import os
import time
from dotenv import load_dotenv
from proxmoxer import ProxmoxAPI

load_dotenv()

def env_requerida(clave):
    valor = os.environ.get(clave)
    if not valor:
        print(f"[!] Falta la variable obligatoria '{clave}' en el .env. Abortando por seguridad.")
        input("\nPresiona Enter para salir...")
        exit(1)
    return valor

def esperar_tarea(proxmox, nodo, upid, timeout=60):
    inicio = time.time()
    while time.time() - inicio < timeout:
        estado = proxmox.nodes(nodo).tasks(upid).status.get()
        if estado['status'] == 'stopped':
            return estado.get('exitstatus') == 'OK'
        time.sleep(1)
    return False

PROXMOX_IP = env_requerida('PROXMOX_IP')
PROXMOX_USER = env_requerida('PROXMOX_USER')
TOKEN_NAME = env_requerida('TOKEN_NAME')
TOKEN_SECRET = env_requerida('TOKEN_SECRET')

try:
    proxmox = ProxmoxAPI(
        PROXMOX_IP, user=PROXMOX_USER, token_name=TOKEN_NAME,
        token_value=TOKEN_SECRET, verify_ssl=True
    )
    proxmox.version.get()
    print("[+] Conexión establecida y token validado correctamente.")
except Exception as e:
    print(f"[-] No se pudo conectar o autenticar contra Proxmox: {e}")
    input("\nPresiona Enter para salir...")
    exit(1)

NODO = env_requerida('PROXMOX_NODE')
ct_id = int(env_requerida('CT_VMID'))
accion = env_requerida('CT_ACTION').lower()   # start | stop | shutdown | reboot | suspend

acciones_validas = {'start', 'stop', 'shutdown', 'reboot', 'suspend'}
if accion not in acciones_validas:
    print(f"[!] Acción '{accion}' no reconocida. Usa una de: {', '.join(acciones_validas)}")
    input("\nPresiona Enter para salir...")
    exit(1)

print(f"[+] Ejecutando '{accion}' sobre el CT {ct_id}...")

try:
    endpoint = getattr(proxmox.nodes(NODO).lxc(ct_id).status, accion)
    upid = endpoint.post()

    if esperar_tarea(proxmox, NODO, upid):
        print(f"[+] Acción '{accion}' completada correctamente sobre el CT {ct_id}.")
    else:
        print(f"[!] Se envió '{accion}' pero no se confirmó su finalización a tiempo.")
except Exception as e:
    print(f"[-] Error al ejecutar '{accion}': {e}")

input("\nPresiona Enter para salir...")