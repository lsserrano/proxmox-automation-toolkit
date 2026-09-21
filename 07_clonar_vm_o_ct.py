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

def esperar_tarea(proxmox, nodo, upid, timeout=180):
    inicio = time.time()
    while time.time() - inicio < timeout:
        estado = proxmox.nodes(nodo).tasks(upid).status.get()
        if estado['status'] == 'stopped':
            return estado.get('exitstatus') == 'OK'
        time.sleep(2)
    return False

PROXMOX_IP = env_requerida('PROXMOX_IP')
PROXMOX_USER = env_requerida('PROXMOX_USER')
TOKEN_NAME = env_requerida('TOKEN_NAME')
TOKEN_SECRET = env_requerida('TOKEN_SECRET')

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

NODO = env_requerida('PROXMOX_NODE')
tipo = env_requerida('CLONE_TYPE').lower()       # 'vm' o 'ct'
vmid_original = int(env_requerida('CLONE_SOURCE_ID'))
vmid_nuevo = int(env_requerida('CLONE_NEW_ID'))
nombre_clon = os.environ.get('CLONE_NAME', f'clon-{vmid_nuevo}')
storage_destino = os.environ.get('CLONE_STORAGE', 'local-lvm')

print(f"[+] Clonando {tipo.upper()} {vmid_original} -> {vmid_nuevo} ('{nombre_clon}')...")

try:
    if tipo == 'vm':
        upid = proxmox.nodes(NODO).qemu(vmid_original).clone.post(
            newid=vmid_nuevo,
            name=nombre_clon,
            full=1,
            storage=storage_destino,
            description=f'Copia exacta y funcional de la VM {vmid_original}'
        )
    elif tipo == 'ct':
        upid = proxmox.nodes(NODO).lxc(vmid_original).clone.post(
            newid=vmid_nuevo,
            hostname=nombre_clon,
            full=1,
            storage=storage_destino,
            description=f'Copia exacta y funcional del CT {vmid_original}'
        )
    else:
        print(f"[!] CLONE_TYPE '{tipo}' no reconocido. Usa 'vm' o 'ct'.")
        input("\nPresiona Enter para salir...")
        exit(1)

    print("[+] Clonación en curso, esperando a que termine (puede tardar varios minutos)...")

    if esperar_tarea(proxmox, NODO, upid):
        print(f"[+] Clonación completada. {vmid_nuevo} ya es independiente y usable.")
    else:
        print("[-] La clonación no terminó correctamente o superó el tiempo de espera.")

except Exception as e:
    print(f"[-] Error al clonar: {e}")

input("\nPresiona Enter para salir...")