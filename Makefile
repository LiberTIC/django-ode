
# virtualenv_wrapper compatible names
VIRTUALENVWRAPPER_VIRTUALENV?=virtualenv
VIRTUAL_ENV?=venv

PYTHON=$(VIRTUAL_ENV)/bin/python
PIP=$(VIRTUAL_ENV)/bin/pip
COVERAGE=$(VIRTUAL_ENV)/bin/coverage
OMIT='./install/*,./node-v0.10.22-linux-x64/'
TEST_COMMAND=manage.py test frontend accounts
COLLECT_STATIC=python manage.py collectstatic --noinput
NPM=npm

$(PYTHON):
	$(VIRTUALENV) $(VIRTUAL_ENV)

virtualenv: $(PYTHON)

dev_requirements:
	$(PIP) install -r dev_requirements.txt
	sudo $(NPM) install -g grunt-cli
	$(NPM) install
	grunt

install:
	$(PYTHON) setup.py install
	$(PYTHON) manage.py syncdb --noinput

develop: dev_requirements
	$(PYTHON) setup.py develop
	$(PYTHON) manage.py syncdb --noinput

$(FLAKE8): virtualenv
	$(PIP) install flake8

test: develop flake8
	$(PYTHON) $(TEST_COMMAND)

coverage: develop
	$(COVERAGE) run --branch --source=. --omit=$(OMIT) $(TEST_COMMAND)
	$(COVERAGE) report -m

start: $(PROC) .env
	$(PROC) start -f $(PROCFILE)

backup:
	#TODO

flake8: $(FLAKE8)
	flake8 --exclude=$(OMIT) .

serve:
	python manage.py runserver
