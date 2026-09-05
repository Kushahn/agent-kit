"""Vercel entrypoint.

A three-line shim rather than the app itself: Vercel executes this file from a
directory that is not the project root, so the root has to go on sys.path before
``app`` can be imported. Getting this wrong is the classic serverless 500.
"""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from app.main import app

__all__ = ["app"]
