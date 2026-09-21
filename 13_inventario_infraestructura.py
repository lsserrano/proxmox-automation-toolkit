import os
import csv
import json
import datetime
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

print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Conectando a Proxmox...")

try:
    proxmox = ProxmoxAPI(
        PROXMOX_IP, user=PROXMOX_USER, token_name=TOKEN_NAME,
        token_value=TOKEN_SECRET, verify_ssl=True
    )
    nodos_lista = proxmox.nodes.get()
    print(f"[+] Conexión establecida. Nodos detectados: {len(nodos_lista)}")
except Exception as e:
    print(f"[-] No se pudo conectar o autenticar contra Proxmox: {e}")
    input("\nPresiona Enter para salir...")
    exit(1)

def generar_inventario():
    fecha = datetime.datetime.now().strftime('%Y-%m-%d_%H%M')
    archivo_json = os.environ.get('INVENTARIO_JSON', f"inventario_proxmox_{fecha}.json")
    archivo_csv = os.environ.get('INVENTARIO_CSV', f"inventario_proxmox_{fecha}.csv")

    inventario = {
        'generado': datetime.datetime.now().isoformat(),
        'nodos': [],
        'vms': [],
        'lxc': []
    }

    print("[+] Escaneando infraestructura...")

    try:
        for node in nodos_lista:
            n = node['node']
            st = proxmox.nodes(n).status.get()

            inventario['nodos'].append({
                'nombre': n,
                'estado': node['status'],
                'cpu_pct': round(st.get('cpu', 0) * 100, 1),
                'ram_gb': round(st['memory']['total'] / 1024**3, 1)
            })

            for vm in proxmox.nodes(n).qemu.get():
                inventario['vms'].append({
                    'vmid': vm['vmid'],
                    'nombre': vm.get('name', 'sin-nombre'),
                    'nodo': n,
                    'estado': vm['status'],
                    'cores': vm.get('cpus', '?'),
                    'ram_mb': vm.get('maxmem', 0) // 1024**2,
                    'disco_gb': vm.get('maxdisk', 0) // 1024**3
                })

            for ct in proxmox.nodes(n).lxc.get():
                inventario['lxc'].append({
                    'vmid': ct['vmid'],
                    'nombre': ct.get('name', 'sin-nombre'),
                    'nodo': n,
                    'estado': ct['status'],
                    'cores': ct.get('cpus', '?'),
                    'ram_mb': ct.get('maxmem', 0) // 1024**2,
                    'disco_gb': ct.get('maxdisk', 0) // 1024**3
                })
    except Exception as e:
        print(f"[-] Error al escanear la infraestructura: {e}")
        return

    try:
        with open(archivo_json, 'w', encoding='utf-8') as fj:
            json.dump(inventario, fj, indent=4, ensure_ascii=False)

        with open(archivo_csv, 'w', newline='', encoding='utf-8') as fc:
            writer = csv.DictWriter(fc, fieldnames=['tipo', 'vmid', 'nombre', 'nodo', 'estado', 'cores', 'ram_mb', 'disco_gb'])
            writer.writeheader()

            for vm in inventario['vms']:
                writer.writerow({'tipo': 'VM', **vm})

            for ct in inventario['lxc']:
                writer.writerow({'tipo': 'CT', **ct})

    except Exception as e:
        print(f"[-] Error al escribir los archivos de inventario: {e}")
        return

    print(f"\n[+] Inventarios creados exitosamente.")
    print(f"[+] {len(inventario['vms'])} VMs y {len(inventario['lxc'])} contenedores procesados.")
    print(f"[+] Archivo JSON: {os.path.abspath(archivo_json)}")
    print(f"[+] Archivo CSV:  {os.path.abspath(archivo_csv)}")


if __name__ == "__main__":
    generar_inventario()