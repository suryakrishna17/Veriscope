# Unix/macOS convenience targets. Windows users: see README "Run locally".
PY ?= python3

.PHONY: install fixtures seed reset api web dev test e2e lint build docker clean

install:            ## install backend + frontend dependencies
	cd backend && $(PY) -m pip install -r requirements-dev.txt
	cd frontend && npm install

fixtures:           ## regenerate synthetic demo documents
	cd backend && $(PY) -m scripts.generate_fixtures

seed:               ## create demo users and cases (idempotent)
	cd backend && $(PY) -m scripts.seed

reset:              ## wipe local data and re-seed
	cd backend && $(PY) -m scripts.reset

api:                ## run the API on :8000
	cd backend && $(PY) wsgi.py

web:                ## run the Vite dev server on :5173 (proxies /api to :8000)
	cd frontend && npm run dev

dev:                ## run API and web together
	$(MAKE) -j2 api web

test:               ## backend test suite
	cd backend && $(PY) -m pytest -q

e2e:                ## browser walkthrough against a running, freshly seeded app
	cd frontend && npm run e2e

lint:
	cd backend && ruff check app scripts tests && mypy app
	cd frontend && npm run typecheck

build:              ## production frontend build (served by the API from frontend/dist)
	cd frontend && npm run build

docker:             ## build and run everything in Docker on :8000
	docker compose up --build

clean:
	rm -rf backend/var frontend/dist
