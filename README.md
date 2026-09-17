kk# ⚡ TPLink-Adapter V2

### AETHER // USB Wi-Fi Adapter Manager

> **Administración · Diagnóstico · Recuperación · Configuración**

Herramienta de administración y diagnóstico para adaptadores Wi-Fi USB en **Kali Linux**, diseñada para detectar dinámicamente hardware, interfaces, PHY, drivers y estado de red sin asumir nombres fijos de interfaz.

---

## 🛰️ ¿Qué es TPLink-Adapter?

**TPLink-Adapter V2** nace como una herramienta para centralizar la administración de adaptadores Wi-Fi USB desde una interfaz de terminal.

El proyecto está especialmente orientado al:

**TP-Link Archer T2U Plus**

```text
USB ID       : 2357:0120
Chipset      : Realtek RTL8821AU
Driver       : rtw88_8821au
Plataforma   : Kali Linux
```

La versión V2 incorpora detección dinámica, diagnóstico, recuperación y mecanismos de verificación para reducir cambios innecesarios sobre el resto de la red.

---

# 🧠 Filosofía del proyecto

TPLink-Adapter no intenta simplemente ejecutar comandos.

La idea es:

```text
        ┌──────────────────────┐
        │     TPLink-Adapter   │
        │          V2          │
        └──────────┬───────────┘
                   │
          ┌────────▼────────┐
          │    DETECCIÓN    │
          └────────┬────────┘
                   │
       ┌───────────┼───────────┐
       ▼           ▼           ▼
    HARDWARE    DRIVER       RED
       │           │           │
       └───────────┼───────────┘
                   ▼
             DIAGNÓSTICO
                   │
          ┌────────▼────────┐
          │    OPERACIÓN    │
          └────────┬────────┘
                   │
             VERIFICACIÓN
                   │
          ┌────────▼────────┐
          │  RECUPERACIÓN   │
          │   / ROLLBACK    │
          └─────────────────┘
```

Cada operación importante intenta comprobar el estado antes y después de realizar un cambio.

---

# ⚙️ Funcionalidades

## 🔎 Detección

* Detección de adaptadores USB Wi-Fi.
* Identificación de chipset.
* Identificación de driver.
* Identificación de firmware.
* Detección dinámica de interfaces.
* Detección dinámica de PHY.
* Detección del modo actual.
* Detección de modos soportados.

## 📡 Wi-Fi

* Información de SSID.
* BSSID.
* Señal.
* Canal.
* Frecuencia.
* Estado de conexión.
* Bandas disponibles.
* Canales soportados.
* Administración de la interfaz Wi-Fi.
* Cambio de modo de operación.

## 🛠️ Diagnóstico

El sistema analiza diferentes componentes:

```text
USB
 │
 ├── Adaptador
 ├── Chipset
 └── Identificación
       │
       ▼
Driver
 │
 ├── Módulo
 ├── Versión
 └── Firmware
       │
       ▼
Interfaz
 │
 ├── Estado
 ├── Modo
 ├── PHY
 └── MAC
       │
       ▼
Red
 │
 ├── IP
 ├── Gateway
 ├── DNS
 └── Conectividad
```

Los problemas encontrados se clasifican para facilitar su interpretación.

---

# 🔄 Recuperación

El proyecto incorpora funciones independientes para recuperación de:

* Wi-Fi.
* Ethernet.
* Interfaz de red.
* Conectividad.
* NetworkManager.

La recuperación de Wi-Fi está separada de Ethernet para evitar modificar innecesariamente una conexión cableada funcional.

---

# 🛡️ Cambio de modo seguro

Una de las características principales de V2 es el cambio de modo con comprobaciones.

Flujo:

```text
ESTADO ACTUAL
      │
      ▼
DETECTAR INTERFAZ
      │
      ▼
VERIFICAR MODOS
      │
      ▼
GUARDAR ESTADO
      │
      ▼
CAMBIAR MODO
      │
      ▼
VERIFICAR RESULTADO
      │
   ┌──┴──┐
   │     │
   ▼     ▼
 OK    ERROR
   │     │
   │     ▼
   │   ROLLBACK
   │     │
   └──┬──┘
      ▼
VERIFICACIÓN FINAL
```

Si una operación falla, el programa puede intentar devolver la interfaz a un estado funcional.

---

# 🌐 Separación Wi-Fi / Ethernet

El proyecto intenta mantener separadas las operaciones de cada interfaz.

Por ejemplo:

```text
             RED DEL EQUIPO
                   │
          ┌────────┴────────┐
          │                 │
        eth0              wlan0
      Ethernet             Wi-Fi
          │                 │
          │                 ├── Diagnóstico
          │                 ├── Reparación
          │                 └── Cambio de modo
          │
          └── Se mantiene independiente
```

El cambio de modo de Wi-Fi no requiere reiniciar NetworkManager globalmente.

El reinicio de NetworkManager existe como una opción independiente para situaciones en las que realmente sea necesario.

---

# 🧪 Hardware de referencia

### TP-Link Archer T2U Plus

```text
Fabricante : TP-Link
Modelo     : Archer T2U Plus
USB ID     : 2357:0120
Chipset    : Realtek RTL8821AU
Driver     : rtw88_8821au
```

> La compatibilidad puede variar dependiendo de la revisión física del adaptador, versión del kernel, firmware y distribución utilizada.

---

# 📦 Dependencias

No utiliza paquetes Python externos para su funcionamiento principal.

Requiere herramientas disponibles en Linux/Kali:

```text
Python 3
iw
ip
nmcli
rfkill
ethtool
lsusb
modinfo
lsmod
dmesg
journalctl
```

---

# 🚀 Instalación

Clonar el repositorio:

```bash
git clone https://github.com/cabrera7551-cmyk/v2-Antena.git
```

Entrar al directorio:

```bash
cd v2-Antena
```

Ejecutar:

```bash
sudo python3 main.py
```

---

# 🖥️ Uso

Al ejecutar el programa aparecerá el menú principal:

```text
AETHER CYBER CAT
TPLink-Adapter V2

1. Información del adaptador
2. Modos soportados
3. Bandas y canales
4. Estado del adaptador
5. Diagnóstico
6. Cambiar modo Wi-Fi
7. Driver Wi-Fi
8. Estado de Wi-Fi
9. Reparar Wi-Fi
10. Estado de Ethernet
11. Reparar Ethernet
12. Estado general de red
13. Reiniciar NetworkManager
14. Cambiar interfaz Wi-Fi administrada

0. Salir
```

---

# 🧩 Detección dinámica

El proyecto evita depender de nombres como:

```text
wlan0
wlan1
phy0
phy1
```

En su lugar, intenta descubrir dinámicamente las interfaces y dispositivos disponibles.

Esto permite trabajar con diferentes configuraciones de hardware y múltiples adaptadores Wi-Fi.

---

# 🧯 Manejo de errores

V2 incorpora mecanismos para reducir errores durante las operaciones:

* Validación de comandos.
* Timeouts.
* Manejo de excepciones.
* Comprobación del estado de interfaces.
* Verificación de modos soportados.
* Comprobación posterior a cambios.
* Recuperación.
* Rollback.
* Diagnóstico de conectividad.

---

# 🧪 Tests

Los tests se encuentran dentro de:

```text
tests/
```

Ejecutar el test básico:

```bash
python3 tests/test_basic.py
```

Comprobar sintaxis:

```bash
python3 tests/test_syntax.py
```

---

# 📁 Estructura

```text
TPLink-Adapter/
│
├── main.py
├── README.md
├── .gitignore
│
├── legacy/
│   └── main_old.py
│
├── src/
│   ├── models/
│   └── commands/
│
├── tests/
│   ├── test_basic.py
│   └── test_syntax.py
│
└── reports/
```

### Componentes

| Directorio | Función                 |
| ---------- | ----------------------- |
| `main.py`  | Aplicación principal    |
| `src/`     | Infraestructura modular |
| `tests/`   | Pruebas                 |
| `legacy/`  | Versiones anteriores    |
| `reports/` | Reportes generados      |

---

# 🔐 Seguridad y alcance

Este proyecto está orientado exclusivamente a:

* Administración Wi-Fi.
* Diagnóstico.
* Recuperación.
* Configuración.
* Mantenimiento.
* Pruebas sobre equipos propios o autorizados.

### No implementa

```text
✗ Captura de credenciales
✗ Phishing
✗ Evil Twin
✗ Deauthentication
✗ Cracking de contraseñas
✗ Robo de sesiones
✗ Bypass de autenticación
✗ Ataques contra redes
```

El proyecto se centra en **administración y diagnóstico del propio sistema y adaptador**.

---

# 🧬 Arquitectura V2

La versión V2 está orientada a separar responsabilidades:

```text
                    AETHER V2
                       │
        ┌──────────────┼──────────────┐
        │              │              │
     HARDWARE        DRIVER          NETWORK
        │              │              │
        └──────────────┼──────────────┘
                       │
                   INTERFACE
                       │
              ┌────────┴────────┐
              │                 │
            Wi-Fi            Ethernet
              │
       ┌──────┼──────┐
       │      │      │
    STATUS  REPAIR  MODE
                      │
                VERIFICATION
                      │
                   ROLLBACK
```

---

# 📌 Estado del proyecto

**Version:** `V2`

**Status:** 🟢 Active Development

El proyecto continúa evolucionando hacia una arquitectura más modular y una detección de hardware más robusta.

---

# 🗺️ Roadmap

### V2.x

* [x] Detección dinámica de interfaces.
* [x] Detección de PHY.
* [x] Información de driver.
* [x] Diagnóstico.
* [x] Recuperación Wi-Fi.
* [x] Recuperación Ethernet.
* [x] Cambio de modo.
* [x] Verificación posterior.
* [x] Rollback.
* [x] Separación Wi-Fi/Ethernet.

### Futuro

* [ ] Arquitectura modular completa.
* [ ] Sistema de logs.
* [ ] Exportación de diagnósticos.
* [ ] Mayor cobertura de adaptadores.
* [ ] Tests automatizados más completos.
* [ ] Detección avanzada de revisiones de hardware.

---

# 👨‍💻 Autor

**Kev / cabrera7551-cmyk**

Proyecto desarrollado como herramienta de administración y diagnóstico de adaptadores Wi-Fi USB sobre Linux.

---

## ⚡ TPLink-Adapter V2

```text
             /\_/\
            ( o.o )
             > ^ <

        AETHER // V2

   DETECT  •  DIAGNOSE
   REPAIR  •  VERIFY
```

**Know your hardware.
Understand your network.
Control your adapter.**

