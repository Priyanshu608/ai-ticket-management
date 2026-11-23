# SupportFlow frontend

The UI for the Support AI service, built with **Next.js 16**, **React 19**, TypeScript, Tailwind CSS, and Lucide icons.

## What's inside

- **Overview:** dataset-backed volume trends, priority distribution, live-filtered ticket and account tables, pagination, and an inspectable ticket detail panel.
- **AI triage:** classify a custom ticket or send one from the queue into the existing retrieval and response-generation pipeline.
- **Account health:** use the deterministic risk rules and generated executive briefs.
- **Evaluation:** inspect the project's recorded LLM evaluation and adversarial scenarios.

The Overview tab is **read-only** and uses the synthetic records in `../data/`. It does not create, edit, or synchronize actual support tickets. The Evaluation tab displays documented benchmark examples; it does not execute new evaluations in the browser.

## Run locally

From the repository root, install the Python dependencies and run FastAPI:

```bash
python -m venv .venv
# Activate your venv, then:
pip install -r requirements.txt
uvicorn src.api:app --reload
```

In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000). The frontend defaults to `http://127.0.0.1:8000` for the API. If the API is elsewhere, set `NEXT_PUBLIC_API_URL` before starting the frontend.

**No Groq key is needed for the Overview tab.** Running AI triage requires `GROQ_API_KEY` in the backend's local `.env` file and may download an embedding model on its first request. Never put secrets in `NEXT_PUBLIC_*` variables.

## Backend endpoints used

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/health` | Backend connection indicator |
| GET | `/operations/summary` | Counts and monthly aggregates over sample data |
| GET | `/operations/tickets` | Search, status, priority and pagination |
| GET | `/operations/accounts` | Search, risk and pagination |
| POST | `/triage` | Existing AI triage workflow |
| GET | `/accounts/{account_id}/brief` | Existing account health brief |

For interactive API documentation visit [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

Note: the checked-in npm lockfile currently needs regeneration for a strict \`npm ci\` install. Until the lockfile is synchronized, use \`npm install\` for local setup and CI.\n\n## Checks\n
```bash
npm run lint
npx tsc --noEmit
npm run build
```

At the repository root, `python -m pytest tests/test_ops.py tests/test_signals.py` runs the lightweight deterministic tests without an API key. The repository's `.github/workflows/ci.yml` automates these checks on pull requests.

## Notes

The sample dataset intentionally has sparse links between tickets and account records. A displayed ticket's account ID is not necessarily present in the account dataset. API errors and empty states are shown explicitly rather than substituting generated demo numbers. This application is a project showcase, not a multi-tenant or authenticated production support service.
