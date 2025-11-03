# Quick Start Guide

## Installation

### 1. Clone the repository
```bash
git clone <repository-url>
cd aiagent
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Set up environment (optional, for real LLMs)
```bash
cp .env.example .env
# Edit .env and add your API keys
```

### 4. Initialize database
```bash
python -c "from src.utils.database import setup_database; setup_database('data/water_facts.db', add_samples=True)"
```

## Basic Usage

### Option 1: Using Mock LLM (No API Key Required)

```python
from src.pipeline import create_chatbot

# Create chatbot with mock LLM
chatbot = create_chatbot()

# Ask a question
response = chatbot.answer_question("Is my tap water safe to drink?")

# Print answer
print(response['answer'])
```

### Option 2: Using OpenAI

```python
from src.pipeline import create_chatbot

# Set your API key in .env or pass directly
# OPENAI_API_KEY=sk-...

# Create chatbot with OpenAI
chatbot = create_chatbot(config_path="config/config.yaml")

# Update config to use OpenAI
chatbot.config.set('llm.provider', 'openai')
chatbot.config.set('llm.model', 'gpt-4')

# Ask questions
response = chatbot.answer_question("Why does my water taste like chlorine?")
print(response['answer'])
```

### Option 3: Using Anthropic Claude

```python
from src.pipeline import create_chatbot

# Set your API key in .env
# ANTHROPIC_API_KEY=sk-ant-...

# Create and configure chatbot
chatbot = create_chatbot(config_path="config/config.yaml")
chatbot.config.set('llm.provider', 'anthropic')
chatbot.config.set('llm.model', 'claude-3-sonnet-20240229')

# Ask questions
response = chatbot.answer_question("Is fluoride in water safe?")
print(response['answer'])
```

## Running Examples

```bash
# Run all example scenarios
python examples/example_usage.py
```

This will demonstrate:
1. Basic usage
2. Location-specific queries
3. Multiple questions with caching
4. Debug mode
5. Custom configuration
6. Batch processing

## Running Tests

```bash
# Install test dependencies
pip install pytest pytest-cov

# Run tests
pytest tests/

# Run with coverage
pytest tests/ --cov=src --cov-report=html
```

## Configuration

Edit `config/config.yaml` to customize:

```yaml
llm:
  provider: "mock"  # Change to "openai" or "anthropic"
  model: "gpt-4"
  temperature: 0.7

merger:
  response_style: "balanced"  # Options: "factual", "persuasive", "balanced"
  max_strategies_in_response: 3

pipeline:
  enable_caching: true
  cache_ttl: 3600
```

## Example Outputs

### Question: "Is my tap water safe to drink?"

**Response:**
```
Based on available information, tap water from municipal systems is generally
safe to drink. Public water systems are required to meet strict EPA standards
and are regularly tested for contaminants. Your local water utility publishes
annual water quality reports that detail test results.

EPA sets legal limits on over 90 contaminants in drinking water, ensuring tap
water is safe for consumption. Testing occurs daily, weekly, monthly, and
annually depending on the contaminant. Tap water is actually more strictly
regulated than bottled water.

If you have specific concerns, you can request additional testing or install
a home filter certified for your particular concern.
```

**Confidence:** 87%

**Processing Time:** 2.3s

### Question: "Why does my water taste like chlorine?"

**Response:**
```
The chlorine taste in your water is actually a sign of proper disinfection.
Chlorine is added to drinking water as a disinfectant to kill harmful bacteria
and viruses. The levels used are safe and EPA-regulated.

While the taste may be noticeable, the amount of chlorine in your water is
well below levels that could cause any health effects. Most public water
systems maintain chlorine levels between 0.2-4.0 mg/L, which is considered
safe by the EPA and CDC.

If the taste bothers you, you can:
• Use a pitcher filter with activated carbon
• Refrigerate water to reduce chlorine taste
• Let water sit uncovered for 30 minutes (chlorine dissipates)

The presence of chlorine indicates your water is being properly treated and
protected from harmful bacteria.
```

## Adding Your Own Water Data

### Method 1: Direct SQL Insert

```python
from src.utils.database import DatabaseManager

db = DatabaseManager('data/water_facts.db')
db.conn = db._connect()

cursor = db.conn.cursor()
cursor.execute("""
    INSERT INTO water_facts (category, topic, content, source, confidence, location)
    VALUES (?, ?, ?, ?, ?, ?)
""", (
    'quality',
    'testing',
    'Our city water is tested 50 times per day for safety.',
    'City Water Department',
    0.95,
    'YourCity'
))
db.conn.commit()
```

### Method 2: Bulk Import from CSV

```python
import csv
from src.utils.database import DatabaseManager

db = DatabaseManager('data/water_facts.db')
db.initialize_database()

with open('your_water_facts.csv', 'r') as f:
    reader = csv.DictReader(f)
    cursor = db.conn.cursor()

    for row in reader:
        cursor.execute("""
            INSERT INTO water_facts (category, topic, content, source, confidence, location)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            row['category'],
            row['topic'],
            row['content'],
            row['source'],
            float(row['confidence']),
            row['location']
        ))

    db.conn.commit()
```

## Troubleshooting

### Issue: "Database not found"
**Solution:** Run database initialization:
```bash
python -c "from src.utils.database import setup_database; setup_database('data/water_facts.db', add_samples=True)"
```

### Issue: "LLM API error"
**Solution:** Check your API key in `.env` file and verify internet connection.

### Issue: "No facts retrieved"
**Solution:** Ensure database has data. Try broader search terms.

## Next Steps

1. **Customize for your use case:** Add local water data to database
2. **Integrate with real LLM:** Set up OpenAI or Anthropic API
3. **Add web search:** Implement actual web search client
4. **Deploy:** Create web interface or API endpoint
5. **Monitor:** Add logging and analytics

## Support

- Read full documentation in `README.md`
- Check architecture in `ARCHITECTURE.md`
- Review code examples in `examples/`
- Run tests in `tests/`
