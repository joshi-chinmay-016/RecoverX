"""Pytest configuration and environment fixtures for RecoverX test suite."""

import sys
import os

# Ensure backend root is always in Python module path
BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)
