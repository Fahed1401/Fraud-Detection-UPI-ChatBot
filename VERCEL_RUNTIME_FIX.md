# Vercel Engine Unavailable — runtime fix

This version is built for a single Vercel project with root directory `./`, Flask auto-detection, and no custom build command.

## Changes

- The trained synthetic-data model lives in `model_artifacts/ensemble.joblib` and is explicitly included in the Vercel Function. Its creation is reproducible via `python train.py` locally, but production requests never train or write files.
- `/api/ping` tests that Flask routing runs without importing XGBoost.
- `/api/health` loads the trained artifact and returns HTTP 200 `status=ready` or a clear HTTP 503 diagnostic, while detailed exceptions are logged server-side.
- XGBoost CPU-only Linux wheel and matching Python/scikit-learn versions reduce memory/bundle pressure.
- Frontend now displays precise HTTP, JSON, or timeout failures and has a retry button independent of Guided Demo.

## Deploy

1. Copy **all** files (including `model_artifacts/ensemble.joblib`) into your cloned repository, not inside a second project folder. Do not copy `.git`, `.venv`, `.model_cache`.
2. `git add -A && git commit -m "fix: package model and repair Vercel inference" && git push origin main`
3. In Vercel Settings > Build & Deployment: Root Directory `./` (repository root), Framework Preset `Flask` or auto-detect. Remove any custom Build Command/Output Directory and use Python 3.13 via `.python-version` (included; matching the bundled artifact). Leave the Large Functions beta toggle enabled if needed.
4. Redeploy newest commit, preferably without build cache.
5. Visit `<your-deployment>/api/ping` (should be HTTP 200 `status=ok`), then `/api/health` (HTTP 200 `status=ready`). Finally test the frontend.

## Interpret failures

- `/api/ping` returns 404 or HTML: Vercel is not routing requests to Flask. Check Root Directory, recognized app entrypoint `app.py`, and Framework Preset.
- `/api/ping` returns 500: Flask dependency or import/runtime startup error; see Vercel Functions Runtime Logs.
- `/api/ping` is OK but `/api/health` returns 503: model or native dependency import/load issue. Response includes `error_type`; Vercel Runtime Logs contain the full traceback. Check that model_artifacts/ensemble.joblib was committed.
- `/api/health` returns 200 but frontend says offline: inspect Network tab `/api/health` for stale config.js or browser cache, then hard refresh. The `public/config.js` must contain `API_BASE_URL: ""`.
- Error `FUNCTION_INVOCATION_TIMEOUT`: inspect memory and execution in the Runtime Logs; ensure large functions/fluid compute are enabled or try CPU-only dependency as provided.

Warning: The bundled artifact contains synthetic-data models and is an educational prototype, not a validated production banking detector. Only load artifacts you trust; joblib is pickle-based.
