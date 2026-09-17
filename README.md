k# NØXCAT V2

```text
        /\_/\\
       ( o.o )
        > ^ <

     N Ø X C A T
   Wi-Fi Manager
```

**Wi-Fi Adapter Manager for Kali Linux**

Herramienta de terminal para administrar, diagnosticar y reparar adaptadores Wi-Fi USB.

## FEATURES

* [+] Adapter Information
* [+] Driver Detection
* [+] Wi-Fi Modes
* [+] Bands & Channels
* [+] Wi-Fi Status
* [+] Wi-Fi Repair
* [+] Ethernet Status
* [+] Ethernet Repair
* [+] Network Diagnostics
* [+] NetworkManager Control

## INSTALL

### 1. Actualizar Kali

```bash
sudo apt update
sudo apt upgrade -y
```

### 2. Instalar requisitos

```bash
sudo apt install -y python3 network-manager iw iproute2 rfkill usbutils ethtool
```

### 3. Clonar NØXCAT V2

El repositorio es público. Usa HTTPS para no necesitar configurar una clave SSH:

```bash
git clone https://github.com/cabrera7551-cmyk/v2-Antena.git
```

### 4. Entrar al proyecto

```bash
cd v2-Antena
```

### 5. Ejecutar NØXCAT V2

```bash
sudo python3 main.py
```

## DEVICE

Actualmente probado con:

* **TP-Link Archer T2U PLUS**
* **Chipset:** RTL8821AU
* **USB ID:** `2357:0120`

NØXCAT V2 realiza detección del adaptador y diagnóstico del driver antes de realizar reparaciones.

## IMPORTANT

NØXCAT V2 está diseñado para administración y diagnóstico de adaptadores Wi-Fi en Kali Linux.

No es necesario instalar drivers externos de forma manual cuando el driver compatible ya está disponible en el sistema.

## AUTHOR

**Kevin Cabrera**

Cybersecurity • Linux • Networking

```text
        /\_/\\
       ( o.o )
        > ^ <

       NØXCAT V2
```

