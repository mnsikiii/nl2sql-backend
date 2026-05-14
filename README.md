# BlackRock NL2SQL

An NL2SQL backend service for financial market data.  
It takes a natural-language question, generates SQL, executes it, and returns a readable answer.

## Features

- End-to-end flow: natural language -> SQL -> query execution -> answer summarization
- SQL safety constraints (SELECT-only, dangerous keyword blocking, row limiting)
- Clarification mechanism (`clarify` status with `missing_slots` for ambiguous questions)
- Three-stage safety checks (generation, validation, execution)
- FastAPI-based backend API

## Project Structure

- `src/`: Main application code (recommended primary entry for development)
  - `src/api/`: API layer
  - `src/core/`: Core business logic (NL2SQL, summarization, safety)
  - `src/utils/`: Utilities (database, LLM client, logging, formatting)
  - `src/models.py`: Request/response models
  - `src/config.py`: Environment-based configuration
- `tests/`: Automated tests
- `tests/manual/`: Manual and stage-specific test scripts
- `scripts/`: Data import and evaluation scripts

## Prerequisites

- Python 3.11+
- PostgreSQL database (or compatible, e.g., Neon)
- OpenAI API key

## Quick Start

### Option 1: Local Python Environment

1. Install dependencies

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

2. Configure environment variables

```bash
cp .env.example .env
```

Required variables:
- `DATABASE_URL`
- `OPENAI_API_KEY`

3. Start the service

```bash
python main.py
```

Default endpoints:
- `http://127.0.0.1:8000`
- Swagger: `http://127.0.0.1:8000/docs`

### Option 2: Docker

1. Build the Docker image

```bash
docker build -t nl2sql-backend .
```

2. Run the container

```bash
docker run -p 8000:8080 --env-file .env nl2sql-backend
```

Note: Ensure your `.env` file is in the current directory and contains the required variables.

## API

### Health

- `GET /api/v1/health`

### Query

- `POST /api/v1/query`
- Request body:

```json
{
  "question": "What is the average closing price of NVDA in the past 30 days?"
}
```

- Response includes:
- `status`: `ok | no_data | error | clarify`
- `final_answer`
- `sql`
- `data`
- `safety_checks`
- `meta`

## Testing

Install development dependencies:

```bash
pip install -r requirements-dev.txt
```

Run tests:

```bash
pytest tests -q
```

## Notes

- A small set of legacy root-level modules is kept for backward compatibility.
- New development should target the `src/` directory only.
- Historical reports and delivery documents are archived under `docs/archive/`.
