#!/usr/bin/env python
"""
Test runner script for SEC Earnings Scraper.
Cross-platform compatible test runner.
"""
import os
import sys
import pytest
from pathlib import Path

def setup_paths():
    """Configure system paths for testing."""
    # Get the paths - handles the SECScraper/SECScraper nested structure
    current_dir = Path(__file__).resolve().parent
    project_dir = current_dir.parent
    
    # Double-check we're in the right spot and fix path if needed
    if project_dir.name == "SECScraper" and project_dir.parent.name == "SECScraper":
        project_dir = project_dir.parent
    
    src_dir = project_dir / "SECScraper" / "src"
    
    # Validate directories
    if not src_dir.exists():
        print(f"Error: Source directory not found at {src_dir}")
        sys.exit(1)
        
    # Add to Python path
    sys.path.insert(0, str(project_dir))
    sys.path.insert(0, str(src_dir))
    
    return current_dir

def main():
    """Run all tests with pytest."""
    tests_dir = setup_paths()
    
    # Configure pytest arguments
    args = [
        "--asyncio-mode=auto",
        "--capture=no",
        "--verbose",
        "--color=yes",
        "--cov=src",
        "--cov-report=term-missing",
        "--cov-report=html:tests/coverage",  # Generate HTML coverage report
        "--rootdir", str(tests_dir),  # Set root directory explicitly
        "-c", str(tests_dir / "pytest.ini"),  # Specify config file location
        ".",  # Run tests in current directory
        "-W", "ignore::DeprecationWarning",
        "-W", "ignore::pytest.PytestDeprecationWarning",
    ]
    
    print("\nRunning tests with configuration:")
    print(f"Test Directory: {tests_dir}")
    print(f"Python Path: {sys.path[0:2]}\n")
    
    try:
        result = pytest.main(args)
        
        # Print coverage report location if tests run successfully
        if result == 0:
            coverage_dir = tests_dir / "coverage"
            print(f"\nHTML coverage report generated at: {coverage_dir / 'index.html'}")
            
        sys.exit(result)
    except Exception as e:
        print(f"Error running tests: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()