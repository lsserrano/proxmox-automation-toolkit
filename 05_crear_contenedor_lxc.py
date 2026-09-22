import os
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
ct_id = env_requerida('CT_CREATE_VMID')
ct_template = env_requerida('CT_TEMPLATE')
ct_password = env_requerida('CT_ROOT_PASSWORD')
ct_hostname = os.environ.get('CT_HOSTNAME')
ct_cores = int(os.environ.get('CT_CORES', 2))
ct_memory = int(os.environ.get('CT_MEMORY', 512))
ct_swap = int(os.environ.get('CT_SWAP', 512))
ct_disk = os.environ.get('CT_DISK', 'local-lvm:8')
ct_bridge = os.environ.get('CT_BRIDGE', 'vmbr0')

try:
    proxmox.nodes(NODO).lxc.post(
        vmid=int(ct_id),
        hostname=ct_hostname,
        cores=ct_cores,
        memory=ct_memory,
        swap=ct_swap,
        ostemplate=ct_template,
        rootfs=ct_disk,
        net0=f'name=eth0,bridge={ct_bridge},ip=dhcp',
        password=ct_password,
        unprivileged=1,
        onboot=1,
        description='CT de python'
    )
    print(f"[+] Contenedor {ct_id} ({ct_hostname}) creado correctamente. Queda apagado, listo para iniciarlo cuando quieras.")
except Exception as e:
    print(f"[-] Error al crear el CT: {e}")

input("\nPresiona Enter para salir...")