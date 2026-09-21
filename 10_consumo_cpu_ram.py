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
        PROXMOX_IP, user=PROXMOX_USER, token_name=TOKEN_NAME,
        token_value=TOKEN_SECRET, verify_ssl=True
    )
    proxmox.version.get()
    print("[+] Conexión establecida y token validado correctamente.")
except Exception as e:
    print(f"[-] No se pudo conectar o autenticar contra Proxmox: {e}")
    input("\nPresiona Enter para salir...")
    exit(1)

top_n = int(os.environ.get('TOP_N_CONSUMO', 5))

print(f"\n[+] Recogiendo consumo de CPU/RAM de VMs y CTs en todos los nodos...\n")

equipos = []

for node in proxmox.nodes.get():
    nodo_actual = node['node']

    try:
        for vm in proxmox.nodes(nodo_actual).qemu.get():
            if vm.get('status') != 'running':
                continue  # solo tiene sentido medir consumo de lo que está encendido
            estado = proxmox.nodes(nodo_actual).qemu(vm['vmid']).status.current.get()
            equipos.append({
                'tipo': 'VM',
                'id': vm['vmid'],
                'nombre': estado.get('name', vm.get('name', '')),
                'nodo': nodo_actual,
                'cpu_pct': estado.get('cpu', 0) * 100,
                'mem_gb': estado.get('mem', 0) / 1024**3,
                'maxmem_gb': estado.get('maxmem', 0) / 1024**3,
            })
    except Exception as e:
        print(f"[!] No se pudo leer VMs del nodo '{nodo_actual}': {e}")

    try:
        for ct in proxmox.nodes(nodo_actual).lxc.get():
            if ct.get('status') != 'running':
                continue
            estado = proxmox.nodes(nodo_actual).lxc(ct['vmid']).status.current.get()
            equipos.append({
                'tipo': 'CT',
                'id': ct['vmid'],
                'nombre': estado.get('name', ct.get('name', '')),
                'nodo': nodo_actual,
                'cpu_pct': estado.get('cpu', 0) * 100,
                'mem_gb': estado.get('mem', 0) / 1024**3,
                'maxmem_gb': estado.get('maxmem', 0) / 1024**3,
            })
    except Exception as e:
        print(f"[!] No se pudo leer CTs del nodo '{nodo_actual}': {e}")

if not equipos:
    print("[!] No hay VMs ni CTs encendidos ahora mismo, nada que medir.")
    input("\nPresiona Enter para salir...")
    exit(0)

print(f"[+] Top {top_n} por uso de CPU:")
for e in sorted(equipos, key=lambda x: x['cpu_pct'], reverse=True)[:top_n]:
    print(f"    {e['tipo']} {e['id']} ({e['nombre']}) [{e['nodo']}] — CPU: {e['cpu_pct']:.1f}%")

print(f"\n[+] Top {top_n} por uso de RAM:")
for e in sorted(equipos, key=lambda x: x['mem_gb'], reverse=True)[:top_n]:
    print(f"    {e['tipo']} {e['id']} ({e['nombre']}) [{e['nodo']}] — RAM: {e['mem_gb']:.2f} / {e['maxmem_gb']:.2f} GB")

input("\nPresiona Enter para salir...")