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
vm_id = env_requerida('VM_VMID')
vm_iso = env_requerida('VM_ISO')

vm_name = os.environ.get('VM_NAME')
vm_cores = int(os.environ.get('VM_CORES', 4))
vm_sockets = int(os.environ.get('VM_SOCKETS', 1))
vm_memory = int(os.environ.get('VM_MEMORY', 1024))
vm_disk = os.environ.get('VM_DISK', 'local-lvm:5')
vm_bridge = os.environ.get('VM_BRIDGE', 'vmbr0')

try:
    proxmox.nodes(NODO).qemu.post(
        vmid=int(vm_id),
        name=vm_name,
        cores=vm_cores,
        sockets=vm_sockets,
        memory=vm_memory,
        scsi0=vm_disk,
        ide2=f'{vm_iso},media=cdrom',
        net0=f'virtio,bridge={vm_bridge}',
        ostype='l26',
        boot='order=ide2;scsi0',
        agent=1,
        onboot=1,
        description='Prueba de python VM1'
    )
    print(f"[+] VM {vm_id} ({vm_name}) creada correctamente. Queda apagada, lista para instalar el SO desde el ISO.")
except Exception as e:
    print(f"[-] Error al crear la VM: {e}")

input("\nPresiona Enter para salir...")