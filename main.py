#!/usr/bin/env python3

import os
import re
import shutil
import signal
import subprocess
import time

# ============================================================
# AETHER / TP-LINK ADAPTER MANAGER
# Wi-Fi + Ethernet + diagnóstico + reparación de red
# ============================================================

BLUE = "\033[94m"
WHITE = "\033[97m"
YELLOW = "\033[93m"
RED = "\033[91m"
GREEN = "\033[92m"
RESET = "\033[0m"

# ============================================================
# BANNER
# ============================================================

BANNER = r"""
███╗   ██╗ ██████╗ ██╗  ██╗ ██████╗ █████╗ ████████╗
████╗  ██║██╔═══██╗╚██╗██╔╝██╔════╝██╔══██╗╚══██╔══╝
██╔██╗ ██║██║   ██║ ╚███╔╝ ██║     ███████║   ██║
██║╚██╗██║██║   ██║ ██╔██╗ ██║     ██╔══██║   ██║
██║ ╚████║╚██████╔╝██╔╝ ██╗╚██████╗██║  ██║   ██║
╚═╝  ╚═══╝ ╚═════╝ ╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝   ╚═╝

                         /\_/\\
                        ( o.o )
                         > ^ <

                    NØXCAT V2
              Wi-Fi Adapter Manager
"""
# ============================================================
# BASE DE DATOS DE ADAPTADORES
# ============================================================

ADAPTER_DATABASE = {
    "2357:0120": {
        "model": "TP-Link Archer T2U PLUS",
        "chipset": "RTL8821AU",
        "driver": "rtw88_8821au",
        "package": "firmware-realtek",
    }
}

MODE_DESCRIPTIONS = {
    "managed": "Conectarse normalmente a una red Wi-Fi.",
    "monitor": "Modo de monitorización del adaptador.",
    "AP": "Funcionamiento como punto de acceso.",
    "AP/VLAN": "Interfaz virtual asociada a un AP.",
    "IBSS": "Red Wi-Fi ad-hoc.",
}

PREFERRED_MODE_ORDER = [
    "managed",
    "monitor",
    "AP",
    "IBSS",
    "AP/VLAN",
]

COMPATIBLE_DRIVER_PATTERNS = {
    "RTL8821AU": [
        r"rtw88",
        r"8821au",
        r"rtl8821au",
    ],
}

_SELECTED_INTERFACE = None


# ============================================================
# UTILIDADES
# ============================================================

def clear():
    os.system("clear")


def pause():
    input(
        f"\n{WHITE}Presiona {YELLOW}ENTER{RESET}"
        f"{WHITE} para continuar...{RESET}"
    )


def separator():
    print(f"{BLUE}{'═' * 41}{RESET}")


def header(title):
    clear()
    separator()
    print(f"{WHITE}{title:^41}{RESET}")
    separator()
    print()


def run_argv(args, timeout=30):
    try:
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=timeout
        )

        output = result.stdout.strip()

        if result.stderr.strip():
            output = (
                f"{output}\n{result.stderr.strip()}"
                if output
                else result.stderr.strip()
            )

        return result.returncode, output

    except subprocess.TimeoutExpired:
        return 1, "Command timeout"

    except FileNotFoundError:
        return 1, "Command not found"

    except Exception as e:
        return 1, str(e)


def command_exists(command):
    return shutil.which(command) is not None


def ok(msg):
    print(f"{GREEN}  [OK]{RESET} {WHITE}{msg}{RESET}")


def err(msg):
    print(f"{RED}  [ERROR]{RESET} {WHITE}{msg}{RESET}")


def warn(msg):
    print(f"{YELLOW}  [WARNING]{RESET} {WHITE}{msg}{RESET}")


def info(label, value, value_color=YELLOW):
    print(
        f"{WHITE}{label}{RESET} "
        f"{value_color}{value}{RESET}"
    )


def exit_program(signum=None, frame=None):
    print(
        f"\n{RED}⚡{RESET} "
        f"{YELLOW}Saliendo del sistema...{RESET}"
    )
    raise SystemExit


signal.signal(signal.SIGINT, exit_program)


# ============================================================
# USB / ADAPTADOR
# ============================================================

def get_usb_devices():
    if not command_exists("lsusb"):
        return []

    code, output = run_argv(["lsusb"])

    if code != 0:
        return []

    devices = []

    for line in output.splitlines():
        match = re.search(
            r"ID\s+([0-9a-fA-F]{4}:[0-9a-fA-F]{4})\s+(.*)",
            line
        )

        if match:
            devices.append({
                "id": match.group(1).lower(),
                "description": match.group(2).strip()
            })

    return devices


def get_tp_link_usb():
    for device in get_usb_devices():
        if device["id"].startswith("2357:"):
            return device

    return None


def get_adapter_info():
    usb = get_tp_link_usb()

    if usb:
        usb_id = usb["id"]

        if usb_id in ADAPTER_DATABASE:
            data = ADAPTER_DATABASE[usb_id].copy()
            data["usb_id"] = usb_id
            data["usb_description"] = usb["description"]
            return data

        return {
            "usb_id": usb_id,
            "usb_description": usb["description"],
            "model": "TP-Link no registrado",
            "chipset": "Desconocido",
            "driver": "Desconocido",
            "package": "Desconocido",
        }

    return {
        "usb_id": "No detectado",
        "usb_description": "No detectado",
        "model": "No detectado",
        "chipset": "No detectado",
        "driver": "No detectado",
        "package": "No detectado",
    }


# ============================================================
# INTERFACES WI-FI
# ============================================================

def get_all_wireless_interfaces():
    if not command_exists("iw"):
        return []

    code, output = run_argv(["iw", "dev"])

    if code != 0:
        return []

    interfaces = []

    for line in output.splitlines():
        if line.strip().startswith("Interface "):
            parts = line.strip().split()

            if len(parts) >= 2:
                iface = parts[1]

                if iface not in interfaces:
                    interfaces.append(iface)

    return interfaces


def choose_wireless_interface(interfaces):
    global _SELECTED_INTERFACE

    header("VARIAS INTERFACES WI-FI DETECTADAS")

    for idx, iface in enumerate(interfaces, 1):
        print(
            f"{BLUE}[{idx}]{RESET} "
            f"{WHITE}{iface}{RESET} "
            f"MAC: {BLUE}{get_mac(iface)}{RESET}"
        )

    choice = input(
        f"\n{YELLOW}>{RESET} "
        f"{WHITE}¿Cuál interfaz deseas administrar?:{RESET} "
    ).strip()

    if choice.isdigit() and 1 <= int(choice) <= len(interfaces):
        _SELECTED_INTERFACE = interfaces[int(choice) - 1]

    else:
        _SELECTED_INTERFACE = interfaces[0]

        warn(
            f"Opción inválida, usando "
            f"{_SELECTED_INTERFACE}."
        )

    return _SELECTED_INTERFACE


def get_wireless_interface():
    global _SELECTED_INTERFACE

    interfaces = get_all_wireless_interfaces()

    if not interfaces:
        _SELECTED_INTERFACE = None
        return None

    if len(interfaces) == 1:
        _SELECTED_INTERFACE = interfaces[0]
        return _SELECTED_INTERFACE

    if _SELECTED_INTERFACE in interfaces:
        return _SELECTED_INTERFACE

    return choose_wireless_interface(interfaces)


def change_managed_interface():
    global _SELECTED_INTERFACE

    header("CAMBIAR INTERFAZ WI-FI ADMINISTRADA")

    interfaces = get_all_wireless_interfaces()

    if not interfaces:
        err("No se detectaron interfaces Wi-Fi.")
        pause()
        return

    if len(interfaces) == 1:
        _SELECTED_INTERFACE = interfaces[0]

        info(
            "Interfaz seleccionada:",
            interfaces[0],
            BLUE
        )

        pause()
        return

    selected = choose_wireless_interface(interfaces)

    ok(
        f"Ahora se administrará: "
        f"{selected}"
    )

    pause()


# ============================================================
# INFORMACIÓN DE INTERFAZ
# ============================================================

def get_phy(interface):
    if not interface:
        return "Desconocido"

    code, output = run_argv(["iw", "dev"])

    if code != 0:
        return "Desconocido"

    current_phy = None

    for line in output.splitlines():
        stripped = line.strip()

        if stripped.startswith("phy#"):
            current_phy = stripped.replace(
                "phy#",
                "phy",
                1
            )

        elif stripped.startswith("Interface ") and current_phy:
            parts = stripped.split()

            if len(parts) >= 2 and parts[1] == interface:
                return current_phy

    return "Desconocido"


def get_mac(interface):
    if not interface:
        return "Desconocida"

    try:
        with open(
            f"/sys/class/net/{interface}/address",
            "r",
            encoding="utf-8"
        ) as f:
            return f.read().strip()

    except Exception:
        return "Desconocida"


def get_ipv4(interface):
    if not interface:
        return None

    code, output = run_argv([
        "ip",
        "-4",
        "addr",
        "show",
        "dev",
        interface
    ])

    if code != 0:
        return None

    match = re.search(
        r"\binet\s+(\d+\.\d+\.\d+\.\d+)",
        output
    )

    return match.group(1) if match else None


def get_carrier(interface):
    if not interface:
        return "Desconocido"

    try:
        with open(
            f"/sys/class/net/{interface}/carrier",
            "r",
            encoding="utf-8"
        ) as f:
            value = f.read().strip()

        if value == "1":
            return "OK"

        if value == "0":
            return "NO-CARRIER"

    except Exception:
        pass

    return "Desconocido"


def get_interface_state(interface):
    if not interface:
        return "Desconocido"

    try:
        with open(
            f"/sys/class/net/{interface}/operstate",
            "r",
            encoding="utf-8"
        ) as f:
            return f.read().strip().upper()

    except Exception:
        return "Desconocido"


def get_current_mode(interface):
    if not interface:
        return "Desconocido"

    code, output = run_argv([
        "iw",
        "dev",
        interface,
        "info"
    ])

    if code != 0:
        return "Desconocido"

    match = re.search(
        r"\btype\s+(\S+)",
        output
    )

    return match.group(1) if match else "Desconocido"


def get_driver(interface):
    if not interface or not command_exists("ethtool"):
        return "Desconocido"

    code, output = run_argv([
        "ethtool",
        "-i",
        interface
    ])

    if code != 0:
        return "Desconocido"

    match = re.search(
        r"^driver:\s*(.+)$",
        output,
        re.MULTILINE
    )

    return match.group(1).strip() if match else "Desconocido"


def get_driver_version(interface):
    if not interface or not command_exists("ethtool"):
        return "Desconocida"

    code, output = run_argv([
        "ethtool",
        "-i",
        interface
    ])

    if code != 0:
        return "Desconocida"

    match = re.search(
        r"^version:\s*(.+)$",
        output,
        re.MULTILINE
    )

    return match.group(1).strip() if match else "Desconocida"


def get_firmware(interface):
    if not interface or not command_exists("ethtool"):
        return "No disponible"

    code, output = run_argv([
        "ethtool",
        "-i",
        interface
    ])

    if code != 0:
        return "No disponible"

    match = re.search(
        r"^firmware-version:\s*(.+)$",
        output,
        re.MULTILINE
    )

    return match.group(1).strip() if match else "No disponible"


# ============================================================
# MODOS SOPORTADOS
# ============================================================

def get_supported_modes(interface):
    phy = get_phy(interface)

    if phy == "Desconocido":
        return []

    code, output = run_argv([
        "iw",
        "phy",
        phy,
        "info"
    ])

    if code != 0:
        return []

    modes = []
    reading = False

    for line in output.splitlines():
        stripped = line.strip()

        if stripped == "Supported interface modes:":
            reading = True
            continue

        if reading:
            if stripped.startswith("*"):
                mode = stripped.replace("*", "", 1).strip()

                if mode and mode not in modes:
                    modes.append(mode)

            elif stripped:
                break

    return modes


def ordered_supported_modes(interface):
    supported = get_supported_modes(interface)

    ordered = [
        mode
        for mode in PREFERRED_MODE_ORDER
        if mode in supported
    ]

    ordered += [
        mode
        for mode in supported
        if mode not in ordered
    ]

    return ordered


def nm_manages_interface_check(interface):
    if not interface or not command_exists("nmcli"):
        return False

    code, output = run_argv([
        "nmcli",
        "-t",
        "-f",
        "GENERAL.STATE",
        "device",
        "show",
        interface
    ])

    if code != 0:
        return False

    return "unmanaged" not in output.lower()


# ============================================================
# RUTA ACTUAL DE INTERNET
# ============================================================

def get_default_route_info():
    code, output = run_argv([
        "ip",
        "route",
        "get",
        "1.1.1.1"
    ])

    if code != 0 or not output:
        return None

    interface_match = re.search(
        r"\bdev\s+(\S+)",
        output
    )

    gateway_match = re.search(
        r"\bvia\s+(\S+)",
        output
    )

    source_match = re.search(
        r"\bsrc\s+(\S+)",
        output
    )

    return {
        "interface": (
            interface_match.group(1)
            if interface_match
            else None
        ),
        "gateway": (
            gateway_match.group(1)
            if gateway_match
            else None
        ),
        "source": (
            source_match.group(1)
            if source_match
            else None
        ),
        "raw": output,
    }


def get_default_gateway(interface=None):
    args = [
        "ip",
        "route",
        "show",
        "default"
    ]

    if interface:
        args += [
            "dev",
            interface
        ]

    code, output = run_argv(args)

    if code != 0:
        return None

    match = re.search(
        r"default\s+via\s+(\S+)",
        output
    )

    return match.group(1) if match else None


# ============================================================
# CONEXIÓN WI-FI CON NETWORKMANAGER
# ============================================================

def reconnect_wifi_connection(interface):
    """
    Intenta devolver la interfaz Wi-Fi a una conexión normal.

    IMPORTANTE:
    - No reinicia NetworkManager.
    - No modifica Ethernet.
    - Solo trabaja con la interfaz indicada.
    """

    if not interface:
        return False

    if not command_exists("nmcli"):
        warn("nmcli no está instalado.")
        return False

    print(
        f"{YELLOW}"
        f"Intentando reconectar {interface}..."
        f"{RESET}"
    )

    # Primero aseguramos que la interfaz esté arriba.
    run_argv([
        "sudo",
        "ip",
        "link",
        "set",
        interface,
        "up"
    ])

    time.sleep(1)

    # Método principal.
    code, output = run_argv(
        [
            "sudo",
            "nmcli",
            "device",
            "up",
            interface
        ],
        timeout=30
    )

    if code == 0:
        ok(
            f"NetworkManager activó "
            f"{interface}."
        )
        return True

    if output:
        print(
            f"{YELLOW}"
            f"{output}"
            f"{RESET}"
        )

    # Segundo intento: nmcli device connect.
    code, output = run_argv(
        [
            "sudo",
            "nmcli",
            "device",
            "connect",
            interface
        ],
        timeout=30
    )

    if code == 0:
        ok(
            f"{interface} fue conectada "
            f"por NetworkManager."
        )
        return True

    # Tercer intento:
    # buscar perfiles Wi-Fi guardados.
    code, output = run_argv([
        "nmcli",
        "-t",
        "-f",
        "NAME,TYPE",
        "connection",
        "show"
    ])

    if code != 0:
        return False

    profiles = []

    for line in output.splitlines():
        parts = line.rsplit(":", 1)

        if len(parts) != 2:
            continue

        name, conn_type = parts

        if conn_type == "802-11-wireless":
            profiles.append(name)

    for profile in profiles:
        print(
            f"{WHITE}"
            f"Probando perfil guardado: "
            f"{profile}"
            f"{RESET}"
        )

        code, output = run_argv(
            [
                "sudo",
                "nmcli",
                "connection",
                "up",
                "id",
                profile,
                "ifname",
                interface
            ],
            timeout=30
        )

        if code == 0:
            ok(
                f"Perfil Wi-Fi activado: "
                f"{profile}"
            )
            return True

    return False


# ============================================================
# CAMBIO DE MODO WI-FI
# ============================================================

def change_mode(target_mode):
    interface = get_wireless_interface()

    if not interface:
        err("No se detectó el adaptador.")
        return False

    supported = get_supported_modes(interface)

    if target_mode not in supported:
        err(
            f"El modo {target_mode} "
            f"no está soportado."
        )
        return False

    current = get_current_mode(interface)

    route_before = get_default_route_info()

    print()

    info(
        "Interfaz Wi-Fi:",
        interface,
        BLUE
    )

    info(
        "Modo actual:",
        current,
        YELLOW
    )

    info(
        "Modo solicitado:",
        target_mode,
        GREEN
    )

    if route_before:
        info(
            "Internet actualmente por:",
            route_before["interface"],
            GREEN
        )

    print()

    if current.lower() == target_mode.lower():

        ok(
            "El adaptador ya está "
            "en este modo."
        )

        # Si ya está managed, aprovechamos
        # para comprobar la conexión.
        if target_mode == "managed":
            if not get_wifi_connection_details(interface):
                warn(
                    "Está en managed pero no está "
                    "asociado a una red."
                )

                if reconnect_wifi_connection(interface):
                    time.sleep(3)

                    if get_wifi_connection_details(
                        interface
                    ):
                        ok(
                            "La conexión Wi-Fi "
                            "fue restaurada."
                        )

        return True

    if target_mode == "AP/VLAN":
        warn(
            "AP/VLAN es una interfaz "
            "virtual asociada a un AP."
        )
        return False

    # --------------------------------------------------------
    # PROTECCIÓN DE LA RUTA
    # --------------------------------------------------------

    if (
        route_before
        and route_before["interface"] == interface
        and target_mode != "managed"
    ):
        warn(
            "La Wi-Fi es actualmente "
            "la salida a Internet."
        )

        warn(
            "Al cambiar de managed a otro "
            "modo, esa conexión se perderá."
        )

        choice = input(
            f"\n{YELLOW}>{RESET} "
            f"{WHITE}"
            "¿Continuar? (s/n):"
            f"{RESET} "
        ).strip().lower()

        if choice != "s":
            warn("Operación cancelada.")
            return False

    managed_by_nm = nm_manages_interface_check(
        interface
    )

    # --------------------------------------------------------
    # SOLO DESCONECTAMOS LA WI-FI
    # --------------------------------------------------------

    if managed_by_nm:

        print(
            f"{YELLOW}"
            f"Desconectando solamente "
            f"{interface} de NetworkManager..."
            f"{RESET}"
        )

        run_argv([
            "sudo",
            "nmcli",
            "device",
            "disconnect",
            interface
        ])

        time.sleep(1)

    # --------------------------------------------------------
    # CAMBIO DE MODO
    # --------------------------------------------------------

    commands = [
        [
            "sudo",
            "ip",
            "link",
            "set",
            interface,
            "down"
        ],
        [
            "sudo",
            "iw",
            "dev",
            interface,
            "set",
            "type",
            target_mode
        ],
        [
            "sudo",
            "ip",
            "link",
            "set",
            interface,
            "up"
        ],
    ]

    for command in commands:

        code, output = run_argv(command)

        if code != 0:

            err(
                "Falló: "
                + " ".join(command)
            )

            if output:
                print(output)

            # ------------------------------------------------
            # RECUPERACIÓN SOLO DE WI-FI
            # ------------------------------------------------

            print(
                f"{YELLOW}"
                f"Intentando devolver "
                f"{interface} a managed..."
                f"{RESET}"
            )

            run_argv([
                "sudo",
                "iw",
                "dev",
                interface,
                "set",
                "type",
                "managed"
            ])

            run_argv([
                "sudo",
                "ip",
                "link",
                "set",
                interface,
                "up"
            ])

            if managed_by_nm:
                reconnect_wifi_connection(
                    interface
                )

            return False

    time.sleep(1)

    new_mode = get_current_mode(interface)

    if new_mode.lower() != target_mode.lower():

        err(
            "El kernel/driver no confirmó "
            "el modo solicitado."
        )

        # Recuperación Wi-Fi solamente.
        run_argv([
            "sudo",
            "iw",
            "dev",
            interface,
            "set",
            "type",
            "managed"
        ])

        run_argv([
            "sudo",
            "ip",
            "link",
            "set",
            interface,
            "up"
        ])

        if managed_by_nm:
            reconnect_wifi_connection(
                interface
            )

        return False

    ok(
        f"Modo cambiado correctamente "
        f"a {new_mode}."
    )

    # --------------------------------------------------------
    # SI VOLVEMOS A MANAGED:
    # RECONEXIÓN REAL DE WI-FI
    # --------------------------------------------------------

    if (
        target_mode == "managed"
        and managed_by_nm
    ):

        print()

        ok(
            "Interfaz devuelta a managed."
        )

        if reconnect_wifi_connection(interface):
            time.sleep(3)

            details = get_wifi_connection_details(
                interface
            )

            if details:

                ok(
                    "Wi-Fi reconectada "
                    "correctamente."
                )

                info(
                    "SSID:",
                    details["ssid"],
                    WHITE
                )

            else:

                warn(
                    "NetworkManager activó "
                    "la interfaz, pero todavía "
                    "no hay asociación Wi-Fi."
                )

        else:

            warn(
                "No se pudo activar "
                "automáticamente una conexión Wi-Fi."
            )

            warn(
                "La interfaz está en managed; "
                "puedes usar 'Reparar Wi-Fi'."
            )

    # --------------------------------------------------------
    # COMPROBAR RUTA
    # --------------------------------------------------------

    time.sleep(1)

    route_after = get_default_route_info()

    print()

    if route_before and route_after:

        if (
            route_before["interface"]
            == route_after["interface"]
        ):

            ok(
                "La interfaz de Internet "
                "se mantuvo sin cambios."
            )

        else:

            warn(
                "La ruta de Internet cambió "
                f"de {route_before['interface']} "
                f"a {route_after['interface']}."
            )

    elif route_before and not route_after:

        warn(
            "La ruta de Internet desapareció "
            "después del cambio de modo."
        )

    elif not route_before and route_after:

        info(
            "Nueva interfaz de Internet:",
            route_after["interface"],
            GREEN
        )

    return True


# ============================================================
# BANDAS / CANALES
# ============================================================

def classify_band(freq):
    if 2400 <= freq <= 2500:
        return "2.4 GHz"

    if 4900 <= freq <= 5900:
        return "5 GHz"

    if 5925 <= freq <= 7125:
        return "6 GHz"

    return None


def get_band_information(interface):

    result = {
        "2.4 GHz": {
            "channels": [],
            "widths": []
        },
        "5 GHz": {
            "channels": [],
            "widths": []
        },
        "6 GHz": {
            "channels": [],
            "widths": []
        },
    }

    phy = get_phy(interface)

    if phy == "Desconocido":
        return result

    code, output = run_argv([
        "iw",
        "phy",
        phy,
        "info"
    ])

    if code != 0:
        return result

    blocks = re.split(
        r"\n(?=\s*Band\s+\d+:)",
        output
    )

    for block in blocks:

        widths = []
        channels = []

        if "HT Capabilities" in block:
            if "20 MHz" not in widths:
                widths.append("20 MHz")

        if "HT20/HT40" in block:
            if "40 MHz" not in widths:
                widths.append("40 MHz")

        if "VHT Capabilities" in block:
            if "80 MHz" not in widths:
                widths.append("80 MHz")

        if "HE Capabilities" in block:
            if "160 MHz" in block:
                if "160 MHz" not in widths:
                    widths.append("160 MHz")

        for line in block.splitlines():

            if "[disabled]" in line:
                continue

            match = re.search(
                r"(\d{4,5}(?:\.\d+)?)\s+MHz\s+\[(\d+)\]",
                line
            )

            if not match:
                continue

            freq = float(match.group(1))
            channel = int(match.group(2))

            band = classify_band(freq)

            if band:
                channels.append(
                    (band, channel)
                )

        for band, channel in channels:

            if channel not in result[band]["channels"]:
                result[band]["channels"].append(
                    channel
                )

            for width in widths:

                if width not in result[band]["widths"]:
                    result[band]["widths"].append(
                        width
                    )

    for band in result:
        result[band]["channels"].sort()

    return result


def get_current_channel(interface):

    if not interface:
        return "Desconocido"

    code, output = run_argv([
        "iw",
        "dev",
        interface,
        "link"
    ])

    match = re.search(
        r"\bfreq:\s*(\d+)",
        output
    )

    if match:

        freq = int(match.group(1))

        if freq == 2484:
            return "14"

        if 2412 <= freq <= 2472:
            return str(
                (freq - 2407) // 5
            )

        if 5000 <= freq <= 5900:
            return str(
                (freq - 5000) // 5
            )

    code, output = run_argv([
        "iw",
        "dev",
        interface,
        "info"
    ])

    match = re.search(
        r"\bchannel\s+(\d+)",
        output
    )

    if match:
        return match.group(1)

    return "No disponible"


# ============================================================
# RED
# ============================================================

def get_all_interfaces():

    code, output = run_argv([
        "ip",
        "-o",
        "link",
        "show"
    ])

    if code != 0:
        return []

    interfaces = []

    for line in output.splitlines():

        match = re.match(
            r"\d+:\s+([^:]+):",
            line
        )

        if not match:
            continue

        iface = match.group(1).split("@")[0]

        if iface == "lo":
            continue

        if iface not in interfaces:
            interfaces.append(iface)

    return interfaces


def get_ethernet_interfaces():

    ethernet = []

    wireless = get_all_wireless_interfaces()

    for interface in get_all_interfaces():

        if interface == "lo":
            continue

        if interface in wireless:
            continue

        if interface.startswith(
            (
                "vir",
                "docker",
                "br-",
                "veth",
                "tun",
                "tap"
            )
        ):
            continue

        path = f"/sys/class/net/{interface}/type"

        try:

            with open(
                path,
                "r",
                encoding="utf-8"
            ) as file:

                interface_type = file.read().strip()

            if interface_type == "1":
                ethernet.append(interface)

        except Exception:
            continue

    return ethernet


def get_ethernet_interface():

    interfaces = get_ethernet_interfaces()

    if not interfaces:
        return None

    if "eth0" in interfaces:
        return "eth0"

    return interfaces[0]


# ============================================================
# DNS / INTERNET
# ============================================================

def get_dns_servers():

    servers = []

    if command_exists("resolvectl"):

        code, output = run_argv([
            "resolvectl",
            "status"
        ])

        if code == 0:

            for line in output.splitlines():

                match = re.search(
                    r"DNS Servers:\s*(.+)",
                    line
                )

                if match:
                    servers.extend(
                        match.group(1).split()
                    )

    if not servers:

        try:

            with open(
                "/etc/resolv.conf",
                "r",
                encoding="utf-8"
            ) as f:

                for line in f:

                    if line.strip().startswith(
                        "nameserver"
                    ):

                        parts = line.split()

                        if len(parts) >= 2:
                            servers.append(
                                parts[1]
                            )

        except Exception:
            pass

    return list(
        dict.fromkeys(servers)
    )


def check_internet():

    code, output = run_argv(
        [
            "ping",
            "-c",
            "1",
            "-W",
            "3",
            "1.1.1.1"
        ],
        timeout=8
    )

    return code == 0


def check_dns(hostname="google.com"):

    if not command_exists("getent"):
        return False

    code, output = run_argv(
        [
            "getent",
            "hosts",
            hostname
        ],
        timeout=8
    )

    return code == 0


# ============================================================
# INFORMACIÓN WI-FI
# ============================================================

def get_wifi_connection_details(interface):

    if not interface:
        return None

    code, output = run_argv([
        "iw",
        "dev",
        interface,
        "link"
    ])

    if code != 0 or not output:
        return None

    if "Not connected" in output:
        return None

    if "Not associated" in output:
        return None

    details = {}

    match = re.search(
        r"Connected to ([0-9a-fA-F:]{17})",
        output
    )

    details["bssid"] = (
        match.group(1)
        if match
        else "Desconocido"
    )

    match = re.search(
        r"SSID:\s*(.+)",
        output
    )

    details["ssid"] = (
        match.group(1).strip()
        if match
        else "Desconocido"
    )

    match = re.search(
        r"freq:\s*(\d+)",
        output
    )

    details["frequency"] = (
        f"{match.group(1)} MHz"
        if match
        else "Desconocida"
    )

    match = re.search(
        r"signal:\s*(-?\d+)\s*dBm",
        output
    )

    details["signal"] = (
        f"{match.group(1)} dBm"
        if match
        else "Desconocida"
    )

    match = re.search(
        r"tx bitrate:\s*([^\n]+)",
        output
    )

    details["tx_bitrate"] = (
        match.group(1).strip()
        if match
        else "Desconocido"
    )

    match = re.search(
        r"rx bitrate:\s*([^\n]+)",
        output
    )

    details["rx_bitrate"] = (
        match.group(1).strip()
        if match
        else "Desconocido"
    )

    details["channel"] = get_current_channel(
        interface
    )

    return details


# ============================================================
# ESTADO DE WI-FI
# ============================================================

def wifi_status():

    header("ESTADO DE WI-FI")

    interface = get_wireless_interface()

    if not interface:
        err(
            "No se detectó una interfaz Wi-Fi."
        )
        pause()
        return

    route = get_default_route_info()

    details = get_wifi_connection_details(
        interface
    )

    info(
        "Interfaz:",
        interface,
        BLUE
    )

    info(
        "Estado:",
        get_interface_state(interface),
        GREEN
    )

    info(
        "Carrier:",
        get_carrier(interface),
        GREEN
    )

    info(
        "Modo:",
        get_current_mode(interface),
        YELLOW
    )

    info(
        "IPv4:",
        get_ipv4(interface)
        or "Sin IPv4",
        WHITE
    )

    print()

    if details:

        ok("Wi-Fi conectada.")

        info(
            "SSID:",
            details["ssid"],
            WHITE
        )

        info(
            "BSSID:",
            details["bssid"],
            BLUE
        )

        info(
            "Frecuencia:",
            details["frequency"],
            BLUE
        )

        info(
            "Canal:",
            details["channel"],
            BLUE
        )

        info(
            "Señal:",
            details["signal"],
            YELLOW
        )

        info(
            "RX bitrate:",
            details["rx_bitrate"],
            GREEN
        )

        info(
            "TX bitrate:",
            details["tx_bitrate"],
            GREEN
        )

    else:

        warn(
            "La interfaz no está asociada "
            "a una red Wi-Fi."
        )

    print()

    if route:

        if route["interface"] == interface:

            ok(
                "Esta interfaz es la salida "
                "actual a Internet."
            )

        else:

            info(
                "Internet sale por:",
                route["interface"],
                GREEN
            )

    else:

        warn(
            "No se detectó ruta hacia Internet."
        )

    pause()


# ============================================================
# REPARAR WI-FI
# ============================================================

def repair_wifi():

    header("REPARAR WI-FI")

    interface = get_wireless_interface()

    if not interface:

        err(
            "No se detectó una interfaz Wi-Fi."
        )

        pause()
        return

    route_before = get_default_route_info()

    info(
        "Interfaz Wi-Fi:",
        interface,
        BLUE
    )

    if route_before:

        info(
            "Internet actualmente por:",
            route_before["interface"],
            GREEN
        )

    print()

    if (
        route_before
        and route_before["interface"] != interface
    ):

        ok(
            "Internet está saliendo por otra "
            "interfaz; se protegerá esa conexión."
        )

    elif (
        route_before
        and route_before["interface"] == interface
    ):

        warn(
            "La Wi-Fi es actualmente "
            "la conexión de Internet."
        )

    print()

    mode = get_current_mode(interface)

    if mode != "managed":

        warn(
            f"{interface} está en modo "
            f"{mode}."
        )

        supported = get_supported_modes(
            interface
        )

        if "managed" not in supported:

            err(
                "El driver no reporta "
                "modo managed."
            )

            pause()
            return

        if not change_mode("managed"):

            err(
                "No se pudo devolver "
                "la interfaz a managed."
            )

            pause()
            return

    run_argv([
        "sudo",
        "ip",
        "link",
        "set",
        interface,
        "up"
    ])

    time.sleep(1)

    # --------------------------------------------------------
    # RECONEXIÓN REAL
    # --------------------------------------------------------

    connected = reconnect_wifi_connection(
        interface
    )

    time.sleep(3)

    details = get_wifi_connection_details(
        interface
    )

    print()

    if details:

        ok(
            f"{interface} está conectada."
        )

        info(
            "SSID:",
            details["ssid"],
            WHITE
        )

        info(
            "BSSID:",
            details["bssid"],
            BLUE
        )

    elif connected:

        warn(
            "NetworkManager activó la interfaz, "
            "pero no se confirmó asociación Wi-Fi."
        )

    else:

        warn(
            f"{interface} todavía no está "
            "asociada a una red."
        )

    route_after = get_default_route_info()

    print()

    if route_before and route_after:

        if (
            route_before["interface"]
            == route_after["interface"]
        ):

            ok(
                "La ruta de Internet "
                "se mantuvo igual."
            )

        else:

            warn(
                "La ruta cambió de "
                f"{route_before['interface']} "
                f"a {route_after['interface']}."
            )

    if check_internet():

        ok(
            "Internet responde."
        )

    else:

        warn(
            "Internet no responde "
            "por el momento."
        )

    pause()


# ============================================================
# ESTADO DE ETHERNET
# ============================================================

def ethernet_status():

    header("ESTADO DE ETHERNET")

    ethernet_interfaces = (
        get_ethernet_interfaces()
    )

    if not ethernet_interfaces:

        err(
            "No se detectaron interfaces "
            "Ethernet físicas."
        )

        pause()
        return

    route = get_default_route_info()

    for interface in ethernet_interfaces:

        state = get_interface_state(
            interface
        )

        carrier = get_carrier(
            interface
        )

        ip4 = get_ipv4(
            interface
        )

        gateway = get_default_gateway(
            interface
        )

        print(
            f"{WHITE}{interface}{RESET}"
        )

        info(
            "  Estado:",
            state,
            GREEN if state == "UP" else RED
        )

        info(
            "  Carrier:",
            carrier,
            GREEN if carrier == "OK" else YELLOW
        )

        info(
            "  IPv4:",
            ip4 or "Sin IPv4",
            GREEN if ip4 else RED
        )

        info(
            "  Gateway:",
            gateway or "No detectado",
            WHITE
        )

        if route:

            if route["interface"] == interface:

                ok(
                    "Esta interfaz es la "
                    "salida actual a Internet."
                )

        print()

    if route:

        info(
            "Interfaz de Internet:",
            route["interface"]
            or "No detectada",
            GREEN
        )

        info(
            "Gateway:",
            route["gateway"]
            or "No detectado",
            WHITE
        )

        info(
            "IP origen:",
            route["source"]
            or "No detectada",
            WHITE
        )

    else:

        warn(
            "No existe una ruta actual "
            "hacia Internet."
        )

    print()

    if check_internet():

        ok(
            "Internet responde."
        )

    else:

        warn(
            "Internet no responde."
        )

    pause()


# ============================================================
# REPARAR ETHERNET
# ============================================================

def repair_ethernet():

    header("REPARAR ETHERNET")

    ethernet_interfaces = (
        get_ethernet_interfaces()
    )

    if not ethernet_interfaces:

        err(
            "No se detectaron interfaces "
            "Ethernet."
        )

        pause()
        return

    route_before = get_default_route_info()

    print(
        f"{WHITE}Interfaces Ethernet:{RESET}\n"
    )

    for interface in ethernet_interfaces:

        info(
            interface,
            (
                f"estado={get_interface_state(interface)} | "
                f"carrier={get_carrier(interface)} | "
                f"IPv4={get_ipv4(interface) or 'Sin IPv4'}"
            ),
            BLUE
        )

    print()

    if route_before:

        info(
            "Internet actualmente por:",
            route_before["interface"],
            GREEN
        )

    print()

    choice = input(
        f"{YELLOW}>{RESET} "
        f"{WHITE}"
        "¿Reparar solamente Ethernet? (s/n):"
        f"{RESET} "
    ).strip().lower()

    if choice != "s":

        warn(
            "Operación cancelada."
        )

        pause()
        return

    for interface in ethernet_interfaces:

        print(
            f"\n{YELLOW}"
            f"Comprobando {interface}..."
            f"{RESET}"
        )

        run_argv([
            "sudo",
            "ip",
            "link",
            "set",
            interface,
            "up"
        ])

        time.sleep(1)

        carrier = get_carrier(
            interface
        )

        if carrier == "OK":

            ok(
                f"{interface} tiene "
                "enlace físico."
            )

        else:

            warn(
                f"{interface} no tiene "
                "carrier."
            )

        if get_ipv4(interface):

            ok(
                f"{interface} ya tiene IPv4."
            )

            continue

        warn(
            f"{interface} no tiene IPv4."
        )

        if command_exists("nmcli"):

            code, output = run_argv(
                [
                    "sudo",
                    "nmcli",
                    "device",
                    "connect",
                    interface
                ],
                timeout=30
            )

            if code == 0:

                ok(
                    f"DHCP/NetworkManager "
                    f"intentó recuperar {interface}."
                )

            else:

                warn(
                    f"NetworkManager no pudo "
                    f"conectar {interface}."
                )

                if output:
                    print(output)

        elif command_exists("dhclient"):

            run_argv(
                [
                    "sudo",
                    "dhclient",
                    "-r",
                    interface
                ],
                timeout=20
            )

            code, output = run_argv(
                [
                    "sudo",
                    "dhclient",
                    interface
                ],
                timeout=30
            )

            if code == 0:

                ok(
                    f"DHCP ejecutado en "
                    f"{interface}."
                )

            else:

                err(
                    f"DHCP falló en "
                    f"{interface}."
                )

        else:

            warn(
                "No se encontró nmcli "
                "ni dhclient."
            )

    time.sleep(3)

    route_after = get_default_route_info()

    print()

    if route_after:

        info(
            "Nueva ruta:",
            route_after["interface"]
            or "No detectada",
            GREEN
        )

        info(
            "Gateway:",
            route_after["gateway"]
            or "No detectado",
            WHITE
        )

    else:

        warn(
            "No hay una ruta por defecto."
        )

    if check_internet():

        ok(
            "Internet responde."
        )

    else:

        warn(
            "Internet todavía no responde."
        )

    pause()


# ============================================================
# ESTADO GENERAL DE RED
# ============================================================

def network_overview():

    header(
        "ESTADO DE RED"
    )

    wifi = get_wireless_interface()
    ethernet = get_ethernet_interfaces()
    route = get_default_route_info()

    print(
        f"{WHITE}WI-FI{RESET}"
    )

    if wifi:

        info(
            "Interfaz:",
            wifi,
            BLUE
        )

        info(
            "Estado:",
            get_interface_state(wifi),
            GREEN
        )

        info(
            "Modo:",
            get_current_mode(wifi),
            YELLOW
        )

        info(
            "IPv4:",
            get_ipv4(wifi)
            or "Sin IPv4",
            WHITE
        )

        details = get_wifi_connection_details(
            wifi
        )

        if details:

            info(
                "SSID:",
                details["ssid"],
                WHITE
            )

            info(
                "Señal:",
                details["signal"],
                YELLOW
            )

    else:

        err(
            "No se detectó Wi-Fi."
        )

    print()

    print(
        f"{WHITE}ETHERNET{RESET}"
    )

    if ethernet:

        for interface in ethernet:

            info(
                "Interfaz:",
                interface,
                BLUE
            )

            info(
                "Estado:",
                get_interface_state(interface),
                GREEN
            )

            info(
                "Carrier:",
                get_carrier(interface),
                GREEN
            )

            info(
                "IPv4:",
                get_ipv4(interface)
                or "Sin IPv4",
                WHITE
            )

    else:

        warn(
            "No se detectó Ethernet."
        )

    print()

    separator()

    print(
        f"{WHITE}INTERNET ACTUAL{RESET}"
    )

    if route:

        info(
            "Interfaz de salida:",
            route["interface"]
            or "No detectada",
            GREEN
        )

        info(
            "Gateway:",
            route["gateway"]
            or "No detectado",
            WHITE
        )

        info(
            "IP origen:",
            route["source"]
            or "No detectada",
            WHITE
        )

    else:

        err(
            "No hay ruta hacia Internet."
        )

    print()

    dns = get_dns_servers()

    info(
        "DNS:",
        ", ".join(dns)
        if dns
        else "No detectados",
        WHITE
    )

    if check_internet():

        ok(
            "Internet: FUNCIONANDO"
        )

    else:

        err(
            "Internet: SIN RESPUESTA"
        )

    if check_dns():

        ok(
            "DNS: FUNCIONANDO"
        )

    else:

        warn(
            "DNS: no se pudo comprobar."
        )

    pause()


# ============================================================
# NETWORKMANAGER
# ============================================================

def networkmanager_active():

    if not command_exists("systemctl"):
        return False

    code, output = run_argv([
        "systemctl",
        "is-active",
        "NetworkManager"
    ])

    return (
        code == 0
        and output.strip() == "active"
    )


def start_networkmanager():

    if networkmanager_active():
        return True

    code, output = run_argv([
        "sudo",
        "systemctl",
        "start",
        "NetworkManager"
    ])

    if code == 0:

        time.sleep(2)

        return networkmanager_active()

    return False


def restart_networkmanager():

    code, output = run_argv([
        "sudo",
        "systemctl",
        "restart",
        "NetworkManager"
    ],
        timeout=45
    )

    return code == 0, output


def restart_networkmanager_menu():

    header(
        "REINICIAR NETWORKMANAGER"
    )

    warn(
        "Esta acción puede interrumpir "
        "WI-FI Y ETHERNET."
    )

    warn(
        "No se ejecuta automáticamente "
        "desde cambiar modo Wi-Fi."
    )

    print()

    if networkmanager_active():

        ok(
            "NetworkManager está activo."
        )

    else:

        err(
            "NetworkManager no está activo."
        )

    print()

    choice = input(
        f"{YELLOW}>{RESET} "
        f"{WHITE}"
        "¿Reiniciar NetworkManager? (s/n):"
        f"{RESET} "
    ).strip().lower()

    if choice != "s":

        warn(
            "Operación cancelada."
        )

        pause()
        return

    route_before = get_default_route_info()

    if route_before:

        info(
            "Ruta antes del reinicio:",
            route_before["interface"],
            GREEN
        )

    print()

    success, output = restart_networkmanager()

    if success:

        ok(
            "NetworkManager reiniciado."
        )

        time.sleep(3)

    else:

        err(
            "No se pudo reiniciar "
            "NetworkManager."
        )

        if output:
            print(output)

        pause()
        return

    route_after = get_default_route_info()

    print()

    if route_after:

        info(
            "Ruta después del reinicio:",
            route_after["interface"],
            GREEN
        )

        if (
            route_before
            and route_before["interface"]
            != route_after["interface"]
        ):

            warn(
                "La interfaz de salida "
                "cambió después del reinicio."
            )

    else:

        warn(
            "Todavía no existe una "
            "ruta por defecto."
        )

    if check_internet():

        ok(
            "Internet responde."
        )

    else:

        warn(
            "Internet no responde."
        )

    pause()


# ============================================================
# INFORMACIÓN DEL ADAPTADOR
# ============================================================

def adapter_information():

    header(
        "INFORMACIÓN DEL ADAPTADOR"
    )

    adapter = get_adapter_info()
    interface = get_wireless_interface()

    info(
        "USB ID:",
        adapter["usb_id"],
        BLUE
    )

    info(
        "Descripción USB:",
        adapter["usb_description"],
        WHITE
    )

    info(
        "Modelo:",
        adapter["model"],
        BLUE
    )

    info(
        "Chipset:",
        adapter["chipset"],
        BLUE
    )

    info(
        "Driver esperado:",
        adapter["driver"],
        GREEN
    )

    info(
        "Paquete:",
        adapter["package"],
        YELLOW
    )

    print()

    if interface:

        info(
            "Interfaz Wi-Fi:",
            interface,
            BLUE
        )

        info(
            "PHY:",
            get_phy(interface),
            BLUE
        )

        info(
            "MAC:",
            get_mac(interface),
            WHITE
        )

        info(
            "Estado:",
            get_interface_state(interface),
            GREEN
        )

        info(
            "Carrier:",
            get_carrier(interface),
            GREEN
        )

        info(
            "Modo:",
            get_current_mode(interface),
            YELLOW
        )

        info(
            "IPv4:",
            get_ipv4(interface)
            or "Sin IPv4",
            WHITE
        )

        info(
            "Driver cargado:",
            get_driver(interface),
            GREEN
        )

        info(
            "Versión driver:",
            get_driver_version(interface),
            YELLOW
        )

    else:

        err(
            "No se detectó interfaz Wi-Fi."
        )

    pause()


# ============================================================
# MODOS SOPORTADOS - MENÚ
# ============================================================

def supported_modes_menu():

    header(
        "MODOS SOPORTADOS"
    )

    interface = get_wireless_interface()

    if not interface:

        err(
            "No se detectó interfaz Wi-Fi."
        )

        pause()
        return

    modes = ordered_supported_modes(
        interface
    )

    info(
        "Interfaz:",
        interface,
        BLUE
    )

    info(
        "PHY:",
        get_phy(interface),
        BLUE
    )

    info(
        "Modo actual:",
        get_current_mode(interface),
        YELLOW
    )

    print()

    if not modes:

        err(
            "No se pudieron leer "
            "los modos soportados."
        )

    else:

        for mode in modes:

            print(
                f"{WHITE}• {YELLOW}"
                f"{mode}"
                f"{RESET}"
            )

            print(
                f"  {WHITE}"
                f"{MODE_DESCRIPTIONS.get(mode, '')}"
                f"{RESET}"
            )

    pause()


# ============================================================
# BANDAS Y CANALES - MENÚ
# ============================================================

def band_channel_menu():

    header(
        "BANDAS Y CANALES"
    )

    interface = get_wireless_interface()

    if not interface:

        err(
            "No se detectó interfaz Wi-Fi."
        )

        pause()
        return

    data = get_band_information(
        interface
    )

    info(
        "Interfaz:",
        interface,
        BLUE
    )

    info(
        "Canal actual:",
        get_current_channel(interface),
        YELLOW
    )

    print()

    for band in [
        "2.4 GHz",
        "5 GHz",
        "6 GHz"
    ]:

        print(
            f"{WHITE}{band}{RESET}"
        )

        channels = data[band]["channels"]
        widths = data[band]["widths"]

        info(
            "  Canales:",
            ", ".join(
                str(c)
                for c in channels
            )
            if channels
            else "No detectados",
            BLUE
        )

        info(
            "  Anchos:",
            ", ".join(widths)
            if widths
            else "No detectados",
            GREEN
        )

        print()

    pause()


# ============================================================
# ESTADO DEL ADAPTADOR
# ============================================================

def adapter_status():

    header(
        "ESTADO DEL ADAPTADOR"
    )

    interface = get_wireless_interface()

    if not interface:

        err(
            "No se detectó interfaz Wi-Fi."
        )

        pause()
        return

    details = get_wifi_connection_details(
        interface
    )

    info(
        "Interfaz:",
        interface,
        BLUE
    )

    info(
        "MAC:",
        get_mac(interface),
        WHITE
    )

    info(
        "PHY:",
        get_phy(interface),
        BLUE
    )

    info(
        "Estado:",
        get_interface_state(interface),
        GREEN
    )

    info(
        "Carrier:",
        get_carrier(interface),
        GREEN
    )

    info(
        "Modo:",
        get_current_mode(interface),
        YELLOW
    )

    info(
        "IPv4:",
        get_ipv4(interface)
        or "Sin IPv4",
        WHITE
    )

    info(
        "Driver:",
        get_driver(interface),
        GREEN
    )

    print()

    if details:

        ok(
            "Asociado a una red Wi-Fi."
        )

        info(
            "SSID:",
            details["ssid"],
            WHITE
        )

        info(
            "BSSID:",
            details["bssid"],
            BLUE
        )

        info(
            "Señal:",
            details["signal"],
            YELLOW
        )

    else:

        warn(
            "No está asociado a una red Wi-Fi."
        )

    pause()


# ============================================================
# DIAGNÓSTICO
# ============================================================

def diagnostic():

    header(
        "DIAGNÓSTICO"
    )

    interface = get_wireless_interface()
    ethernet = get_ethernet_interface()
    route = get_default_route_info()

    print(
        f"{WHITE}INTERFACES{RESET}"
    )

    if interface:

        info(
            "Wi-Fi:",
            interface,
            BLUE
        )

        info(
            "Wi-Fi estado:",
            get_interface_state(interface),
            GREEN
        )

        info(
            "Wi-Fi modo:",
            get_current_mode(interface),
            YELLOW
        )

        info(
            "Wi-Fi IPv4:",
            get_ipv4(interface)
            or "Sin IPv4",
            WHITE
        )

    else:

        err(
            "Wi-Fi no detectada."
        )

    if ethernet:

        info(
            "Ethernet:",
            ethernet,
            BLUE
        )

        info(
            "Ethernet estado:",
            get_interface_state(ethernet),
            GREEN
        )

        info(
            "Ethernet carrier:",
            get_carrier(ethernet),
            GREEN
        )

        info(
            "Ethernet IPv4:",
            get_ipv4(ethernet)
            or "Sin IPv4",
            WHITE
        )

    else:

        warn(
            "Ethernet no detectada."
        )

    print()

    print(
        f"{WHITE}RUTA{RESET}"
    )

    if route:

        info(
            "Salida:",
            route["interface"]
            or "Desconocida",
            GREEN
        )

        info(
            "Gateway:",
            route["gateway"]
            or "Desconocido",
            WHITE
        )

        info(
            "IP origen:",
            route["source"]
            or "Desconocida",
            WHITE
        )

    else:

        err(
            "No hay ruta hacia Internet."
        )

    print()

    print(
        f"{WHITE}SERVICIOS{RESET}"
    )

    if networkmanager_active():

        ok(
            "NetworkManager activo."
        )

    else:

        err(
            "NetworkManager no está activo."
        )

    if check_internet():

        ok(
            "Ping a Internet: OK"
        )

    else:

        err(
            "Ping a Internet: FALLÓ"
        )

    if check_dns():

        ok(
            "Resolución DNS: OK"
        )

    else:

        warn(
            "Resolución DNS: FALLÓ"
        )

    pause()


# ============================================================
# DRIVER
# ============================================================

def detailed_driver_info():

    header(
        "INFORMACIÓN DEL DRIVER"
    )

    interface = get_wireless_interface()

    if not interface:

        err(
            "No se detectó el adaptador Wi-Fi."
        )

        pause()
        return

    info(
        "Interfaz:",
        interface,
        BLUE
    )

    info(
        "Driver:",
        get_driver(interface),
        GREEN
    )

    info(
        "Versión:",
        get_driver_version(interface),
        YELLOW
    )

    info(
        "Firmware:",
        get_firmware(interface),
        YELLOW
    )

    if command_exists("ethtool"):

        code, output = run_argv([
            "ethtool",
            "-i",
            interface
        ])

        print()

        if output:
            print(output)

    pause()


def is_driver_compatible(
    driver,
    chipset
):

    patterns = (
        COMPATIBLE_DRIVER_PATTERNS
        .get(chipset, [])
    )

    if (
        driver == "Desconocido"
        or not patterns
    ):
        return False

    return any(
        re.search(
            pattern,
            driver,
            re.IGNORECASE
        )
        for pattern in patterns
    )


def verify_driver():

    header(
        "VERIFICAR COMPATIBILIDAD"
    )

    adapter = get_adapter_info()
    interface = get_wireless_interface()

    info(
        "USB ID:",
        adapter["usb_id"],
        BLUE
    )

    info(
        "Modelo:",
        adapter["model"],
        BLUE
    )

    info(
        "Chipset:",
        adapter["chipset"],
        BLUE
    )

    if not interface:

        err(
            "No hay interfaz Wi-Fi."
        )

        pause()
        return

    driver = get_driver(interface)

    info(
        "Driver cargado:",
        driver,
        GREEN
    )

    if is_driver_compatible(
        driver,
        adapter["chipset"]
    ):

        ok(
            f"El driver coincide con "
            f"{adapter['chipset']}."
        )

    else:

        warn(
            "El driver no coincide con "
            "los patrones registrados."
        )

        info(
            "Nota:",
            "Esto no demuestra por sí solo "
            "que el adaptador esté fallando.",
            WHITE
        )

    pause()


def repair_driver():

    header(
        "REINSTALAR FIRMWARE"
    )

    adapter = get_adapter_info()

    if (
        adapter["usb_id"]
        not in ADAPTER_DATABASE
    ):

        err(
            "Adaptador no registrado."
        )

        pause()
        return

    info(
        "Modelo:",
        adapter["model"],
        BLUE
    )

    info(
        "Chipset:",
        adapter["chipset"],
        BLUE
    )

    info(
        "Paquete:",
        adapter["package"],
        BLUE
    )

    warn(
        "Esto reinstala firmware, "
        "no recompila el driver."
    )

    choice = input(
        f"\n{YELLOW}>{RESET} "
        f"{WHITE}"
        "¿Reinstalar firmware? (s/n):"
        f"{RESET} "
    ).strip().lower()

    if choice != "s":

        warn(
            "Operación cancelada."
        )

        pause()
        return

    code, output = run_argv(
        [
            "sudo",
            "apt",
            "update"
        ],
        timeout=120
    )

    if code != 0:

        err(
            "apt update falló."
        )

        if output:
            print(output)

        pause()
        return

    code, output = run_argv(
        [
            "sudo",
            "apt",
            "install",
            "--reinstall",
            "-y",
            adapter["package"]
        ],
        timeout=120
    )

    if code == 0:

        ok(
            "Firmware instalado/"
            "reinstalado correctamente."
        )

    else:

        err(
            "No se pudo instalar "
            "el paquete."
        )

        if output:
            print(output)

    pause()


def driver_menu():

    while True:

        header("DRIVER")

        print(
            f"{BLUE}[1]{RESET} "
            "Reinstalar firmware"
        )

        print(
            f"{BLUE}[2]{RESET} "
            "Información detallada"
        )

        print(
            f"{BLUE}[3]{RESET} "
            "Verificar compatibilidad"
        )

        print(
            f"{BLUE}[0]{RESET} "
            "Regresar"
        )

        choice = input(
            f"\n{YELLOW}>{RESET} "
            f"{WHITE}Selecciona:{RESET} "
        ).strip()

        if choice == "1":

            repair_driver()

        elif choice == "2":

            detailed_driver_info()

        elif choice == "3":

            verify_driver()

        elif choice == "0":

            return

        else:

            err(
                "Opción inválida."
            )

            time.sleep(1)


# ============================================================
# MENÚ CAMBIAR MODO
# ============================================================

def mode_menu():

    while True:

        header("CAMBIAR MODO")

        interface = get_wireless_interface()

        if not interface:

            err(
                "No se detectó el adaptador Wi-Fi."
            )

            pause()
            return

        modes = ordered_supported_modes(
            interface
        )

        info(
            "Interfaz:",
            interface,
            BLUE
        )

        info(
            "Modo actual:",
            get_current_mode(interface),
            YELLOW
        )

        print()

        if not modes:

            err(
                "No se detectaron "
                "modos soportados."
            )

            pause()
            return

        for idx, mode in enumerate(
            modes,
            1
        ):

            print(
                f"{BLUE}[{idx}]{RESET} "
                f"{YELLOW}{mode}{RESET}"
            )

            print(
                f"    {WHITE}"
                f"{MODE_DESCRIPTIONS.get(mode, '')}"
                f"{RESET}"
            )

        print(
            f"\n{BLUE}[0]{RESET} "
            f"{WHITE}Regresar{RESET}"
        )

        choice = input(
            f"\n{YELLOW}>{RESET} "
            f"{WHITE}Selecciona:{RESET} "
        ).strip()

        if choice == "0":
            return

        if (
            not choice.isdigit()
            or not (
                1 <= int(choice)
                <= len(modes)
            )
        ):

            err(
                "Opción inválida."
            )

            time.sleep(1)
            continue

        selected = modes[
            int(choice) - 1
        ]

        change_mode(selected)

        pause()


# ============================================================
# MENÚ PRINCIPAL
# ============================================================

def main_menu():

    while True:

        interface = get_wireless_interface()
        adapter = get_adapter_info()

        clear()

        print(
            f"{WHITE}{BANNER}{RESET}"
        )

        separator()

        info(
            "Adaptador:",
            interface or "No detectado",
            BLUE
        )

        info(
            "Modelo:",
            adapter["model"],
            BLUE
        )

        info(
            "Chipset:",
            adapter["chipset"],
            BLUE
        )

        print()

        print(
            f"{BLUE}[1]{RESET} "
            "Información del adaptador"
        )

        print(
            f"{BLUE}[2]{RESET} "
            "Modos soportados"
        )

        print(
            f"{BLUE}[3]{RESET} "
            "Bandas y canales"
        )

        print(
            f"{BLUE}[4]{RESET} "
            "Estado del adaptador"
        )

        print(
            f"{BLUE}[5]{RESET} "
            "Diagnóstico"
        )

        print(
            f"{BLUE}[6]{RESET} "
            "Cambiar modo Wi-Fi"
        )

        print(
            f"{BLUE}[7]{RESET} "
            "Driver Wi-Fi"
        )

        print()

        separator()

        print(
            f"{WHITE}RED{RESET}"
        )

        print(
            f"{BLUE}[8]{RESET} "
            "Estado de Wi-Fi"
        )

        print(
            f"{BLUE}[9]{RESET} "
            "Reparar Wi-Fi"
        )

        print(
            f"{BLUE}[10]{RESET} "
            "Estado de Ethernet"
        )

        print(
            f"{BLUE}[11]{RESET} "
            "Reparar Ethernet"
        )

        print(
            f"{BLUE}[12]{RESET} "
            "Estado general de red"
        )

        print(
            f"{BLUE}[13]{RESET} "
            "Reiniciar NetworkManager"
        )

        print(
            f"{BLUE}[14]{RESET} "
            "Cambiar interfaz Wi-Fi administrada"
        )

        print()

        print(
            f"{BLUE}[0]{RESET} "
            "Salir"
        )

        choice = input(
            f"\n{YELLOW}>{RESET} "
            f"{WHITE}"
            "Selecciona una opción:"
            f"{RESET} "
        ).strip()

        if choice == "1":

            adapter_information()

        elif choice == "2":

            supported_modes_menu()

        elif choice == "3":

            band_channel_menu()

        elif choice == "4":

            adapter_status()

        elif choice == "5":

            diagnostic()

        elif choice == "6":

            mode_menu()

        elif choice == "7":

            driver_menu()

        elif choice == "8":

            wifi_status()

        elif choice == "9":

            repair_wifi()

        elif choice == "10":

            ethernet_status()

        elif choice == "11":

            repair_ethernet()

        elif choice == "12":

            network_overview()

        elif choice == "13":

            restart_networkmanager_menu()

        elif choice == "14":

            change_managed_interface()

        elif choice == "0":

            exit_program()

        else:

            err(
                "Opción inválida."
            )

            time.sleep(1)


# ============================================================
# EJECUCIÓN
# ============================================================

if __name__ == "__main__":

    try:

        main_menu()

    except KeyboardInterrupt:

        exit_program()

    except Exception as e:

        print()

        err(
            f"Error inesperado: {e}"
        )

        pause()
