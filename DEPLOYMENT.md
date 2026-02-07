# Deployment Guide

This guide covers deploying the Financial RAG Analyst to production using **GitHub Pages** (Frontend) and **Railway/Render** (Backend).

## 1. Backend Deployment (Railway)

We recommend [Railway](https://railway.app/) for the backend as it simplifies Docker deployment.

1.  **Fork/Clone Repo**: Ensure your code is on GitHub.
2.  **Sign up for Railway**: Log in with GitHub.
3.  **New Project**: Click "New Project" -> "Deploy from GitHub repo".
4.  **Select Repository**: Choose your `financial-analyst` repo.
5.  **Configure Service**:
    *   Railway will likely detect the `Dockerfile`.
    *   Go to **Variables**: Add `GOOGLE_API_KEY` with your actual API key.
    *   **Port**: Ensure it is set to `8000`.
6.  **Deploy**: Railway will build and deploy.
7.  **Get URL**: Once live, copy the public URL (e.g., `https://financial-analyst-production.up.railway.app`).

## 2. Frontend Deployment (GitHub Pages)

1.  **Update API URL**:
    *   Go to your GitHub Repository > **Settings** > **Secrets and variables** > **Actions**.
    *   Click **New repository variable**.
    *   Name: `API_BASE_URL`
    *   Value: Your Railway URL (e.g., `https://financial-analyst-production.up.railway.app`) - *No trailing slash*.
2.  **Enable Pages**:
    *   Go to **Settings** > **Pages**.
    *   Source: **GitHub Actions**.
3.  **Trigger Deploy**:
    *   Push a commit to `main` OR go to **Actions** tab > **Deploy Frontend** > **Run workflow**.

## 3. Vercel Deployment (Alternative Frontend)

If you prefer Vercel for the frontend:

1.  Install Vercel CLI: `npm i -g vercel`
2.  Run `vercel` in the `frontend/` directory.
3.  Configure Build settings:
    *   Framework: Other
    *   Output Directory: `.` (Current directory)
4.  **Environment Variables**:
    *   For a static site, you cannot inject env vars at runtime easily without a build step.
    *   **Workaround**: Hardcode the production URL in `frontend/js/app.js` BEFORE deploying to Vercel, or use the GitHub Pages method which handles this via `sed` replacement during CI/CD.

## troubleshooting

*   **CORS Error**: If frontend fails to talk to backend, ensure your Backend `main.py` CORS origins include your frontend domain.
*   **Health Check**: Visit `https://your-backend.app/health` to verify it's running.
