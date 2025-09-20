# Librarian - LangGraph Backend Server

A LangGraph-powered backend web server for AI agent workflows.

## Setup

1. Install dependencies:
```bash
pip install -e .
```

2. Install LangGraph CLI:
```bash
pip install -U langgraph-cli
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

4. Start the LangGraph server:
```bash
langgraph dev
```

The server will be available at http://localhost:8123
