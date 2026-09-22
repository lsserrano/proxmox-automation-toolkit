# Proxmox Automation Toolkit

Suite de scripts en Python para automatizar la gestión de un hipervisor Proxmox VE vía su API REST, usando proxmoxer. Cubre todo el ciclo de vida de la infraestructura: identidad y permisos (RBAC), aprovisionamiento de VMs/CTs, observabilidad y operaciones de mantenimiento.

Desarrollado y probado en un `HOME LAB LOCAL`, simulando flujos de trabajo de nivel Enterprise: gestión de credenciales por token, control de acceso basado en roles, certificados TLS propios, y automatización de tareas recurrentes (snapshots, alertas, inventario).

## Motivación

Este proyecto nace como ejercicio práctico de automatización de infraestructura, aplicando en un entorno controlado los principios que se esperan en un puesto DevOps / SysAdmin real:

- **Seguridad primero**: sin credenciales hardcodeadas, autenticación por token con privilegios separables, verificación TLS real.
- **Mínimo privilegio**: cada automatización usa el permiso justo que necesita, no más.
- **Resiliencia**: manejo de errores explícito, confirmación real de operaciones asíncronas.
- **Reproducibilidad**: toda la configuración vive en variables de entorno, nada queda "quemado" en el código.

## Arquitectura del entorno

| Componente | Detalle |

| Hipervisor | Proxmox VE, virtualizado dentro de VirtualBox (*nested virtualization*) sobre Windows — home lab local |
| Autenticación | Token API dedicado (`root@pam` + Token ID), no la cuenta de usuario directa |
| Certificados TLS | Certificado local gestionado con [mkcert](https://github.com/FiloSottile/mkcert) — `verify_ssl=True` real, sin desactivar la verificación |
| Lenguaje | Python 3.12 |
| Librería principal | [`proxmoxer`](https://github.com/proxmoxer/proxmoxer) |
| Gestión de secretos | Variables de entorno vía `python-dotenv` (`.env`, nunca versionado) |

> **Nota sobre `verify_ssl=True`:** el certificado de Proxmox fue generado con mkcert y confiado localmente en la máquina de desarrollo. Al desplegar esto en otro entorno, genera/instala tu propio certificado (mkcert, CA corporativa o Let's Encrypt) antes de activar la verificación estricta.

## Scripts incluidos

### Identidad y seguridad (RBAC)
| Script | Descripción |

| `01_crear_usuario.py` | Crea un usuario en Proxmox con validaciones y manejo de duplicados |
| `02_crear_grupo_y_rol.py` | Crea un grupo, y le asigna un rol existente (p. ej. `PVEAuditor`) sobre un path concreto vía ACL |
| `03_crear_token_api.py` | Genera un token API para un usuario con `privsep=1` (sin herencia automática de permisos — mínimo privilegio) |
| `04_configurar_metric_server.py` | Registra un servidor externo (Graphite) como destino de métricas del clúster |

### Ciclo de vida de infraestructura
| Script | Descripción |

| `05_crear_contenedor_lxc.py` | Aprovisiona un contenedor LXC desde una plantilla, sin arrancarlo automáticamente |
| `06_crear_vm.py` | Aprovisiona una VM QEMU desde una ISO |
| `07_clonar_vm_o_ct.py` | Clona una VM o CT existente (full clone), confirmando la finalización real de la tarea asíncrona |
| `08_control_estado_vm_ct.py` | Ejecuta una acción de ciclo de vida (start / stop / shutdown / reboot / suspend) sobre un CT, con confirmación real |

### Observabilidad
| Script | Descripción |

| `09_consumo_de_almacenamiento.py` | Lista los N archivos que más espacio ocupan por cada storage del clúster |
| `10_consumo_cpu_ram.py` | Ranking de las VMs/CTs con mayor consumo de CPU y RAM en tiempo real |

### Operación y mantenimiento
| Script | Descripción |

| `11_rotacion_snapshots.py` | Crea un snapshot diario por máquina y elimina automáticamente los más antiguos que la retención configurada |
| `12_alerta_certificados_ssl.py` | Vigila la caducidad de los certificados SSL del clúster y envía una alerta por email cuando quedan pocos días |
| `13_inventario_infraestructura.py` | Genera un inventario completo del clúster (nodos, VMs, CTs) en formato JSON y CSV |

## Instalación

```bash
git clone https://github.com/lsserrano/proxmox-automation-toolkit.git
cd proxmox-automation-toolkit
pip install -r requirements.txt
```

Copia el archivo de ejemplo y rellena tus propios valores:

```bash
cp .env.example .env
```

Edita `.env` con tu editor favorito y completa, como mínimo, las credenciales de conexión:

```dotenv
PROXMOX_IP=192.168.0.100
PROXMOX_USER=root@pam
TOKEN_NAME=tu_token_id
TOKEN_SECRET=tu_token_secret
PROXMOX_NODE=pve
```

Cada script documenta en `.env.example` las variables adicionales que necesita.

## Uso

Cada script es independiente y se ejecuta directamente:

```bash
python 01_crear_usuario.py
python 08_control_estado_vm_ct.py
```

La configuración de cada ejecución se controla desde `.env` — no es necesario tocar el código para cambiar de usuario, VM/CT objetivo, o acción a realizar.

Todos los scripts siguen la misma convención de salida en consola:

```
[+] Operación correcta
[!] Aviso (p. ej. el recurso ya existía)
[-] Error
```

## Prácticas de seguridad aplicadas

- ✅ Autenticación por **token API dedicado**, no por usuario/contraseña directo
- ✅ Tokens con `privsep=1` (sin herencia automática de permisos del usuario)
- ✅ **RBAC explícito**: cada grupo/token recibe solo los permisos que necesita, sobre el path que necesita
- ✅ Cero credenciales hardcodeadas — todo vía `.env`, excluido de git
- ✅ Verificación TLS real (`verify_ssl=True`) con certificado propio gestionado
- ✅ Confirmación real de operaciones asíncronas (creación, clonación, arranque) en vez de esperas fijas (`sleep`)
- ✅ Manejo de errores explícito en cada llamada a la API, sin bloques `except` silenciosos

## Requisitos previos en Proxmox

- Un token API creado en *Datacenter → Permissions → API Tokens*
- Al menos una plantilla LXC descargada (*Storage → CT Templates*) para `05_crear_contenedor_lxc.py`
- Al menos una imagen ISO descargada (*Storage → ISO Images*) para `06_crear_vm.py`
- Un servidor SMTP (p. ej. Gmail con contraseña de aplicación) para `12_alerta_certificados_ssl.py`

## Próximos pasos

- Módulo común de conexión (`conexion.py`) para eliminar la duplicación entre scripts
- Integración con Grafana para visualizar las métricas exportadas por `04_configurar_metric_server.py`
- Automatización vía `cron` en el propio host de Proxmox para los scripts de mantenimiento (`11`, `12`)

## Autor

**lsserrano** — Técnico en Sistemas de Telecomunicaciones e Informáticos.
Proyecto desarrollado como parte de la preparación autodidacta previa a un máster en ciberseguridad.

[LinkedIn](https://www.linkedin.com/in/lsleoserrano) · [GitHub](https://github.com/lsserrano)
