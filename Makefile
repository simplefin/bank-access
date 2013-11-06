# Copyright (c) The SimpleFIN Team
# See LICENSE for details.

.phony: test clean


test:
	coverage run $$(which trial) banka
	-mv _trial_temp/.coverage.* .
	coverage combine
	coverage report --fail-under 100
	pyflakes banka bin/banka
	$(MAKE) pep8

pep8:
	pep8 --show-source --show-pep8 banka

clean:
	-find . -name "*.pyc" -exec rm {} \;
	-rm .coverage

