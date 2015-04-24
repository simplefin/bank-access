#!/bin/bash
# Copyright (c) The SimpleFIN Team
# See LICENSE for details.

set -e
MISSING=$(grep -Lr \
    --exclude='*.js' \
    --exclude='*.pyc' \
    --exclude='tox.ini' \
    --exclude-dir='siloscript.egg-info' \
    --exclude='_trial_temp/*' \
    --exclude='requirements.txt' \
    --exclude=LICENSE \
    --exclude='*.sublime-*' \
    --exclude-dir='util/samplekeys' \
    "Copyright (c) The SimpleFIN Team" \
    *)

if [ ! -z "$MISSING" ]; then
    echo "Missing copyright on:"
    echo "$MISSING"
    exit 1
fi