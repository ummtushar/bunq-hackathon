# bunq Hackathon 6.0
I built an end to end multi-agent AI implementation for automated notifactions on your phone that give you advice to save money based on your last week's transactions.

## Check out the submission at Devpost
https://devpost.com/software/bunqsplit-mila

# Financial Transaction Analysis System

A multi-agent AI system that analyzes bank transaction data (specifically Bunq format) and provides personalized money-saving recommendations using LangGraph, OpenAI/NVIDIA models, and web search capabilities.

## 🎯 Overview

This system processes multiple bank transaction JSON files and employs a coordinated team of AI agents to:
- **Classify** transactions by brand, category, and subscription type
- **Analyze** spending patterns and identify savings opportunities
- **Research** cheaper alternatives and money-saving strategies
- **Recommend** specific, actionable steps to reduce expenses

## 🏗️ Architecture

The system uses a **supervisor-worker pattern** with specialized agents:

<img width="607" alt="image" src="https://github.com/user-attachments/assets/7ba49f40-d58e-44b9-87d6-95dadba4dc41" />

### Agent Responsibilities

1. **Supervisor**: Orchestrates the workflow and routes tasks to appropriate agents
2. **Classifier**: Identifies brands, product categories, subscription status, and transaction frequency
3. **PatternAnalyzer**: Detects spending patterns, outliers, and potential savings opportunities
4. **Researcher**: Uses web search to find cheaper alternatives and money-saving strategies
5. **Recommender**: Generates final, actionable recommendations based on all collected data

## 🚀 Setup and Installation

### Prerequisites

- Python 3.8+
- API keys for:
  - NVIDIA AI Endpoints
  - Tavily Search
  - OpenAI

### Installation

1. **Clone or download the script**

2. **Install dependencies**:
```bash
pip install python-dotenv langchain-community langchain-core langchain-nvidia-ai-endpoints langgraph langchain-tavily langchain-openai typing-extensions
```
3. Set up environment variables: Create a ```.env``` file in the project directory:
```
NVIDIA_API_KEY=your_nvidia_api_key_here
TAVILY_API_KEY=your_tavily_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
```

## 📁 Input Data Format
Bunq Transaction JSON Structure
The system expects JSON files in Bunq bank format:

```
{
  "Response": [
    {
      "Payment": {
        "id": 12345,
        "created": "2024-01-15 10:30:00",
        "amount": {
          "value": "-15.50",
          "currency": "EUR"
        },
        "description": "McDonald's Payment",
        "counterparty_alias": {
          "display_name": "McDonald's"
        },
        "type": "BUNQ",
        "sub_type": "PAYMENT"
      }
    }
  ]
}
```
## Directory Structure
Place your transaction JSON files in a data/ directory:
```
project/
├── script.py
├── .env
├── data/
│   ├── transaction_1.json
│   ├── transaction_2.json
│   └── transaction_3.json
└── README.md
```

## 🎮 Usage
Basic Usage
```
python script.py
```
The script will automatically:

- Look for JSON files matching data/*.json

- Process all found transaction files

- Run the multi-agent analysis

- Generate recommendations

- Save results to bunq_multiple_analysis_results.json

## Custom File Pattern

Modify the main execution section to use a different file pattern:
```
if __name__ == "__main__":
    # Custom pattern examples:
    analyze_multiple_bunq_transactions("transactions/*.json")
    analyze_multiple_bunq_transactions("data/january_*.json")
    analyze_multiple_bunq_transactions("specific_file.json")
```

## 📊 Output
Console Output
The system provides real-time progress updates:

```
Looking for Bunq payment data matching data/*.json...
Found 5 files to analyze.
Successfully loaded 5 transactions.
Running analysis through multi-agent system...

Calling Classifier
Classifier: [JSON classification results]

Calling PatternAnalyzer
PatternAnalyzer: [JSON pattern analysis]

Calling Researcher
Researcher: [Research findings on alternatives]

Calling Recommender
Recommender: [Final recommendations]

==================================================
ANALYSIS COMPLETE
==================================================

FINAL RECOMMENDATION:
TL;DR: Save money by cooking at home instead of frequent fast food purchases.

Based on your transaction analysis, I recommend...
```

JSON Output File
Results are saved to bunq_multiple_analysis_results.json:
```
{
  "transactions": [...],
  "merchant_analysis": {
    "McDonald's": {
      "total_spent": 45.50,
      "transaction_count": 3,
      "transactions": [...]
    }
  },
  "classification": {...},
  "pattern_analysis": {...},
  "research": "...",
  "recommendation": "..."
}
```

## ⚙️ Configuration
Model Selection
Switch between LLM providers by uncommenting the desired model:
```
# NVIDIA model
# model = ChatNVIDIA(model="meta/llama-3.3-70b-instruct", temperature=0)

# OpenAI model (default)
model = ChatOpenAI(
    model="gpt-4.1-2025-04-14",
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2,
)
```

Search Configuration
Modify search parameters:

```
web_search = TavilySearch(max_results=3)  # Adjust max_results as needed
```

Agent Prompts
Customize agent behavior by modifying their prompts in the agent creation section.

## 🔧 Key Functions
- extract_transaction_data(bunq_json_data)
Converts Bunq JSON format to simplified transaction format.

- load_multiple_json_files(file_paths)
Loads and processes multiple transaction JSON files.

- analyze_transactions_by_merchant(transactions)
Groups transactions by merchant and calculates spending totals.

- enrich_transactions_with_history(transactions)
Adds transaction history context for each merchant.

- analyze_multiple_bunq_transactions(json_file_pattern)
Main analysis function that orchestrates the entire process.


## 🛠️ Troubleshooting
Common Issues
- Missing API Keys: Ensure all required API keys are set in .env or environment variables

- No Files Found: Check that JSON files exist in the specified directory and match the glob pattern

- JSON Parse Errors: Verify that transaction files are valid JSON in Bunq format

- Network Issues: Ensure internet connectivity for web search functionality

Debug Mode
Add print statements or logging to track agent execution:
```
print(f"Processing {len(transactions)} transactions...")
```

## 📋 Dependencies
- python-dotenv: Environment variable management

- langchain-community: Document loaders and utilities

- langchain-core: Core LangChain functionality

- langchain-nvidia-ai-endpoints: NVIDIA AI model integration

- langgraph: Multi-agent workflow orchestration

- langchain-tavily: Web search capabilities

- langchain-openai: OpenAI model integration

- typing-extensions: Enhanced type hints

## 🔒 Security Notes
- Store API keys securely in environment variables or .env files

- Never commit API keys to version control

- Consider using API key rotation for production use

- Review transaction data privacy before processing

## 🚀 Future Enhancements
- Support for additional bank formats (beyond Bunq)

- Integration with multiple search providers

- Advanced visualization capabilities

- Real-time transaction monitoring

- Machine learning-based pattern recognition

- Export capabilities (PDF, Excel reports)

- Web interface for easier interaction

