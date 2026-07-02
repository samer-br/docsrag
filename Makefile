.PHONY: install ingest serve ui eval test

install:
	pip install -r requirements.txt

ingest:
	python -m app.ingest

serve:
	uvicorn app.main:app --reload

ui:
	streamlit run ui/streamlit_app.py

eval:
	python -m evals.run_evals

test:
	pytest -q
