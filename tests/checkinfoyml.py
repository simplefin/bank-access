#!/usr/bin/env python
"""
Copyright (c) The SimpleFIN Team
See LICENSE for details.

This script will assert that the given info.yml files meet the minimum
requirements for info.yml files.
"""

import yaml
import sys
import traceback

required = ['name', 'domain', 'maintainers']

success = True
for filename in sys.argv[1:]:
    try:
        data = yaml.load(open(filename, 'rb'))
        for field in required:
            if not data.get(field, None):
                success = False
                print '%s: missing %s field' % (filename, field)
    except:
        print 'Error reading file: %s' % (filename,)
        traceback.print_exc()
        success = False

if not success:
    sys.exit(1)
