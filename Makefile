VENV:=.venv/bin/python
REQ_TEST:=requirements.test.txt

.venv: $(REQ_TEST)
	python -m venv .venv
	$(VENV) -m pip install --upgrade pip
	$(VENV) -m pip install -r $(REQ_TEST)
	touch .venv

.PHONY: test
test: .venv
	$(VENV) -m pytest
