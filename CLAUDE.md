# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a RAGAS (Retrieval-Augmented Generation Assessment) evaluation framework implementation in Python. It evaluates RAG pipelines using four metrics: Faithfulness, Answer Relevancy, Context Precision, and Context Recall.

## Architecture

The project follows Clean Architecture with clear separation of concerns:

- `src/domain/` - Core domain models (evaluation data structures)
- `src/application/` - Business logic and port interfaces
- `src/infrastructure/` - External adapters (LLM, storage, RAGAS framework)
- `src/presentation/` - Entry points (main.py)

## Running the Application

### Main Evaluation
```bash
python src/presentation/main.py
```

### Simple Test
```bash
python hello.py
```

## Environment Setup

1. Create a `.env` file with:
```
GEMINI_API_KEY=your_api_key_here
```

2. Install dependencies (no requirements.txt found - dependencies need to be documented):
- ragas
- google-generativeai
- python-dotenv
- Other dependencies as needed

## Key Implementation Details

- **Rate Limiting**: Gemini adapter is configured for 8 requests/minute (free tier limit)
- **LLM Model**: Uses `gemini-2.5-flash` by default
- **Data Format**: Evaluation data is stored in `data/evaluation_data.json`
- **Language**: Korean is used in documentation and comments

## Important Files

- `src/presentation/main.py` - Application entry point
- `config.py` - Environment configuration
- `data/evaluation_data.json` - Sample evaluation dataset
- `RAGAS_METRICS.md` - Detailed metric explanations in Korean

## Development Notes

- Python 3.11+ required
- No test files or linting configuration currently exists
- Uses dataclasses and type hints throughout
- Implements adapter pattern for external dependencies