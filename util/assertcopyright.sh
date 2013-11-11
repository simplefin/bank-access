#!/bin/bash
# Copyright (c) The SimpleFIN Team
# See LICENSE for details.
#
# Exit with non-zero if there are files missing copyright.

ALL_FILES=$(find . -type f | egrep '\.(py|sh|md)$' | cut -c3- | grep -v '/_' | sort)
HAVE_COPYRIGHT=$(grep -rl "Copyright (c) The SimpleFIN Team" * | sort)
MISSING=$(diff --unchanged-line-format= --old-line-format='%L' --new-line-format= <(echo "$ALL_FILES") <(echo "$HAVE_COPYRIGHT"))

if [ ! -z "$MISSING" ]; then
    echo "*******************************************************************************"
	echo "The following $(echo "$MISSING" | wc -l) file(s) are missing copyright notices:"
	echo "$MISSING"
    echo "*******************************************************************************"
	exit 1
fi