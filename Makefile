.PHONY: run install test deploy

# Target to run the application server
run:
	gunicorn -w 4 -b 127.0.0.1:5000 'app:create_app()'

# Target to install dependencies
install:
	pip install -r requirements.txt

# Target to run test cases
test:
	python -m unittest discover -s tests

# Clean up compiled Python files
clean:
	find . -name "*.pyc" -exec rm -f {} \;
