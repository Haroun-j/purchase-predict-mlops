"""
This is a boilerplate pipeline 'training'
generated using Kedro 1.3.1
"""

from dotenv import load_dotenv

from .pipeline import create_pipeline

load_dotenv()

__all__ = ["create_pipeline"]

__version__ = "0.1"
