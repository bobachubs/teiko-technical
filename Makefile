.PHONY: setup pipeline dashboard

setup:
	pip install -r requirements.txt

pipeline:
	rm -f teiko.db
	python load_data.py
	python analysis.py

dashboard:
	streamlit run app.py
