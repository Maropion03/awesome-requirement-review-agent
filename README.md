# repo-b

Independent web repository for the PRD reviewer product.

## Contents

- `backend/`: FastAPI application
- `frontend/`: Vue 3 application
- `docs/`: Web design documents

## Run backend

```bash
cd backend
cp .env.example .env
# edit .env with your local values before starting the app
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8005
```

## Run frontend

```bash
cd frontend
npm install
npm run dev
```

默认会监听 `http://127.0.0.1:5176`，并通过 `/api` 代理到后端 `http://127.0.0.1:8005`。

## Verify

```bash
python3 -m unittest discover -q
cd frontend && npm run build
```
