#!/usr/bin/env python3
"""
Validates fetched content files (.md, .html, and .json) for basic quality checks.

Checks:
- File is at least 100 bytes (minimum meaningful content)
- File is valid UTF-8

Outputs a summary with total files checked and pass/fail counts.
Exits with code 1 if any files fail validation.
Warns when a specified directory contains zero matching files.

Usage:
    python validate_content.py --input ./output/ --input ./orzecznictwo/
    python validate_content.py --input ./output/ --verbose
    python validate_content.py --input ./output/ --fail-on-empty
"""

import argparse
import logging
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

MIN_FILE_SIZE = 100  # bytes


def setup_logging(verbose: bool = False) -> None:
    """Configure logging."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def validate_file(filepath: Path, verbose: bool = False) -> bool:
    """
    Validate a single file for minimum size and valid UTF-8.

    Args:
        filepath: Path to the file to validate
        verbose: If True, log details about each file

    Returns:
        True if the file passes all checks, False otherwise
    """
    # Check minimum size
    file_size = filepath.stat().st_size
    if file_size < MIN_FILE_SIZE:
        logger.warning(
            "FAIL: %s - too small (%d bytes, minimum %d)",
            filepath, file_size, MIN_FILE_SIZE
        )
        return False

    # Check valid UTF-8
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            f.read()
    except UnicodeDecodeError as e:
        logger.warning("FAIL: %s - invalid UTF-8: %s", filepath, e)
        return False

    if verbose:
        logger.debug("PASS: %s (%d bytes)", filepath, file_size)

    return True


def find_content_files(directories: list) -> list:
    """
    Find all .md, .html, and .json files in the given directories.

    Args:
        directories: List of directory paths to scan

    Returns:
        List of Path objects for found files
    """
    files = []
    extensions = {".md", ".html", ".json"}

    for dir_path in directories:
        path = Path(dir_path)
        if not path.exists():
            logger.warning("Directory does not exist: %s", dir_path)
            continue
        if not path.is_dir():
            logger.warning("Not a directory: %s", dir_path)
            continue

        for ext in extensions:
            files.extend(path.rglob(f"*{ext}"))

    return sorted(files)


def main():
    """Main function - parse arguments and run validation."""
    parser = argparse.ArgumentParser(
        description="Validate fetched content files (.md, .html, and .json) for minimum "
                    "size and valid UTF-8 encoding.",
        epilog="Example: python validate_content.py --input ./output/ --input ./orzecznictwo/",
    )
    parser.add_argument(
        "--input", "-i",
        type=str,
        action="append",
        required=True,
        dest="input_dirs",
        help="Input directory to validate (can be specified multiple times)",
    )
    parser.add_argument(
        "--fail-on-empty",
        action="store_true",
        help="Exit with code 1 if any specified directory has zero matching files",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output (show each file result)",
    )

    args = parser.parse_args()
    setup_logging(args.verbose)

    # Check for empty directories and warn
    empty_dirs = []
    extensions = {".md", ".html", ".json"}
    for dir_path in args.input_dirs:
        path = Path(dir_path)
        if path.exists() and path.is_dir():
            dir_files = []
            for ext in extensions:
                dir_files.extend(path.rglob(f"*{ext}"))
            if not dir_files:
                logger.warning(
                    "Directory '%s' contains zero .md/.html/.json files", dir_path
                )
                empty_dirs.append(dir_path)

    # Find all content files
    files = find_content_files(args.input_dirs)

    if not files:
        print("No .md, .html, or .json files found in specified directories.")
        print(f"Directories checked: {', '.join(args.input_dirs)}")
        if args.fail_on_empty:
            print("\nFAILED: --fail-on-empty specified and no files found.")
            sys.exit(1)
        sys.exit(0)

    if empty_dirs and args.fail_on_empty:
        print(f"\nWARNING: Empty directories (no matching files): {', '.join(empty_dirs)}")

    # Validate each file
    pass_count = 0
    fail_count = 0

    for filepath in files:
        if validate_file(filepath, verbose=args.verbose):
            pass_count += 1
        else:
            fail_count += 1

    # Print summary
    total = pass_count + fail_count
    print(f"\nValidation Summary:")
    print(f"  Total files checked: {total}")
    print(f"  Passed: {pass_count}")
    print(f"  Failed: {fail_count}")

    if empty_dirs:
        print(f"  Empty directories: {', '.join(empty_dirs)}")

    if fail_count > 0:
        print(f"\nValidation FAILED: {fail_count} file(s) did not pass checks.")
        sys.exit(1)
    elif empty_dirs and args.fail_on_empty:
        print(f"\nValidation FAILED: {len(empty_dirs)} directory(ies) had zero matching files.")
        sys.exit(1)
    else:
        print("\nAll files passed validation.")
        sys.exit(0)


if __name__ == "__main__":
    main()
