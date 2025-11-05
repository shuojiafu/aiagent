# Zero-shot Persuasive Chatbots for Household Water Trust

This framework implements a Zero-shot Persuasive Chatbots system designed to build trust in localized household water and answer questions about household water quality and safety.

## Architecture Overview

The system consists of two main modules:

### 1. Strategy Maintenance Module (SMM)
Generates and maintains persuasive strategies for building trust in household water.

**Three Stages:**
- **LLM Generation**: Generates persuasive strategies using large language models
- **Strategy Extraction**: Extracts and structures strategies from LLM outputs
- **Fact-Check & IR**: Validates strategies with information retrieval and fact-checking

### 2. Question Handling Module (QHM)
Handles user questions about household water using retrieval-augmented generation.

**Two Stages:**
- **SQL-based RAG**: Retrieves facts from localized structured database
- **Curated Web Search**: Supplements with verified web sources

### Pipeline Flow

```
User Question
      |
      v
[Question Handling Module]
      |
      +---> SQL Database RAG
      |
      +---> Curated Web Search
      |
      v
Retrieved Facts & Context
      |
      v
[Strategy Maintenance Module]
      |
      +---> LLM Generation
      |
      +---> Strategy Extraction
      |
      +---> Fact-Check & IR
      |
      v
Persuasive Strategies
      |
      v
[Response Merger]
      |
      v
Final Answer (Fact-based + Persuasive)
```

## Project Structure

```
aiagent/
├── src/
│   ├── modules/
│   │   ├── smm/               # Strategy Maintenance Module
│   │   │   ├── llm_generation.py
│   │   │   ├── strategy_extraction.py
│   │   │   └── fact_check_ir.py
│   │   ├── qhm/               # Question Handling Module
│   │   │   ├── sql_rag.py
│   │   │   └── web_search.py
│   │   └── merger/
│   │       └── response_merger.py
│   ├── pipeline.py            # Main pipeline orchestrator
│   ├── config.py              # Configuration management
│   └── utils/
│       ├── database.py
│       └── llm_client.py
├── data/
│   ├── water_facts.db         # Structured water data
│   └── strategies/            # Cached strategies
├── config/
│   └── config.yaml            # System configuration
├── examples/
│   └── example_usage.py
├── tests/
│   └── test_pipeline.py
├── requirements.txt
└── README.md
```

### Pipeline structure
```
User Question → answer_question()
     │
     ├─ Check Cache → return if exists
     │
     ├─ QHM (Question Handling Module)
     │     ├─ SQL Fact Retrieval (local DB)
     │     └─ Web Retrieval (optional)
     │
     ├─ SMM (Strategy Maintenance Module)
     │     ├─ Generate strategies using LLM
     │     ├─ Extract useful strategies
     │     └─ Fact-check & rank strategies
     │
     ├─ Response Merger → Final Answer
     │
     ├─ Cache result
     └─ Return answer as JSON-like dictionary
```


## Installation

```bash
pip install -r requirements.txt
```

## Quick Start

```python
from src.pipeline import WaterTrustChatbot

# Initialize chatbot
chatbot = WaterTrustChatbot(config_path="config/config.yaml")

# Ask a question
response = chatbot.answer_question(
    "Is my tap water safe to drink?"
)

print(response)
```

## Configuration

Edit `config/config.yaml` to customize:
- Azure OpenAI settings (endpoint, deployment, API version, etc.)
- Database connection
- Web search parameters
- Strategy generation settings

To use Azure OpenAI, set the following environment variables:
```bash
export AZURE_OPENAI_API_KEY=your_api_key
export AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
export AZURE_OPENAI_DEPLOYMENT_NAME=your-deployment-name
```

Then update `config/config.yaml`:
```yaml
llm:
  provider: "azure"  # Change from "mock" to "azure"
```

## Use Case

This system is specifically designed for:
- Building public trust in household water systems
- Answering questions about water quality, safety, and treatment
- Providing fact-based, persuasive responses backed by local data
- Addressing concerns about contaminants, taste, odor, and health effects
