"""
Universal Claude Builder - Intelligent Claude Code Environment Generator

A universal tool that analyzes any project directory and generates optimized
Claude Code development environments with intelligent project detection and
customizable configurations.
"""

from .cli.main import main
from .core.analyzer import ProjectAnalyzer
from .core.config import Config, ConfigManager
from .core.generator import DocumentGenerator


__version__ = "0.1.0"
__author__ = "Claude Builder Team"
__description__ = "Universal Claude Code Environment Generator"


__all__ = ["Config", "ConfigManager", "DocumentGenerator", "ProjectAnalyzer", "main"]
