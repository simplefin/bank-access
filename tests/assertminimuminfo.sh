#!/bin/bash
# Copyright (c) The SimpleFIN Team
# See LICENSE for details.
#
# Exit with non-zero if any of the info.yml files are missing required fields.

EXIT_CODE=0
INSTDIR=$1
INSTDIRS=$(find $INSTDIR -type d -depth 1)
REQUIRED_FIELDS="name domain maintainers"
for instdir in $INSTDIRS; do
    infoyml="${instdir}/info.yml"
    if [ ! -e $infoyml ]; then
        EXIT_CODE=1
        echo "missing file: $infoyml"
        continue
    fi
    if ! $(python tests/checkinfoyml.py $infoyml); then
        EXIT_CODE=1
    fi
done
exit $EXIT_CODE
