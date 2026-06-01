# This file makes the models directory a Python package
from .db import get_db

__all__ = ['get_db']