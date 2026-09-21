import os
import time
from datetime import datetime, timezone
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

DIAS_RETENCION = int(os.environ.get('SNAPSHOT_RETENTION_DAYS', 3))


def crear_y_rotar_snapshots(proxmox):
    print(f"[+] Creación y rotación de snapshots (retención {DIAS_RETENCION} días)\n")
    ahora = datetime.now(timezone.utc)
    nombre_hoy = ahora.strftime("auto_%Y-%m-%d_%H%M")

    total_ok = 0
    total_error = 0

    try:
        nodos = proxmox.nodes.get()
    except Exception as e:
        print(f"[-] No se pudo obtener la lista de nodos: {e}")
        return

    for n in nodos:
        nodo = n['node']

        try:
            maquinas = [(proxmox.nodes(nodo).qemu, m, 'VM') for m in proxmox.nodes(nodo).qemu.get()] + \
                       [(proxmox.nodes(nodo).lxc, m, 'CT') for m in proxmox.nodes(nodo).lxc.get()]
        except Exception as e:
            print(f"[-] No se pudo listar VMs/CTs del nodo '{nodo}': {e}")
            continue

        for api, m, tipo in maquinas:
            vmid = m['vmid']
            print(f"\n[+] Procesando {tipo} {vmid} ({m.get('name', 'Sin nombre')})")

            try:
                snaps = api(vmid).snapshot.get()
            except Exception as e:
                print(f"  [-] Error al listar snapshots: {e}")
                total_error += 1
                continue

            for s in snaps:
                if s['name'].startswith('auto_'):
                    dias = (ahora - datetime.fromtimestamp(s.get('snaptime', 0), timezone.utc)).days
                    if dias >= DIAS_RETENCION:
                        print(f"  [!] Borrando snapshot antiguo: {s['name']} ({dias} días)")
                        try:
                            api(vmid).snapshot(s['name']).delete()
                            time.sleep(3)
                        except Exception as e:
                            print(f"  [-] Error al borrar '{s['name']}': {e}")

            print(f"  [+] Creando snapshot: {nombre_hoy}")
            try:
                api(vmid).snapshot.post(snapname=nombre_hoy, description="Auto-generado por script")
                total_ok += 1
            except Exception as e:
                print(f"  [-] Error al crear snapshot: {e}")
                total_error += 1

    print(f"\n[+] Proceso completado: {total_ok} snapshots creados correctamente, {total_error} con error.")

crear_y_rotar_snapshots(proxmox)
input("\nPresiona Enter para salir...")