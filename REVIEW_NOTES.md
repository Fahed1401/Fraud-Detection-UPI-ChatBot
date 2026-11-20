# Code Review — Original repository → UPI Sentinel upgrade

Reviewed original GitHub files: `app.py`, `generate_transactions.py`, `index.html`, `script.js`, `style.css`, `report.html`, `requirements.txt`, `README.md`.

| Original problem | Resolution in this package |
| --- | --- |
| Flask `static_folder='../frontend'` did not match original root-level assets | Serve only permitted files from `public/` via explicit Flask routes. |
| `train_models()` called only under `if __name__ == '__main__'` | `train.py` creates an artifact during build; `model.get_model()` loads it lazily for Gunicorn. |
| `fetch('http://localhost:5001/...')` breaks on deployment | Same-origin API calls by default and configurable remote API in `public/config.js`. |
| One-Class SVM modeled raw INR and integer hour with inconsistent scales | `log1p` amount, sine/cosine hour, and `StandardScaler` fit on normal synthetic training subset. |
| XGBoost labels defined by hardcoded `Amount > 8000`, falsely implying verified fraud | Reproducible *explicitly synthetic* label generator with overlapping amount/time distributions and stratified holdout. |
| No stable train/test split or reported evaluation | Train/holdout split and synthetic-only precision, recall, F1 diagnostics. No real-world accuracy claim. |
| CSV overwritten whenever training | In-memory data generation by default; explicit CLI CSV export only when requested. |
| `request.json` could be null or not an object | Strict JSON-type, amount, timestamp and payload-size validation, with safe errors. |
| Missing PDF control despite report claims | Printable report that uses the browser's built-in Save as PDF workflow. |
| Duplicate CSS, basic chatbot without navigation or session history | New responsive dashboard with four views, light/dark modes, session-only history, export and guided assistant. |
| No tests, CI, production server definition | pytest model/API tests, CI GitHub Action, Gunicorn and Render Blueprint. |
| Ambiguous simulation vs inference | Explicit online, offline and fixed-example demo states; no silent fallback from live API to mocked votes. |

## Verification performed in the build environment

- `python -m py_compile app.py model.py train.py generate_transactions.py` — passed.
- `node --check public/script.js` — passed.
- `pytest -q` — **20 passed, 1 skipped**. The skipped module contains Flask route tests because Flask was unavailable in this build environment. Flask is present in `requirements.txt`, and CI will run those tests after dependency installation.
- `python train.py` — passed, created a locally trusted joblib artifact.
- Held-out synthetic 840-case ensemble evaluation — precision **0.743**, recall **0.821**, F1 **0.780**. **Not real-world fraud metrics.**
- Browser smoke tests using Chromium, with frontend loaded through in-memory HTML/CSS/JS because local browser navigation is restricted in the build environment. Verified navigation, mobile no-horizontal-overflow, theme toggle, guided demo, model vote rendering, history and guided assistant without JavaScript exceptions.
- Mocked HTTP response integration in Chromium — verified live readiness badge, POST request, vote output, result source and session record. This is a frontend integration smoke test, **not** a live Flask service integration test.

## Remaining work for real-world deployment

1. Run API tests in GitHub Actions or a local environment where Flask can be installed.
2. Deploy through Render, check `/api/health`, and make end-to-end inference requests from the deployed browser.
3. For a real security product, replace synthetic data with appropriately governed, labeled data and implement authentication, rate limiting, privacy policy, auditability, drift monitoring and real-world model validation.
