.PHONY: backend frontend dev build clean

BACKEND_DIR := backend
FRONTEND_DIR := frontend
BACKEND_HOST ?= 127.0.0.1
BACKEND_PORT ?= 8000

backend:
	@echo "Starting backend at http://$(BACKEND_HOST):$(BACKEND_PORT)"
	@cd $(BACKEND_DIR) && set -a; [ ! -f .env ] || . ./.env; set +a; python3 -m uvicorn main:app --reload --host "$${HOST:-$(BACKEND_HOST)}" --port "$${PORT:-$(BACKEND_PORT)}"

frontend:
	@echo "Starting frontend at http://127.0.0.1:5173"
	@cd $(FRONTEND_DIR) && pnpm run dev

dev:
	@echo "Starting backend and frontend."
	@echo "Backend:  http://$(BACKEND_HOST):$(BACKEND_PORT)"
	@echo "Frontend: http://127.0.0.1:5173"
	@echo "Press Ctrl+C to stop both processes."
	@trap 'kill 0' INT TERM EXIT; \
		( $(MAKE) backend ) & \
		( $(MAKE) frontend ) & \
		wait

build:
	@echo "Checking backend syntax..."
	@cd $(BACKEND_DIR) && python3 -m py_compile main.py
	@echo "Building frontend..."
	@cd $(FRONTEND_DIR) && pnpm build

clean:
	@echo "Removing generated artifacts..."
	@rm -rf $(FRONTEND_DIR)/dist
	@find . -type d -name __pycache__ -prune -exec rm -rf {} +
	@find . -type f -name "*.pyc" -delete
	@find . -type f -name "*.tsbuildinfo" -delete
