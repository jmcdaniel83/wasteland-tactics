.PHONY: install run clean

install:
	uv sync

run:
	uv run python main.py

clean:
	rm -rf .venv uv.lock
