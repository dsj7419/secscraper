
# SEC Earnings Scraper

A robust data scraper designed to collect and analyze earnings data from SEC EDGAR and NASDAQ APIs. Built with modern Python, the project emphasizes scalability, reliability, and adherence to best practices like SOLID principles and async programming.

---

## Features

- **Data Models**: Structured models for company and earnings data with validation.
- **API Clients**: Reliable integration with SEC EDGAR and NASDAQ APIs.
- **Repository Layer**: Supports CSV-based storage with thread-safe operations.
- **Testing**: Comprehensive test suite with high coverage.
- **Error Handling**: Built-in retry logic and rate-limiting.

---

## Installation

### Step 1: Clone the Repository

```bash
git clone https://github.com/<your-repo-owner>/sec-earnings-scraper.git
cd sec-earnings-scraper
```

### Step 2: Create a Virtual Environment

On Unix/macOS:

```bash
python -m venv venv
source venv/bin/activate
```

On Windows:

```bash
python -m venv venv
venv\Scripts\activate
```

### Step 3: Install Dependencies

Install the project and development dependencies:

```bash
pip install -e ".[dev]"
```

---

## Usage

### Running the Scraper

To run the scraper and fetch earnings data:

```bash
python scripts/run_scraper.py --days-back 1
```

### Maintenance Tasks

To validate data or rebuild files:

```bash
python scripts/maintenance.py --validate
```

### Testing

Run the test suite:

```bash
pytest
```

Generate a coverage report:

```bash
pytest --cov=src --cov-report=html
```

---

## Configuration

### Required Environment Variables

Set these variables in a `.env` file:

```env
SEC_USER_AGENT_EMAIL=your.email@example.com
NASDAQ_API_KEY=your-api-key   # Optional
LOG_LEVEL=INFO
SEC_RATE_LIMIT_SECONDS=0.1
NASDAQ_RATE_LIMIT_SECONDS=1.0
```

### Updating the .env file

Place the `.env` file in the root directory.

---

## Project Structure

```plaintext
SEC-Earnings-Scraper/
├── config/
│   └── settings.py        # Application settings
├── scripts/
│   ├── maintenance.py     # Maintenance scripts
│   ├── run_scraper.py     # Main scraper script
│   └── test_setup.py      # Test configuration
├── src/
│   ├── clients/           # API client implementations
│   ├── models/            # Data models
│   ├── repositories/      # CSV-based data storage
│   ├── services/          # Business logic
│   ├── utils/             # Helper utilities
│   └── __init__.py
├── tests/
│   ├── unit/              # Unit tests
│   ├── integration/       # Integration tests
│   └── conftest.py        # Pytest configuration
├── .github/
│   └── workflows/
│       └── main.yml       # CI/CD pipeline configuration
├── pyproject.toml         # Project configuration
├── README.md              # Documentation
└── .env                   # Environment variables
```

---

## CI/CD Pipeline

### CICD Features

1. Automated testing and linting with GitHub Actions.
2. Code coverage reporting.
3. Pre-commit hooks for consistent code quality.

### Running CI/CD

CI/CD is triggered on every push to `main` or a pull request. Workflow includes:

- Running tests (`pytest`)
- Code formatting checks (`black`)
- Linting (`ruff`)
- Type checking (`mypy`)

---

## Contribution

We welcome contributions! Please follow these steps:

1. Fork the repository.
2. Create a feature branch.
3. Commit your changes with meaningful messages.
4. Open a pull request against the `main` branch.

Before submitting:

- Run tests: `pytest`
- Check formatting: `black .`
- Check linting: `ruff check .`

---

## License

This project is licensed under the [MIT License](LICENSE).
