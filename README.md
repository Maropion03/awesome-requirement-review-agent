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
uvicorn main:app --reload
```

## Run frontend

```bash
cd frontend
npm install
npm run dev
```

## Verify

```bash
python3 -m unittest discover -q
cd frontend && npm run build
```
