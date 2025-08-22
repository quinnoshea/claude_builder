#!/usr/bin/env python3
"""Fix coverage.xml paths for external tools like Codacy.

This script fixes path issues in coverage.xml files generated from src layout projects.
External tools like Codacy expect paths to be relative to the project root without
the src/ prefix, while coverage.py generates paths with src/ when using src layout.
"""
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def fix_coverage_paths(coverage_file: str) -> None:
    """Fix coverage.xml paths for external tools.

    Args:
        coverage_file: Path to the coverage.xml file to fix
    """
    if not Path(coverage_file).exists():
        sys.exit(1)

    try:
        tree = ET.parse(coverage_file)
        root = tree.getroot()

        # Track changes made
        changes_made = 0

        # Fix source paths in <source> elements
        for source in root.findall(".//source"):
            if source.text and "src/claude_builder" in source.text:
                source.text = source.text.replace("src/claude_builder", "claude_builder")
                changes_made += 1

        # Fix filename attributes in <class> elements
        for cls in root.findall(".//class"):
            filename = cls.get("filename", "")
            if filename.startswith("src/"):
                new_filename = filename[4:]  # Remove 'src/' prefix
                cls.set("filename", new_filename)
                changes_made += 1

        # Fix filename attributes in <package> elements
        for package in root.findall(".//package"):
            name = package.get("name", "")
            if name.startswith("src."):
                new_name = name[4:]  # Remove 'src.' prefix
                package.set("name", new_name)
                changes_made += 1

        # Save the modified file
        tree.write(coverage_file, encoding="utf-8", xml_declaration=True)


    except ET.ParseError:
        sys.exit(1)
    except Exception:
        sys.exit(1)


def main() -> None:
    """Main entry point."""
    coverage_file = "coverage.xml" if len(sys.argv) < 2 else sys.argv[1]

    fix_coverage_paths(coverage_file)


if __name__ == "__main__":
    main()
