# Copyright (c) The SimpleFIN Team
# See LICENSE for details.

.phony: test test-copyright test-info-yml simplefin/banka clean

clean:
	-rm -r .gpghome
	-rm *.sqlite


.gpghome:
	python util/genkey.py .gpghome

test:
	$(MAKE) test-copyright
	$(MAKE) test-info-yml


test-copyright:
	@bash tests/check-license.sh

test-info-yml:
	@bash tests/assertminimuminfo.sh banka/inst


simplefin/banka: .gpghome
	docker build -t simplefin/banka .
