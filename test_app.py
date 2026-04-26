#!/usr/bin/env python3
"""Test the Dance Manager web app."""
from dancemanager.api import create_app

app = create_app()
print("App created successfully")
