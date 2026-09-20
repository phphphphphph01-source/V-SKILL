"""Validate Library content after the application has initialized its database.

Usage: python tools/validate_library.py
"""
from app import app
from core.library import validate_library

with app.app_context():
    warnings = validate_library()
    if warnings:
        print(f"LIBRARY WARNINGS: {len(warnings)}")
        for warning in warnings:
            print(f"- {warning}")
    else:
        print("LIBRARY VALIDATION PASSED")
