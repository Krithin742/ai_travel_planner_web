# AI Travel Planner — Agentic Web Application

This project converts the Phase 2/Phase 3 Google Colab notebook into a modular Python web application.

## Architecture

User → HTML/CSS → FastAPI → LangGraph

LangGraph:

Query Analyzer
↓
Web/Specialized Research
├── Serper Web Search
├── Open-Meteo
├── Nominatim / OpenStreetMap
├── Wikipedia
├── OSRM
└── Frankfurter
↓
Itinerary Generator
↓
Critic
├── PASS → Final Plan
└── REPLAN → Replanner → Critic
             (maximum 2 replanning attempts)

## Run locally

```bash
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
```

Install:

```bash
pip install -r requirements.txt
```

Set your Serper key:

Windows PowerShell:

```powershell
$env:SERPER_API_KEY="YOUR_KEY"
```

Linux/macOS:

```bash
export SERPER_API_KEY="YOUR_KEY"
```

Run:

```bash
uvicorn app:app --reload
```

Open:

```text
http://127.0.0.1:8000
```

## Notes

- Qwen is loaded locally from Hugging Face.
- Serper is the only tool here that requires an API key.
- Open-Meteo, Nominatim, Wikipedia, OSRM and Frankfurter are called through HTTP APIs without an API key in this implementation.
- OSRM is used as a road-route estimate and should not be interpreted as international flight duration.
