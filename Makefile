
.phony: test clean


test:
	coverage run $$(which trial) banka
	coverage report --fail-under 100
	pyflakes banka
	pep8 --show-source --show-pep8 banka

clean:
	-find . -name "*.pyc" -exec rm {} \;
	-rm .coverage

