#!/bin/bash
# Copyright (c) The SimpleFIN Team
# See LICENSE for details.
#
# Exit with non-zero if any of the info.yml files are missing required fields.

EXIT_CODE=0
INFO_FILES=$(find . -type f | egrep '/info.yml$' | cut -c3-)
REQUIRED_FIELDS="name domain maintainers"
for infoyml in $INFO_FILES; do
    MISSING=""
    for field in $REQUIRED_FIELDS; do
        COUNT=$(grep $field $infoyml)
        RC=$?
        if [ ! $RC -eq "0" ]; then
            MISSING="$MISSING $field"
        fi
    done
    if [ ! -z "$MISSING" ]; then
        if [ $EXIT_CODE -eq 0 ]; then
            EXIT_CODE=1
            echo "*******************************************************************************"
        fi
        echo "$infoyml is missing the following required fields:"
        for field in $MISSING; do
            echo $field
        done
    fi
done
exit $EXIT_CODE
