# Copyright (c) The SimpleFIN Team
# See LICENSE for details.

.phony: test clean test-copyright


test:
	pyflakes banka bin/banka
	$(MAKE) pep8
	$(MAKE) test-copyright
	$(MAKE) test-info-yml
	coverage run $$(which trial) banka
	-mv _trial_temp/.coverage.* .
	coverage combine
	coverage report --fail-under 100

pep8:
	pep8 --show-source --show-pep8 banka

clean:
	-find . -name "*.pyc" -exec rm {} \;
	-rm .coverage
	-rm .coverage.*
	-rm -r htmlcov
	-rm -r dist
	-rm -r banka.egg-info
	-rm -r _trial_temp
	-rm -r build

test-copyright:
	@bash util/assertcopyright.sh

test-info-yml:
	@bash util/assertminimuminfo.sh