.PHONY: install ingest serve ui retrieval-eval eval test

PYTHON ?= python3

install:
	pip install -r requirements.txt

ingest:
	$(PYTHON) -m app.ingest

serve:
	uvicorn app.main:app --reload

ui:
	streamlit run ui/streamlit_app.py

# Retrieval metrics only: no API key, no cost
retrieval-eval:
	$(PYTHON) -m evals.retrieval_only

# Full eval including LLM-judged faithfulness (needs a generation API key)
eval:
	$(PYTHON) -m evals.run_evals

test:
	pytest -q
