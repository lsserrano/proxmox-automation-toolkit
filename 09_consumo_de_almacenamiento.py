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

top_n = int(os.environ.get('TOP_N_ARCHIVOS', 5))

print(f"\n[+] Buscando los {top_n} archivos que más espacio ocupan por storage...\n")

for node in proxmox.nodes.get():
    nodo_actual = node['node']

    for storage in proxmox.nodes(nodo_actual).storage.get():
        storage_id = storage['storage']
        try:
            contenido = proxmox.nodes(nodo_actual).storage(storage_id).content.get()
            mayores = sorted(contenido, key=lambda x: x.get('size', 0), reverse=True)[:top_n]

            if not mayores:
                continue

            print(f"[+] Storage '{storage_id}' (nodo {nodo_actual}):")
            for item in mayores:
                gb = item.get('size', 0) / 1024**3
                print(f"    {item['volid']}: {gb:.1f} GB")

        except Exception as e:
            print(f"[!] No se pudo leer el contenido de '{storage_id}': {e}")

input("\nPresiona Enter para salir...")