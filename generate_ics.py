from datetime import datetime
import json
import urllib.request

# Diccionario para personalizar los nombres de los festivos a tu gusto
REEMPLAZOS_NOMBRES = {
    "Natividad del Señor": "Navidad",
    "Epifanía del Señor": "Reyes Magos",
    "Fiesta del Trabajo": "Día del Trabajador",
    "Fiesta Nacional de España": "Fiesta Nacional",
    "Asunción de la Virgen": "Asunción",
}

current_year = datetime.now().year
# Definimos los años que queremos incluir (por ejemplo: este año y el siguiente)
anios_a_incluir = [current_year, current_year + 1]

# Construir la estructura básica del archivo iCal (.ics)
ics_lines = [
    "BEGIN:VCALENDAR",
    "VERSION:2.0",
    "PRODID:-//Festivos Arroyo de la Encomienda//ES",
    "CALSCALE:GREGORIAN",
    "METHOD:PUBLISH",
    "X-WR-CALNAME:Festivos en Arroyo",
]

# Recorrer cada año configurado para acumular sus festivos
for year in anios_a_incluir:
  url = f"https://calendariosnacionales.com/es/v1/{year}/localidades/cyl/valladolid/arroyo-de-la-encomienda.json"

  try:
    req = urllib.request.Request(
        url, headers={"User-Agent": "Mozilla/5.0 (Compatible; CalendarBot/1.0)"}
    )
    with urllib.request.urlopen(req) as response:
      data = json.loads(response.read().decode())

    # Recorrer los festivos de ese año
    for holiday in data.get("holidays", {}).get("calendar", []):
      name_original = holiday.get("name")
      name = REEMPLAZOS_NOMBRES.get(name_original, name_original)
      date_str = holiday.get("date").replace("-", "")
      source = holiday.get("source", "Fuente oficial")

      ics_lines.extend([
          "BEGIN:VEVENT",
          f"SUMMARY:{name}",
          f"DTSTART;VALUE=DATE:{date_str}",
          f"DTEND;VALUE=DATE:{date_str}",
          f"DESCRIPTION:Festivo oficial ({source})",
          "END:VEVENT",
      ])
  except Exception as e:
    # Si la API del año siguiente aún no está publicada por el ayuntamiento, no rompe el script
    print(f"Aviso: No se pudieron cargar los datos para el año {year}: {e}")

ics_lines.append("END:VCALENDAR")

# Guardar el resultado consolidado en festivos.ics
with open("festivos.ics", "w", encoding="utf-8") as f:
  f.write("\n".join(ics_lines))

print(
    "Calendario plurianual generado con éxito para los años:"
    f" {anios_a_incluir}"
)
