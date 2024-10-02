.PHONY: run install test

# Target to run the application server
run:
	python app.py

# Target to install dependencies
install:
	pip install -r requirements.txt

# Target to run test cases
test:
	python -m unittest discover -s tests

