#!/usr/bin/env python3
import sys

sys.path.insert(0, "/Users/jake/code/dancemanager")

try:
    from tests.test_store import *

    print("Tests imported successfully")
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
