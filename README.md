# SEC Earnings Scraper

A robust data scraper for SEC earnings information.

## Installation

Create virtual environment:
\`\`\`bash
python -m venv venv
source venv/bin/activate  # On Unix/macOS

### or

venv\\Scripts\\activate  # On Windows
\`\`\`

Install dependencies:
\`\`\`bash
pip install -e ".[dev]"
\`\`\`

## Usage

Run the scraper:
\`\`\`bash
python scripts/run_scraper.py --days-back 1
\`\`\`

## License

MIT License
