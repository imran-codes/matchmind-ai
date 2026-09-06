.PHONY: train test api web build
train:
	PYTHONPATH=backend python -m app.train
test:
	PYTHONPATH=backend python -m pytest backend/tests -q
api:
	PYTHONPATH=backend uvicorn app.main:app --reload --port 8000 --no-access-log
web:
	cd frontend && npm ci && npm run dev
build:
	cd frontend && npm ci && npm run build
