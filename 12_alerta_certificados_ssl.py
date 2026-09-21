import os
import smtplib
import datetime
from email.message import EmailMessage
from dotenv import load_dotenv
from proxmoxer import ProxmoxAPI

load_dotenv()

def env_requerida(clave):
    valor = os.environ.get(clave)
    if not valor:
        print(f"[!] Falta la variable obligatoria '{clave}' en el .env. Abortando por seguridad.")
        exit(1)
    return valor

PROXMOX_IP = env_requerida('PROXMOX_IP')
PROXMOX_USER = env_requerida('PROXMOX_USER')
TOKEN_NAME = env_requerida('TOKEN_NAME')
TOKEN_SECRET = env_requerida('TOKEN_SECRET')

SMTP_SERVER = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.environ.get('SMTP_PORT', 587))
MI_CORREO = env_requerida('SMTP_USER')
MI_PASSWORD = env_requerida('SMTP_PASSWORD')
DESTINO = env_requerida('SMTP_DESTINO')

DIAS_AVISO = int(os.environ.get('SSL_ALERT_DAYS', 7))

try:
    proxmox = ProxmoxAPI(
        PROXMOX_IP, user=PROXMOX_USER, token_name=TOKEN_NAME,
        token_value=TOKEN_SECRET, verify_ssl=True
    )
    proxmox.version.get()
    print("[+] Conexión establecida y token validado correctamente.")
except Exception as e:
    print(f"[-] No se pudo conectar o autenticar contra Proxmox: {e}")
    exit(1)

def alerta_email(asunto, cuerpo):
    msg = EmailMessage()
    msg.set_content(cuerpo)
    msg['Subject'], msg['From'], msg['To'] = asunto, MI_CORREO, DESTINO
    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as s:
            s.starttls()
            s.login(MI_CORREO, MI_PASSWORD)
            s.send_message(msg)
        print(f"[+] Alerta enviada a {DESTINO}")
    except Exception as e:
        print(f"[-] Error enviando email: {e}")

def gestionar_certificados():
    try:
        nodos = proxmox.nodes.get()
    except Exception as e:
        print(f"[-] No se pudo obtener la lista de nodos: {e}")
        return

    for node in nodos:
        n = node['node']
        try:
            certs = proxmox.nodes(n).certificates.info.get()
        except Exception as e:
            print(f"[-] No se pudieron leer certificados del nodo '{n}': {e}")
            continue

        for c in certs:
            nombre = c.get('filename', 'pveproxy-ssl.pem')
            exp_dt = datetime.datetime.fromtimestamp(c.get('notafter', 0))
            dias = (exp_dt - datetime.datetime.now()).days

            if dias <= DIAS_AVISO:
                print(f"[!] Certificado {nombre} en nodo {n} vence en {dias} días.")
                alerta_email(
                    f'[AVISO] SSL en [{n}] vence en {dias} días',
                    f'El certificado {nombre} en el servidor {n} caduca el {exp_dt.date()}.\n'
                    f'Accede para renovarlo: https://{PROXMOX_IP}:8006'
                )
            else:
                print(f"[+] Nodo [{n}]: {nombre} vence en {dias} días.")

if __name__ == "__main__":
    gestionar_certificados()