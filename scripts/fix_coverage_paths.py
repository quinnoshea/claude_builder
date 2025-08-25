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
        print(f"Error: Coverage file not found: {coverage_file}")
        sys.exit(1)

    try:
        tree = ET.parse(coverage_file)
        root = tree.getroot()

        # Track changes made
        changes_made = 0

        # Fix source paths in <source> elements
        for source in root.findall(".//source"):
            if source.text and "src/claude_builder" in source.text:
                old_text = source.text
                source.text = source.text.replace(
                    "src/claude_builder", "claude_builder"
                )
                print(f"Fixed source path: {old_text} -> {source.text}")
                changes_made += 1

        # Fix filename attributes in <class> elements
        for cls in root.findall(".//class"):
            filename = cls.get("filename", "")
            if filename.startswith("src/"):
                old_filename = filename
                new_filename = filename[4:]  # Remove 'src/' prefix
                cls.set("filename", new_filename)
                print(f"Fixed class filename: {old_filename} -> {new_filename}")
                changes_made += 1

        # Fix filename attributes in <package> elements
        for package in root.findall(".//package"):
            name = package.get("name", "")
            if name.startswith("src."):
                old_name = name
                new_name = name[4:]  # Remove 'src.' prefix
                package.set("name", new_name)
                print(f"Fixed package name: {old_name} -> {new_name}")
                changes_made += 1

        # Save the modified file
        tree.write(coverage_file, encoding="utf-8", xml_declaration=True)

        print("\nCoverage paths fixed successfully!")
        print(f"Total changes made: {changes_made}")
        print(f"Updated file: {coverage_file}")

    except ET.ParseError as e:
        print(f"Error parsing coverage.xml: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error processing coverage file: {e}")
        sys.exit(1)


def main() -> None:
    """Main entry point."""
    if len(sys.argv) < 2:
        coverage_file = "coverage.xml"
        print(f"No coverage file specified, using default: {coverage_file}")
    else:
        coverage_file = sys.argv[1]

    print(f"Fixing coverage paths in: {coverage_file}")
    fix_coverage_paths(coverage_file)


if __name__ == "__main__":
    main()
