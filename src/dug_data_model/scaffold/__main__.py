"""CLI entry point for the Dug data model scaffold.

Usage:
    python -m dug_data_model.scaffold new <name> [--output <path>]

Examples:
    # Create a new model package in the current directory
    python -m dug_data_model.scaffold new my_dug_model

    # Create a new model package in a specific directory
    python -m dug_data_model.scaffold new my_dug_model --output ./src/my_dug_model
"""

import argparse
import sys

from .cli import main

if __name__ == "__main__":
    sys.exit(main())
