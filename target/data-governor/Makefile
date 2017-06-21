.PHONY: clean

export GOVERNOR_ENV?=dev

clean:
	rm -rf governor_env htmlcov results_* coverage_* *.out && \
	find . -type f -iname "*.pyc" -exec rm '{}' \;

install:
	virtualenv governor_env && \
	source governor_env/bin/activate && \
	pip install --allow-all-external --allow-unverified mysql-connector-python -r requirements.txt

test: install
	source governor_env/bin/activate && \
	pep8 --config=.pep8 endpoints > pep8.out &&  \
	pylint --rcfile=.pylintrc -f parseable endpoints > pylint.out ||  \
	py.test test "--junitxml=results_$(BUILD_ID).xml" --cov=. --cov-report=xml --cov-report=html

