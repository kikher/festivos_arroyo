from datetime import datetime, timedelta, timezone
from pathlib import Path
import hashlib
import json
import re
import sys
import urllib.request

# Nombres personalizados de festivos
REEMPLAZOS_NOMBRES = {
    "Natividad del Señor": "Navidad",
    "Epifanía del Señor": "Reyes Magos",
    "Fiesta del Trabajo": "Día del Trabajador",
    "Fiesta Nacional de España": "Fiesta Nacional",
    "Asunción de la Virgen": "Asunción",
}

URL_BASE = (
    "https://calendariosnacionales.com/es/v1/{year}/localidades/"
    "cyl/valladolid/arroyo-de-la-encomienda.json"
)
ARCHIVO = Path("festivos.ics")

ahora = datetime.now(timezone.utc)
current_year = ahora.year
anios_a_incluir = [current_year, current_year + 1]
dtstamp = ahora.strftime("%Y%m%dT%H%M%SZ")


def escapar(texto):
    return (
        texto.replace("\\", "\\\\")
        .replace(";", "\\;")
        .replace(",", "\\,")
    )


def descargar(year):
    req = urllib.request.Request(
        URL_BASE.format(year=year),
        headers={"User-Agent": "Mozilla/5.0 (Compatible; CalendarBot/1.0)"},
    )
    with urllib.request.urlopen(req, timeout=30) as response:
        data = json.loads(response.read().decode("utf-8"))
    return data.get("holidays", {}).get("calendar", [])


def crear_evento(fecha_iso, nombre_original, fuente):
    nombre = REEMPLAZOS_NOMBRES.get(nombre_original, nombre_original)
    inicio = datetime.strptime(fecha_iso, "%Y-%m-%d").date()
    fin = inicio + timedelta(days=1)  # DTEND es exclusivo en eventos de día completo
    huella = hashlib.md5(nombre_original.encode("utf-8")).hexdigest()[:8]
    return [
        "BEGIN:VEVENT",
        f"UID:{inicio:%Y%m%d}-{huella}@festivos-arroyo",
        f"DTSTAMP:{dtstamp}",
        f"SUMMARY:{escapar(nombre)}",
        f"DTSTART;VALUE=DATE:{inicio:%Y%m%d}",
        f"DTEND;VALUE=DATE:{fin:%Y%m%d}",
        f"DESCRIPTION:Festivo oficial ({escapar(fuente)})",
        "TRANSP:TRANSPARENT",
        "END:VEVENT",
    ]


def eventos_antiguos(year):
    """Recupera los eventos de un año desde el archivo ya generado."""
    if not ARCHIVO.exists():
        return []
    texto = ARCHIVO.read_text(encoding="utf-8")
    bloques = re.findall(r"BEGIN:VEVENT.*?END:VEVENT", texto, flags=re.S)
    return [
        b.splitlines()
        for b in bloques
        if f"DTSTART;VALUE=DATE:{year}" in b
    ]


eventos = []

for year in anios_a_incluir:
    try:
        festivos = descargar(year)
        if not festivos:
            raise ValueError("la lista de festivos está vacía")
        for holiday in festivos:
            eventos.append(
                crear_evento(
                    holiday["date"],
                    holiday["name"],
                    holiday.get("source", "Fuente oficial"),
                )
            )
        print(f"{year}: {len(festivos)} festivos cargados")
    except Exception as e:
        print(f"Aviso: no se pudieron cargar los datos de {year}: {e}")
        if year == current_year:
            # Año actual roto: no tocamos el archivo y hacemos fallar el workflow
            print("Error: falla el año actual. Se conserva el archivo anterior.")
            sys.exit(1)
        antiguos = eventos_antiguos(year)
        if antiguos:
            eventos.extend(antiguos)
            print(f"{year}: se conservan {len(antiguos)} eventos anteriores")

lineas = [
    "BEGIN:VCALENDAR",
    "VERSION:2.0",
    "PRODID:-//Festivos Arroyo de la Encomienda//ES",
    "CALSCALE:GREGORIAN",
    "METHOD:PUBLISH",
    "X-WR-CALNAME:Festivos en Arroyo",
    "X-WR-TIMEZONE:Europe/Madrid",
    "REFRESH-INTERVAL;VALUE=DURATION:P1D",
    "X-PUBLISHED-TTL:P1D",
]
for evento in eventos:
    lineas.extend(evento)
lineas.append("END:VCALENDAR")

with open(ARCHIVO, "w", encoding="utf-8", newline="") as f:
    f.write("\r\n".join(lineas) + "\r\n")

print(f"Calendario generado para los años {anios_a_incluir}: {len(eventos)} eventos")
