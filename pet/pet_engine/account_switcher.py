"""
pet_engine/account_switcher.py - Account Switcher CLI entry point alias.
Enables execution via `python -m pet_engine.account_switcher`.
"""

import sys
from pet_engine.cli import main

if __name__ == "__main__":
    sys.exit(main())
