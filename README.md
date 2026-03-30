# RAPT.io MCP Server

Ein MCP (Model Context Protocol) Server zum Überwachen und Steuern von KegLand RAPT-Geräten – Gärschränken (Fermentation Chambers) und RaptPill-Hydrometern – über die [RAPT.io API](https://api.rapt.io/index.html).

## Funktionen

### Gärschrank (Fermentation Chamber)
- Alle Gärschränke auflisten
- Status abrufen (Temperatur, Heizen/Kühlen, PID, Laufzeiten)
- Solltemperatur setzen
- PID-Regler ein-/ausschalten
- PID-Parameter (P, I, D) konfigurieren
- Telemetrieverlauf abrufen

### RaptPill (Hydrometer)
- Alle RaptPills auflisten
- Status abrufen (Stammwürze/Gravity, Temperatur, Akkustand)
- Telemetrieverlauf abrufen

### Allgemein
- Alle gebundenen Geräte auflisten
- Fermentationsprofile verwalten

## Installation

### Voraussetzungen
- Python 3.11+
- [uv](https://docs.astral.sh/uv/) (empfohlen) oder pip

### Mit uv installieren

```bash
uv sync
```

### Mit pip installieren

```bash
pip install -e .
```

## Konfiguration

Setze deine RAPT-Zugangsdaten als Umgebungsvariablen:

```bash
export RAPT_USERNAME="deine@email.com"
export RAPT_PASSWORD="deinPasswort"
```

## Verwendung

### Direkt starten

```bash
RAPT_USERNAME="..." RAPT_PASSWORD="..." uv run raptio-mcp
```

### Claude Desktop Integration

Füge folgendes zu deiner `claude_desktop_config.json` hinzu:

```json
{
  "mcpServers": {
    "raptio": {
      "command": "uv",
      "args": ["--directory", "/pfad/zum/raptio_mcp", "run", "raptio-mcp"],
      "env": {
        "RAPT_USERNAME": "deine@email.com",
        "RAPT_PASSWORD": "deinPasswort"
      }
    }
  }
}
```

### Claude Code Integration

```bash
claude mcp add raptio -- uv --directory /pfad/zum/raptio_mcp run raptio-mcp
```

Dann Umgebungsvariablen setzen:
```bash
claude mcp add raptio -e RAPT_USERNAME=deine@email.com -e RAPT_PASSWORD=deinPasswort -- uv --directory /pfad/zum/raptio_mcp run raptio-mcp
```

## Verfügbare Tools

| Tool | Beschreibung |
|------|--------------|
| `get_bonded_devices` | Alle gebundenen Geräte auflisten |
| `get_bonded_device` | Einzelnes Gerät abrufen |
| `get_bonded_device_telemetry` | Telemetrie eines Geräts abrufen |
| `get_fermentation_chambers` | Alle Gärschränke auflisten |
| `get_fermentation_chamber` | Status eines Gärschranks abrufen |
| `set_fermentation_chamber_temperature` | Solltemperatur setzen |
| `set_fermentation_chamber_pid_enabled` | PID ein-/ausschalten |
| `set_fermentation_chamber_pid` | PID-Parameter konfigurieren |
| `get_fermentation_chamber_telemetry` | Temperaturverlauf abrufen |
| `get_hydrometers` | Alle RaptPills auflisten |
| `get_hydrometer` | Status einer RaptPill abrufen |
| `get_hydrometer_telemetry` | Gravity-/Temperaturverlauf abrufen |
| `get_profiles` | Alle Fermentationsprofile auflisten |
| `get_profile` | Profil-Details abrufen |
| `get_profile_types` | Verfügbare Profiltypen auflisten |

## Authentifizierung

Der Server verwendet OAuth2 Password Grant gegen `https://id.rapt.io/connect/token` mit deinen RAPT.io-Zugangsdaten. Das Token wird automatisch erneuert.

## Lizenz

MIT
