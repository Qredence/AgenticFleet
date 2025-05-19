#!/usr/bin/env python3

"""
Test script for examining the SystemMessage class from autogen_core.
"""

import traceback

try:
    from autogen_core.models import SystemMessage

    # Print class information
    print("SystemMessage class information:")
    print(f"Module: {SystemMessage.__module__}")
    print(f"Class: {SystemMessage.__name__}")
    print(f"MRO: {SystemMessage.__mro__}")

    # Print attributes and methods
    print("\nAttributes and methods:")
    for attr in dir(SystemMessage):
        if not attr.startswith("__"):
            print(f"- {attr}")

    # Try to create instances with and without source
    print("\nTesting instance creation:")
    try:
        msg1 = SystemMessage(content="Test message with source", source="system")
        print(f"Created with source: {msg1}")
        print(f"Has source attribute: {hasattr(msg1, 'source')}")
        if hasattr(msg1, "source"):
            print(f"Source value: {msg1.source}")
    except Exception as e:
        print(f"Error creating with source: {e}")
        traceback.print_exc()

    try:
        msg2 = SystemMessage(content="Test message without source")
        print(f"Created without source: {msg2}")
        print(f"Has source attribute: {hasattr(msg2, 'source')}")
    except Exception as e:
        print(f"Error creating without source: {e}")
        traceback.print_exc()

    # Print initialization parameters
    print("\nInit parameters:")
    if hasattr(SystemMessage.__init__, "__code__"):
        print(f"Parameters: {SystemMessage.__init__.__code__.co_varnames}")

except ImportError as e:
    print(f"Import error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
    traceback.print_exc()
