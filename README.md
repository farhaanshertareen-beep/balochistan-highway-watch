# Balochistan Smart Highway Watch

A Streamlit prototype for corridor weather awareness, driver records, manually maintained road-status records, checkpoint records, and Urdu alert previews.

## Included
- Responsive dark dashboard
- Balochistan corridor overview map using representative town coordinates
- Open-Meteo current conditions and short forecast charts
- SQLite database created automatically on first run
- Driver registration and CSV export
- Checkpoint and manually maintained road-status registers
- Urdu alert preview and alert-history CSV export
- Sample checkpoint and road-status records seeded automatically

## Run locally

Python 3.10 or newer is recommended.

```bash
python -m venv .venv
```

Windows:
```bash
.venv\\Scripts\\activate
```

macOS / Linux:
```bash
source .venv/bin/activate
```

Install and start:
```bash
pip install -r requirements.txt
streamlit run app.py
```

The app will create `highway_alerts.db` beside `app.py` automatically.

## Deploy on Streamlit Community Cloud
1. Create a GitHub repository and upload the contents of this folder.
2. In Streamlit Community Cloud, create an app from that repository.
3. Set the main file path to `app.py`.
4. Deploy. The app needs outbound internet access for Open-Meteo weather requests.

A `.streamlit/config.toml` file is included for the app theme.

## Data and safety limitations — read before use
- Weather data is fetched from the public Open-Meteo Forecast API. It is forecast data, not an official Pakistan Meteorological Department feed.
- Town coordinates are representative reference points. They are not road-segment sensors and do not describe exact highway alignment or conditions at every point.
- Road status is entered manually by an operator. It is not connected to an official road closure or reopening feed.
- Alert Centre creates and stores message previews only. It does not send SMS messages or place voice calls.
- The prototype does not use an AI model to make safety decisions and is not an emergency-warning service.
- Do not use this prototype alone to decide whether a route is safe or open. Verify conditions with relevant authorities before travel.

## Before operational / public deployment
1. Arrange authorized weather and road-status data feeds with the responsible agencies.
2. Validate all route coordinates and checkpoints with authoritative GIS / field data.
3. Add authentication, role-based permissions, audit logs, secure backups, encryption, consent and retention controls.
4. Integrate an approved SMS / voice provider using secrets stored in deployment settings, never in source code.
5. Add monitoring, stale-data warnings, failure handling, duplicate-alert prevention and human approval for critical messages.
6. Have Urdu, Pashto and Balochi content and voice quality reviewed by fluent speakers.
7. Conduct security, privacy, reliability and field testing before any operational use.

## Database
The SQLite database is created automatically. It is excluded from Git by `.gitignore` so local driver data is not accidentally committed.
