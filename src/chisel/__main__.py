"""
Entry point for running Chisel as a module.

Usage: python -m chisel
"""

from .app import main

if __name__ == "__main__":
    exit(main())