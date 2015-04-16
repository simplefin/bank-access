# Copyright (c) The SimpleFIN Team
# See LICENSE for details.

.phony: test test-copyright test-info-yml


test:
	$(MAKE) test-copyright
	$(MAKE) test-info-yml


test-copyright:
	@bash tests/check-license.sh

test-info-yml:
	@bash tests/assertminimuminfo.sh banka
