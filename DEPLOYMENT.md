# Deployment and GitHub update guide

This repository contains a **static frontend in `public/`** and a **stateful Python/Flask inference API**. A static-only deployment does not run the ML models. All instructions below assume you own the GitHub repository.

## Step 1 — Download and inspect the update

Unzip the `UPI-Sentinel-Portfolio-Upgrade.zip` package. Make sure it contains `app.py`, `model.py`, `render.yaml`, `requirements.txt`, and the `public/` directory.

## Step 2 — Replace the files in your existing repository

On macOS Terminal:

```bash
cd ~/Desktop
# Skip this clone command if your repository is already cloned locally.
git clone https://github.com/Fahed1401/Fraud-Detection-UPI-ChatBot.git
cd Fraud-Detection-UPI-ChatBot

# Optional safety checkpoint for your original code:
git switch -c feature/upi-sentinel-dashboard

# Remove legacy frontend and generated dataset files; new UI is in public/.
git rm --ignore-unmatch index.html style.css script.js report.html transactions.csv

# Copy the CONTENTS of the extracted upgrade folder into this repo.
# Replace the source path with your actual Downloads location:
rsync -av --exclude='.git' --exclude='.model_cache' ~/Downloads/upi-fraud-detection-upgrade/ ./

git status
git add -A
git commit -m "feat: build UPI Sentinel dashboard and refactor fraud ensemble"
git push -u origin feature/upi-sentinel-dashboard
```

Then open GitHub → your repository → **Compare & pull request** → merge into `main` after GitHub Actions passes. If you prefer direct updates, run `git switch main`, commit there, and `git push origin main` instead. If you've already made changes to the old repository, stash or commit them before replacing files.

## Step 3 — Test locally

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
python train.py
python -m pytest -q
python app.py
```

Open **http://127.0.0.1:5001**. Expect a **green ML engine online** badge. Click **Analyze transaction**, use each sample preset, and check model votes, history, CSV export and Save PDF. To verify the actual API:

```bash
curl http://127.0.0.1:5001/api/health
curl -X POST http://127.0.0.1:5001/api/check_fraud \
  -H "Content-Type: application/json" \
  -d '{"amount":1250,"timestamp":"2026-11-18T14:25"}'
```

## Step 4A — Easiest: deploy the entire app on Render

1. Sign in to **https://dashboard.render.com** and connect GitHub.
2. Choose **New → Blueprint**, select your updated repository, and use its root `render.yaml`.
3. Review the service plan and region before approving. `render.yaml` requests the **free** plan (subject to current availability and restrictions); choose a paid plan if required for memory, reliability or uptime.
4. Render builds the app with `pip install -r requirements.txt && python train.py` and starts it with Gunicorn.
5. Once deployed, open `https://YOUR-SERVICE.onrender.com/api/health`. It should return `"status":"ready"`.
6. Visit the same URL without `/api/health`. The complete frontend should load and show **ML engine online**. No `config.js` changes are needed because both sides are hosted together.

If you deploy manually as a Render Web Service rather than Blueprint:

- Runtime: **Python**
- Build command: `pip install -r requirements.txt && python train.py`
- Start command: `gunicorn --bind 0.0.0.0:$PORT --workers 1 --threads 4 --timeout 120 app:app`
- Health path: `/api/health`
- Python runtime: 3.11 (or another supported version compatible with dependencies)

Free instances can have availability, idle-sleep, resource or usage limits depending on Render's current offering. Retraining writes to the build environment; deployments are immutable and do not preserve runtime data between releases. This app has no server-side transaction database.

## Step 4B — Optional: Vercel frontend + Render backend

This is useful if you want the public UI on Vercel while keeping heavy Python ML dependencies off Vercel.

1. Finish **Step 4A** first so your Flask backend is reachable at `https://YOUR-SERVICE.onrender.com`.
2. In `public/config.js`, set:

   ```js
   window.UPI_CONFIG = { API_BASE_URL: "https://YOUR-SERVICE.onrender.com" };
   ```

3. Commit and push the config change.
4. On Render → your service → **Environment**, add `CORS_ORIGINS` with the **exact Vercel domain**, e.g. `https://your-project.vercel.app` (no trailing slash). If you have a custom domain, add it separated by a comma, then redeploy.
5. In Vercel → **Add New → Project** → Import the GitHub repository. Set **Root Directory: `public`**, **Framework Preset: Other**, **Build Command: none**, **Output Directory: default**; deploy.
6. On the Vercel URL, check the status badge and inspect browser developer tools → Network for `/api/health` and `/api/check_fraud` requests going to your Render service.

**Do not deploy the whole repository as one Vercel static site** and expect the Python ensemble to run: the Python backend will not start from HTML/CSS/JS hosting alone. Do not set `API_BASE_URL` to `localhost` in a hosted site.

### Common deployment issues

| Symptom | Cause / fix |
| --- | --- |
| Vercel 404 | Confirm root directory is `public`, which contains `index.html`. |
| Badge says Engine unavailable | The Flask backend is offline, `config.js` points at the wrong URL, or `/api/health` returns 503. Deploy and train backend first. |
| CORS error in browser console | Set Render `CORS_ORIGINS` to the exact `https://...vercel.app` origin and redeploy. Do not use `*` on an open financial demo API. |
| Python dependency build error | Use Python 3.11/3.12 and install with `requirements.txt`; inspect the first failing install step in Render logs. |
| Model not ready | Run `python train.py` during build. `render.yaml` already does this. |
| Missing assets | Check `public/index.html`, `public/style.css`, `public/script.js`, and `public/config.js` all exist and match case exactly. |
| PDF button opens Print | Intended: choose **Save as PDF** in the system print dialog. No hidden server-side PDF service is claimed. |

## Step 5 — Showcase it on your resume

Add the deployed URL as a GitHub repository **Website** in its About section, and include it near the project title on your resume. Clearly describe it as an ML **research prototype trained on synthetic data**, not a production anti-fraud platform. Use the README screenshots for your GitHub project introduction.
