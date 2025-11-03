# Architecture Documentation

## System Overview

The Water Trust Chatbot implements a Zero-shot Persuasive framework with two main modules that work in tandem to generate fact-based, persuasive responses about household water safety.

## Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER QUESTION                                │
│                    "Is my tap water safe?"                          │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   QUESTION HANDLING MODULE (QHM)                    │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  Stage 1: SQL-based RAG                                       │  │
│  │  • Query structured water database                           │  │
│  │  • Keyword & topic-based search                              │  │
│  │  • Retrieve relevant facts with confidence scores            │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                             │                                        │
│  ┌──────────────────────────▼───────────────────────────────────┐  │
│  │  Stage 2: Curated Web Search                                  │  │
│  │  • Search trusted domains (EPA, CDC, WHO, etc.)              │  │
│  │  • Filter & validate results                                 │  │
│  │  • Supplement database facts                                 │  │
│  └──────────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
                   ┌─────────────────┐
                   │  Retrieved Facts │
                   └────────┬─────────┘
                            │
         ┌──────────────────┴──────────────────┐
         ▼                                      ▼
┌────────────────────┐              ┌───────────────────────────┐
│  QHM Facts         │              │  Original Question        │
│  • Database facts  │              │  • User query             │
│  • Web sources     │──────────────▶  • Context                │
│  • Confidence      │              │  • Location (optional)    │
└────────────────────┘              └────────────┬──────────────┘
                                                 │
                                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│               STRATEGY MAINTENANCE MODULE (SMM)                     │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  Stage 1: LLM Generation                                      │  │
│  │  • Send question + facts to LLM                              │  │
│  │  • Generate persuasive strategies                            │  │
│  │  • Focus on trust-building approaches                        │  │
│  └────────────────────────────┬─────────────────────────────────┘  │
│                               │                                     │
│  ┌────────────────────────────▼─────────────────────────────────┐  │
│  │  Stage 2: Strategy Extraction                                 │  │
│  │  • Parse LLM output                                           │  │
│  │  • Structure strategies (type, message, evidence, etc.)      │  │
│  │  • Validate completeness                                     │  │
│  └────────────────────────────┬─────────────────────────────────┘  │
│                               │                                     │
│  ┌────────────────────────────▼─────────────────────────────────┐  │
│  │  Stage 3: Fact-Check & IR                                     │  │
│  │  • Verify strategy claims against facts                      │  │
│  │  • Retrieve additional supporting information               │  │
│  │  • Rank strategies by evidence strength                     │  │
│  │  • Filter out unverified strategies                         │  │
│  └──────────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
                   ┌─────────────────────┐
                   │ Validated Strategies │
                   └──────────┬───────────┘
                              │
         ┌────────────────────┴────────────────────┐
         ▼                                         ▼
┌────────────────────┐                   ┌──────────────────┐
│  QHM Facts         │                   │  SMM Strategies  │
│  • Original facts  │                   │  • Validated     │
│  • Web sources     │────────┐          │  • Ranked        │
└────────────────────┘        │          │  • Evidence-based│
                              │          └──────────────────┘
                              │                    │
                              └─────────┬──────────┘
                                        ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      RESPONSE MERGER                                │
│                                                                      │
│  • Select best strategies (top 3)                                   │
│  • Integrate facts and strategies                                   │
│  • Generate cohesive, natural response via LLM                     │
│  • Calculate confidence score                                       │
│  • Compile sources & metadata                                       │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         FINAL ANSWER                                │
│                                                                      │
│  {                                                                   │
│    "answer": "Your tap water is safe to drink...",                 │
│    "confidence": 0.87,                                              │
│    "strategies_used": [...],                                        │
│    "facts_referenced": [...],                                       │
│    "sources": [...],                                                │
│    "processing_time": 2.34                                          │
│  }                                                                   │
└─────────────────────────────────────────────────────────────────────┘
```

## Module Details

### 1. Question Handling Module (QHM)

**Purpose:** Retrieve relevant, factual information about household water

**Components:**

#### 1.1 SQL-based RAG (`sql_rag.py`)
- **Retrieval Strategies:**
  - Keyword search
  - Topic-based search
  - Related facts expansion
- **Database Schema:**
  ```
  water_facts:
    - id: INTEGER PRIMARY KEY
    - category: TEXT (safety, quality, treatment, etc.)
    - topic: TEXT (lead, chlorine, testing, etc.)
    - content: TEXT (fact content)
    - source: TEXT (EPA, CDC, etc.)
    - confidence: REAL (0-1)
    - location: TEXT (optional geolocation)
    - last_updated: TIMESTAMP
  ```

#### 1.2 Curated Web Search (`web_search.py`)
- **Trusted Domains:**
  - Government: EPA, CDC, WHO, USGS
  - Professional: AWWA, WaterRF
  - NGO: NRDC, EWG
- **Validation:**
  - Domain verification
  - Content relevance checking
  - Confidence scoring by source

### 2. Strategy Maintenance Module (SMM)

**Purpose:** Generate and validate persuasive communication strategies

**Components:**

#### 2.1 LLM Generation (`llm_generation.py`)
- **Input:** Question + Retrieved Facts
- **Output:** Persuasive strategies
- **Strategy Structure:**
  ```
  {
    "strategy_type": "Authority Appeal / Evidence-Based / etc.",
    "key_message": "Main point to communicate",
    "supporting_evidence": "How facts support message",
    "delivery_approach": "How to present persuasively",
    "trust_elements": ["specific trust-building elements"]
  }
  ```

#### 2.2 Strategy Extraction (`strategy_extraction.py`)
- **Methods:**
  - JSON parsing
  - Pattern-based extraction
  - Section-based fallback
- **Validation:**
  - Required field checking
  - Content quality filtering
  - Deduplication

#### 2.3 Fact-Check & IR (`fact_check_ir.py`)
- **Validation Process:**
  1. Extract claims from strategies
  2. Match against retrieved facts
  3. Query database for verification
  4. Calculate confidence scores
- **Enhancement:**
  - Retrieve additional supporting information
  - Add context from multiple sources
- **Ranking:**
  - Evidence strength
  - Fact support
  - Source credibility

### 3. Response Merger

**Purpose:** Combine facts and strategies into coherent answer

**Process:**
1. **Strategy Selection:** Choose top 3 strategies by evidence
2. **Integration:** Merge facts and strategies naturally
3. **Generation:** Use LLM to create final response
4. **Metadata:** Add confidence, sources, and timing

## Data Flow

```
User Question
    ↓
[Parse & Understand]
    ↓
┌───────────────────────┐
│ QHM Parallel Retrieval│
│  • SQL Database       │
│  • Web Search         │
└───────────┬───────────┘
            ↓
    [Merge & Rank Facts]
            ↓
    Facts → SMM Pipeline
            ↓
┌───────────────────────┐
│ SMM Sequential Stages │
│  1. Generate          │
│  2. Extract           │
│  3. Validate          │
└───────────┬───────────┘
            ↓
  Validated Strategies
            ↓
┌───────────────────────┐
│ Response Merger       │
│  • Select strategies  │
│  • Integrate facts    │
│  • Generate answer    │
└───────────┬───────────┘
            ↓
      Final Answer
```

## Configuration

The system is highly configurable through `config/config.yaml`:

- **LLM Settings:** Provider, model, temperature
- **Database:** Path, retrieval limits
- **Web Search:** Enable/disable, trusted domains
- **SMM:** Strategy limits, validation thresholds
- **Merger:** Response style, strategy selection
- **Pipeline:** Caching, timeouts

## Extension Points

### Adding New LLM Providers
1. Inherit from `BaseLLMClient` in `utils/llm_client.py`
2. Implement `generate()` method
3. Add to `create_llm_client()` factory

### Adding New Data Sources
1. Create retriever class with `retrieve_facts()` method
2. Add to QHM pipeline in `pipeline.py`
3. Update fact merging logic

### Custom Strategy Types
1. Define new strategy types in SMM generation prompt
2. Update extraction patterns in `strategy_extraction.py`
3. Add specific validation rules if needed

### Custom Response Styles
1. Add style to config options
2. Implement style instructions in `response_merger.py`
3. Adjust strategy selection weights

## Performance Considerations

- **Caching:** Responses cached with configurable TTL
- **Parallel Retrieval:** QHM searches run concurrently
- **Database Indexing:** Categories, topics, and locations indexed
- **Response Streaming:** Can be added for long responses
- **Batch Processing:** Support for multiple questions

## Security & Privacy

- **API Keys:** Stored in environment variables
- **Database:** Local SQLite, no external data sharing
- **Web Search:** Only curated, trusted domains
- **Validation:** All strategies fact-checked before use
- **Logging:** Configurable, no PII stored by default
