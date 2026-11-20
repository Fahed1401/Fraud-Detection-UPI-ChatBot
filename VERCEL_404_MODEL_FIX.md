# Vercel homepage 404 + ML `not_ready` — corrected release

The two screenshots show Flask's 404 page at `/` and an older `/api/health` response:

```json
{"status":"not_ready","message":"Run python train.py to initialize the inference artifact."}
```

That message exists only in the earlier API implementation. It means the deployed version does not include the updated health-check implementation and its pre-trained model artifact (or the deployment has not been promoted to production).

## What's different in this release

- `public/` is explicitly included in the Python function **in addition to** being served by Vercel's CDN. This fixes the Flask `send_from_directory` 404 when the function bundle omitted the frontend. `/` also redirects to the CDN's `/index.html` as a fallback when running on Vercel.
- The 2.2 MB pre-trained `model_artifacts/ensemble.joblib` is bundled. The backend never trains or writes model files during a production request.
- `/api/ping` has a unique `release` marker plus `model_artifact_present` and `frontend_present` booleans to establish exactly what Vercel deployed.
- `/api/health` checks that the actual Python model loads, returning HTTP 200 and `ready`, or HTTP 503 with a safe error class if not.
- `public/config.js` uses an empty `API_BASE_URL` to request your site's own `/api/...` paths.

## Deploy to GitHub and Vercel

1. Extract the ZIP to `~/Downloads/upi-sentinel-vercel-404-model-fix`. This ZIP contains the whole project, *not just a patch*.
2. Clone the GitHub repository separately so its `.git` history is preserved:

   ```bash
   cd ~/Downloads
   git clone https://github.com/Fahed1401/Fraud-Detection-UPI-ChatBot.git upi-sentinel-publish
   rsync -av --exclude='.git/' --exclude='.venv/' --exclude='__pycache__/' \
     ~/Downloads/upi-sentinel-vercel-404-model-fix/ ~/Downloads/upi-sentinel-publish/
   cd ~/Downloads/upi-sentinel-publish
   git rm -f --ignore-unmatch index.html script.js style.css report.html
   git add -A
   git add -f model_artifacts/ensemble.joblib
   git status --short
   git commit -m "fix: bundle UPI Sentinel frontend and model for Vercel"
   git push origin main
   ```

3. In Vercel project Settings > Build & Deployment: Git repo = the above repo, production branch = `main`, Root Directory = repository root `./` (not `public`), Framework Preset = Flask, no custom Output Directory or Build Command. Keep `VERCEL_SUPPORT_LARGE_FUNCTIONS=1` if your prior build required it. The `.python-version` file specifies 3.13.
4. Confirm a **Production** deployment built the new commit. In its build logs, `model_artifacts/ensemble.joblib` should be packaged by `includeFiles` and `public/` should exist in the deployment.
5. Test these routes in order:
   - `https://frauddetection-upi-chatbot.vercel.app/api/ping` should say `release:"2026-11-20-route-model-fix"`, `model_artifact_present:true`, `frontend_present:true`.
   - `https://frauddetection-upi-chatbot.vercel.app/api/health` should return `status:"ready"` (HTTP 200).
   - `https://frauddetection-upi-chatbot.vercel.app/` should show the dashboard.
   - Submit one example transaction to verify real inference.
6. If `/api/ping` still has no `release` field, Vercel is still running an older deployment. Confirm the Git commit and deploy/Promote that deployment to Production.
7. If ping reports `model_artifact_present:false`, check the tracked artifact with `git ls-files model_artifacts/ensemble.joblib`. The file should be present in GitHub and in the deployment's function bundle.
8. If ping succeeds and health returns HTTP 503, use Vercel > Project > Logs to identify the `error_type` from `/api/health` and the complete Python traceback.

## Mac note

Local training with Python 3.9 still works through the `.model_cache` mechanism; the production artifact shipped in this ZIP was generated using Python 3.13 and the pinned dependencies in `requirements.txt`. The production artifact is only a research/synthetic-data model, not a real bank fraud classifier.
