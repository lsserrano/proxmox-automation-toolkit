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

metric_id = os.environ.get('METRIC_SERVER_ID')
metric_type = os.environ.get('METRIC_SERVER_TYPE', 'graphite')
metric_host = os.environ.get('METRIC_SERVER_HOST')
metric_port = os.environ.get('METRIC_SERVER_PORT')

if not metric_id or not metric_host or not metric_port:
    print("[!] Falta METRIC_SERVER_ID, METRIC_SERVER_HOST o METRIC_SERVER_PORT en el .env. Abortando por seguridad.")
    input("\nPresiona Enter para salir...")
    exit(1)

print(f"\n[+] Configurando Metric Server '{metric_id}' ({metric_type}) -> {metric_host}:{metric_port}...")

try:
    proxmox.cluster.metrics.server(metric_id).create(
        type=metric_type,
        server=metric_host,
        port=int(metric_port)
    )
    print(f"[+] Metric Server '{metric_id}' configurado correctamente.")
except Exception as e:
    if "already exists" in str(e).lower():
        print(f"[!] Ya existía un Metric Server con el id '{metric_id}'.")
    else:
        print(f"[-] Ocurrió un error al configurar el Metric Server: {e}")

input("\nPresiona Enter para salir...")