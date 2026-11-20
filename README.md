# Balochistan Smart Highway Watch — Enhanced Expo Prototype

## What's real now
- Live weather forecast requests from Open-Meteo (internet required; no API key for this demo use).
- Current temperature, apparent temperature, wind, visibility, humidity, precipitation and short hourly forecast charts.
- Local SQLite driver, checkpoint, road-status and alert-preview records.
- Custom dashboard styling and an embedded original SVG logo.

## What's still a demo / not connected
- No official PMD data feed or government road-closure/reopening feed.
- Town-level coordinates are representative forecast points, not sensors or exact road-segment coverage.
- Road status is manually entered and not verified by an authority.
- SMS and voice calls are previews only; no messages or calls are sent.
- No AI model is currently making safety decisions. Weather information is displayed from a forecast API; don't use it as a basis for travel decisions.

## Run on Windows
Open CMD in this folder and run:
```bash
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```
If you already created `.venv`, do not create it again.

## Live weather provider
The app calls the Open-Meteo Forecast API. The source and observation time are shown in the app. Internet access is required. API terms/usage limits and attribution should be checked before public or production deployment.

## Before real-world deployment
1. Obtain a formal, authorized weather data arrangement with PMD or another approved provider.
2. Integrate official road closure/reopening information from the responsible road authority.
3. Verify every route coordinate and checkpoint with field/authority data.
4. Add authentication, role permissions, audit logs, encryption, consent and retention controls.
5. Connect an approved SMS and voice provider using private credentials stored in environment variables, never in source code.
6. Test Urdu, Pashto and Balochi content and voice quality with fluent speakers.
7. Add fail-safe behavior, stale-data warnings, duplicate-alert prevention, monitoring and human approval for critical alerts.
