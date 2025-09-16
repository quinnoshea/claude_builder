#!/usr/bin/env python3
"""Fix coverage.xml paths for external tools like Codacy.

This script fixes path issues in coverage.xml files generated from src-layout
projects. External tools often expect paths relative to the project root without
the `src/` prefix.
"""

import logging
import sys

from pathlib import Path


try:  # Prefer hardened XML parsing when available
    from defusedxml import ElementTree as ET  # type: ignore[import-not-found]
except Exception:  # Fallback remains safe for local CI artifact rewriting
    import xml.etree.ElementTree as ET  # noqa: S314


LOGGER = logging.getLogger("fix_coverage_paths")


def fix_coverage_paths(coverage_file: str) -> None:
    """Fix coverage.xml paths for external tools.

    Args:
        coverage_file: Path to the coverage.xml file to fix
    """
    path = Path(coverage_file)
    if not path.exists():
        LOGGER.error("Coverage file not found: %s", coverage_file)
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
                LOGGER.info("Fixed source path: %s -> %s", old_text, source.text)
                changes_made += 1

        # Fix filename attributes in <class> elements
        for cls in root.findall(".//class"):
            filename = cls.get("filename", "")
            if filename.startswith("src/"):
                old_filename = filename
                new_filename = filename[4:]  # Remove 'src/' prefix
                cls.set("filename", new_filename)
                LOGGER.info(
                    "Fixed class filename: %s -> %s", old_filename, new_filename
                )
                changes_made += 1

        # Fix filename attributes in <package> elements
        for package in root.findall(".//package"):
            name = package.get("name", "")
            if name.startswith("src."):
                old_name = name
                new_name = name[4:]  # Remove 'src.' prefix
                package.set("name", new_name)
                LOGGER.info("Fixed package name: %s -> %s", old_name, new_name)
                changes_made += 1

        # Save the modified file
        tree.write(coverage_file, encoding="utf-8", xml_declaration=True)

        LOGGER.info("Coverage paths fixed successfully!")
        LOGGER.info("Total changes made: %d", changes_made)
        LOGGER.info("Updated file: %s", coverage_file)

    except ET.ParseError as err:
        LOGGER.error("Error parsing coverage.xml: %s", err)
        sys.exit(1)
    except (OSError, ValueError) as err:
        LOGGER.error("Error processing coverage file: %s", err)
        sys.exit(1)


def main() -> None:
    """Main entry point."""
    MIN_ARGS = 2
    if len(sys.argv) < MIN_ARGS:
        coverage_file = "coverage.xml"  # default path in CI workspace
        LOGGER.info("No coverage file specified, using default: %s", coverage_file)
    else:
        coverage_file = sys.argv[1]

    LOGGER.info("Fixing coverage paths in: %s", coverage_file)
    fix_coverage_paths(coverage_file)


if __name__ == "__main__":
    main()
