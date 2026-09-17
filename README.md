k# TPLink-Adapter V2

```text
████████╗███████╗███╗   ███╗██████╗ ██╗███╗   ██╗
╚══██╔══╝██╔════╝████╗ ████║██╔══██╗██║████╗  ██║
   ██║   █████╗  ██╔████╔██║██████╔╝██║██╔██╗ ██║
   ██║   ██╔══╝  ██║╚██╔╝██║██╔══██╗██║██║╚██╗██║
   ██║   ███████╗██║ ╚═╝ ██║██║  ██║██║██║ ╚████║
   ╚═╝   ╚══════╝╚═╝     ╚═╝╚═╝  ╚═╝╚═══╝
```

### TP-Link Wi-Fi Adapter Manager

Herramienta para **administrar, diagnosticar y recuperar adaptadores Wi-Fi USB** en Kali Linux.

Diseñada especialmente para:

**TP-Link Archer T2U PLUS — RTL8821AU**

## Requisitos

* Kali Linux o distribución Linux compatible
* Python 3
* NetworkManager
* `iw`
* `ip`
* `rfkill`
* `lsusb`
* `ethtool`
* `modinfo`
* `lsmod`

## Instalación

Instalar los requisitos:

```bash
sudo apt update
sudo apt install python3 network-manager iw iproute2 rfkill usbutils ethtool
```

Clonar el repositorio:

```bash
git clone https://github.com/cabrera7551-cmyk/v2-Antena.git
```

Entrar al proyecto:

```bash
cd v2-Antena
```

Ejecutar:

```bash
sudo python3 main.py
```

## Funciones

* Información del adaptador
* Modos soportados
* Bandas y canales
* Estado del adaptador
* Diagnóstico
* Cambio de modo Wi-Fi
* Información del driver
* Estado y reparación de Wi-Fi
* Estado y reparación de Ethernet
* Diagnóstico general de red
* Gestión de NetworkManager

## Autor

**Kevin Cabrera**

---

### GitHub

https://github.com/cabrera7551-cmyk/v2-Antena

**TPLink-Adapter V2 • 2026**

