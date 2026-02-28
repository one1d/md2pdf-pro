"""MD2PDF Pro - Batch Markdown to PDF Converter."""

__version__ = "1.0.0"
__author__ = "MD2PDF Team"

from md2pdf_pro.config import ProjectConfig
from md2pdf_pro.converter import PandocEngine
from md2pdf_pro.parallel import BatchProcessor
from md2pdf_pro.preprocessor import MermaidPreprocessor

__all__ = [
    "ProjectConfig",
    "PandocEngine",
    "MermaidPreprocessor",
    "BatchProcessor",
]
