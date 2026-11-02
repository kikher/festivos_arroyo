from datetime import datetime
import json
import urllib.request

# Obtener el año actual de forma dinámica
current_year = datetime.now().year
url = f"https://calendariosnacionales.com/es/v1/{current_year}/localidades/cyl/valladolid/arroyo-de-la-encomienda.json"

# Crear una petición simulando ser un navegador web para evitar el bloqueo 403
req = urllib.request.Request(
    url, headers={"User-Agent": "Mozilla/5.0 (Compatible; CalendarBot/1.0)"}
)

# Descargar el JSON de la API
with urllib.request.urlopen(req) as response:
  data = json.loads(response.read().decode())

# Construir la estructura básica del archivo iCal (.ics)
ics_lines = [
    "BEGIN:VCALENDAR",
    "VERSION:2.0",
    "PRODID:-//Festivos Arroyo de la Encomienda//ES",
    "CALSCALE:GREGORIAN",
    "METHOD:PUBLISH",
    f"X-WR-CALNAME:Festivos Arroyo {current_year}",
]

# Recorrer los festivos obtenidos del JSON
for holiday in data.get("holidays", {}).get("calendar", []):
  name = holiday.get("name")
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

ics_lines.append("END:VCALENDAR")

# Guardar el resultado en un archivo festivos.ics
with open("festivos.ics", "w", encoding="utf-8") as f:
  f.write("\n".join(ics_lines))

print(f"Calendario para {current_year} generado con éxito.")
