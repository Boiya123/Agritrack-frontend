# Monorepo Merge Documentation (Frontend + Backend)

This document explains how the frontend and backend repositories were merged into a single local monorepo for easier navigation, development, and presentations. It focuses on what changed, why it is safe, and how to reproduce the merge if needed.

---

## Executive Summary

- The backend repo was pulled into this workspace as a **git subtree** under `backend/`.
- The frontend was moved into `frontend/` to create a clean two-folder monorepo layout.
- This merge was performed **locally only** and does **not** alter the backend GitHub repository.
- All history from the backend is preserved inside this local repo under the `backend/` subtree.

---

## Final Layout

```
repo-root/
├── backend/   # FastAPI + blockchain services (from agritrack-backend repo)
└── frontend/  # Vite React app (this original frontend repo)
```

---

## Why This Merge Is Safe

- The backend GitHub repo remains unchanged because the merge used `git fetch` + `git subtree add` locally.
- No backend code was pushed to the backend remote.
- The frontend repo can be pushed to a **new combined repo** if desired.

---

## Merge Method (Exact Steps)

1) Add backend repo as a remote (local only):

```
git remote add backend https://github.com/LanceBigInt/agritrack-backend.git
```

2) Fetch backend history (no file changes yet):

```
git fetch backend
```

3) Merge backend into `backend/` as a subtree (preserves history):

```
git subtree add --prefix backend backend/main
```

4) Move frontend files into `frontend/` for clean layout:

```
mkdir -p frontend

git mv eslint.config.js index.html package.json package-lock.json public src vite.config.js README.md frontend/
```

---

## Navigation Benefits

- Clear separation of concerns
- One repo to open in VS Code
- Full backend docs remain intact in `backend/`
- Full frontend assets remain intact in `frontend/`

---

## What Did NOT Change

- No backend remote history was edited or rewritten.
- No backend files were overwritten by frontend files.
- Backend deployment steps and documentation are still valid.

---

## How To Present This Merge

Suggested talking points:

- "We combined two repos into a single monorepo locally for easier development."
- "The merge uses git subtree, so backend history is preserved."
- "The backend GitHub repo is untouched; we can still work on it separately."
- "The frontend now consumes the backend API directly from this same workspace."

---

## Optional: Split Back Out Later

If you ever need to split again, the backend subtree contains its own history. It can be pushed to a new repo by extracting the subtree from `backend/`.

---

## Live Demo Checklist

- Start backend: `cd backend` then run `uvicorn app.main:app --reload --port 8000`.
- Start frontend: `cd frontend` then run `npm install` and `npm run dev`.
- Open the Operations console at `/ops` and show:
  - Product creation
  - Batch creation
  - Lifecycle events
  - Logistics
  - Processing
  - Regulatory approvals

---

## Notes For Slides

- Title: "AgriTrack Monorepo Merge"
- Diagram: Two boxes (Frontend + Backend) -> one box (Monorepo)
- Emphasize: "Local-only merge, safe, reversible"
