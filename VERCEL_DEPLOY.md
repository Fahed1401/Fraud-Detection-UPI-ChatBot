# Vercel-only deployment — slim CPU package

## What the screenshot error meant

`[LAMBDA_SIZE_EXCEEDED] Total bundle size (524.48 MB)` means the original Python function exceeded Vercel's default 500 MB uncompressed bundle limit. It does not indicate a problem with the Flask routes or ML vote calculation.

## The fix in this edition

- `requirements.txt` selects the official small `xgboost-cpu==3.4.1` wheel on Linux x86-64 using Python >= 3.12 (Vercel's build platform), and full `xgboost` on Apple Silicon/macOS or older Python versions. `from xgboost import XGBClassifier` remains unchanged.
- `vercel.json` excludes development documents, tests, and screenshots from the function bundle.
- The frontend and Flask API share one origin, so you do not need Render or a public CORS origin.

## Update your existing GitHub repository

Clone your repository if you have not already. Copy the *contents* of this ZIP into its root, preserving `.git` (never copy `.venv` or local `.model_cache`). Then:

```bash
git status
git add -A
git commit -m "fix: slim Vercel ML function using CPU-only XGBoost"
git push origin main
```

Vercel will automatically deploy the new commit if Git integration is enabled.

## Vercel project settings

- Plan: Hobby; for personal, non-commercial portfolio projects.
- Framework: Flask / auto-detected.
- Root Directory: `./` (not `public`).
- Build/Install: use default; `pyproject.toml` builds the synthetic training model with `python train.py`.
- Python: `3.12` from `.python-version`.
- `public/config.js`: Keep `API_BASE_URL: ""` so the frontend uses its own backend.
- Enable Fluid Compute if you use the Large Functions beta.

The reduced dependency size should help bring the function below the 500 MB standard limit, but the actual packaged size can only be confirmed by Vercel's build output.

## If the size error persists

1. In Vercel, open Project → Settings → Environment Variables and set `VERCEL_SUPPORT_LARGE_FUNCTIONS` to `1` for Production and Preview.
2. Save; go to Deployments → Redeploy (disable existing build cache if offered).
3. Large Functions is a public beta with project eligibility constraints. The free plan has usage limits.
4. If the error remains, copy the complete red error line and the preceding installation output. Check whether Vercel installed `xgboost-cpu` or mistakenly installed the larger `xgboost` wheel.

## Verify

Open `https://YOUR-VERCEL-DOMAIN/api/health` and look for `"status":"ready"`. Then open the main page and test a live transaction; guided demo mode is not live ML inference.

## Local development on your Mac

From the updated project directory:

```bash
source .venv/bin/activate  # if the existing venv lives in this folder
python -m pip install -r requirements.txt
python train.py
python app.py
```

On macOS, requirements install the standard XGBoost package, so you may still need the `libomp` Homebrew library you installed earlier. The model is research-only and trained on synthetic data.
