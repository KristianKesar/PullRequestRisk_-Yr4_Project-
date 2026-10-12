# sample_bad_code.py
# Kristian Kesar, C00296348
#
# Test input for the PR Risk workflow. Contains known issues so I can
# confirm the GitHub integration picks them up and comments on the PR.

import os    # unused import (F401)
import sys   # unused import (F401)


def calculate_total(items):
    total = 0
    unused_value = 42   # assigned but never used (F841)
    for item in items:
        total += item
    return totl         # undefined name (F821)


def check_value(x):
    if x == None:       # should be "is None" (E711)
        return False
    return True
