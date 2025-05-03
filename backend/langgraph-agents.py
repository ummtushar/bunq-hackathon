import getpass
import os
import glob
from dotenv import load_dotenv
from typing import Annotated, Dict, Any, List, Literal, TypedDict, Optional, Union
from langchain_community.document_loaders import WebBaseLoader
from langchain_core.tools import Tool, tool
from langchain_core.messages import HumanMessage
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.prebuilt import create_react_agent
from langgraph.types import Command
from typing_extensions import TypedDict
from langchain_tavily import TavilySearch
import json
from langchain_openai import ChatOpenAI


# Load environment variables
load_dotenv()

# Check for required API keys
def _set_if_undefined(var: str):
    if not os.getenv(var):
        os.environ[var] = getpass.getpass(f"Please provide your {var}")

_set_if_undefined("NVIDIA_API_KEY")
_set_if_undefined("TAVILY_API_KEY")
_set_if_undefined("OPENAI_API_KEY")

# Initialize the LLM
# model = ChatNVIDIA(model="meta/llama-3.3-70b-instruct", temperature=0)
model = ChatOpenAI(
    model="gpt-4.1-2025-04-14",
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2,
)

# Tools definition
web_search = TavilySearch(max_results=3)

@tool
def search_for_money_saving_alternatives(query: str) -> str:
    """
    Search the web for money-saving alternatives to products or services.
    
    Args:
        query: A search query related to finding alternatives or cheaper options.
        
    Returns:
        Relevant information from the web about money-saving alternatives.
    """
    search_results = web_search.invoke(query)
    
    # Format the results for better readability
    formatted_results = "## Web Search Results\n\n"
    for i, result in enumerate(search_results, 1):
        formatted_results += f"### Result {i}: {result.get('title', 'No Title')}\n"
        formatted_results += f"{result.get('content', 'No content available')}\n\n"
        formatted_results += f"Source: {result.get('url', 'No URL')}\n\n"
        formatted_results += "---\n\n"
    
    return formatted_results

# Create tool objects
tools = [
    search_for_money_saving_alternatives
]

# Define our team members
members = ["Classifier", "PatternAnalyzer", "Researcher", "Recommender"]
options = members + ["FINISH"]

# Define our supervisor prompt
# supervisor_prompt = """
# You are a financial assistant supervisor coordinating a team of specialized agents to help users save money.

# You work with these agents:
# 1. Classifier: Identifies brands, products, and categories in transaction data
# 2. PatternAnalyzer: Analyzes spending patterns and identifies opportunities to save
# 3. Researcher: Researches alternatives that could save the user money
# 4. Recommender: Creates the final recommendation based on all the information gathered

# Your job is to route the message to the appropriate agent and decide when the work is complete.
# Only route to FINISH when a complete recommendation has been generated.
# """

supervisor_prompt = """
You are a financial assistant supervisor coordinating a team of specialized agents to help users save money.

You work with these agents:
1. Classifier: Identifies brands, products, and categories in transaction data
2. PatternAnalyzer: Analyzes spending patterns and identifies opportunities to save
3. Researcher: Researches alternatives that could save the user money
4. Recommender: Creates the final recommendation based on all the information gathered

Your job is to route the message to the appropriate agent and decide when the work is complete.

IMPORTANT: Follow this exact workflow:
1. First, route to Classifier to analyze transaction data
2. Then, route to PatternAnalyzer to find spending patterns
3. Then, route to Researcher to research money-saving alternatives
4. Then, route to Recommender to generate final recommendations
5. Only after all 4 agents have been called, route to FINISH

Never route to FINISH until all four agents have processed the data and a complete recommendation has been generated.
"""

# Define our router type
class Router(TypedDict):
    """Worker to route to next. If no workers needed, route to FINISH."""
    next: str

# Define our state type
class AgentState(TypedDict, total=False):
    """State for the multi-agent system."""
    messages: List[Dict[str, Any]]
    transaction_data: Optional[List[Dict[str, Any]]]  
    classification_results: Optional[Dict[str, Any]]
    pattern_results: Optional[Dict[str, Any]]
    research_results: Optional[str]
    final_recommendation: Optional[str]
    next: Optional[str]

# Supervisor node
def supervisor_node(state: AgentState) -> Union[Command, Dict[str, Any]]:
    messages = [
        {"role": "system", "content": supervisor_prompt},
    ] + state["messages"]
    
    response = model.with_structured_output(Router).invoke(messages)
    goto = response["next"]
    
    if goto == "FINISH":
        return Command(goto=END, update={"next": "FINISH"})
    else:
        return Command(goto=goto, update={"next": goto})

# # Create agents
# classifier_agent = create_react_agent(
#     model, 
#     tools=[], 
#     prompt="You are a transaction classification agent. Analyze multiple transaction data and identify brands, product categories, whether they're subscriptions, and frequencies. Return your analysis as a JSON object that identifies spending patterns across all transactions."
# )

# pattern_agent = create_react_agent(
#     model, 
#     tools=[],
#     prompt="You are a spending pattern analysis agent. Analyze multiple transactions to identify patterns, repeated transactions, potential savings, and if recommendations are needed. Look for merchants that appear multiple times and calculate total spending per category. Return your analysis as a JSON object."
# )

# researcher_agent = create_react_agent(
#     model, 
#     tools=[search_for_money_saving_alternatives],
#     prompt="You are a research agent focused on finding money-saving alternatives. Research cheaper options and alternatives for products based on transaction data. Prioritize researching the categories with highest total spending. Use the search tools to find the best alternatives."
# )

# recommender_agent = create_react_agent(
#     model,
#     tools=[],
#     prompt="You are a recommendation agent. Create a final, friendly recommendation for the user based on all the information collected about their transactions and potential alternatives. Make it specific and actionable, focusing on the areas with highest potential savings."
# )


# Create agents
classifier_agent = create_react_agent(
    model, 
    tools=[], 
    prompt="""
    You are a transaction classification agent. You will receive a list of payment transactions. For each transaction, identify and return the following attributes:
    - brand: the business or service name (e.g. Starbucks, Amazon)
    - product_category: e.g. groceries, transport, phone top-up, etc.
    - is_subscription: true/false, based on whether this could be or is part of a subscription
    - frequency: e.g. one-time, weekly, monthly, unknown
    - transaction_type: one of [vendor, peer_to_peer, uncategorizable]
    
    IMPORTANT: Return ONLY valid JSON with no additional text. Format your response as:
    ```json
    {
      "transactions": [
        {
          "brand": "...",
          "product_category": "...",
          "is_subscription": true/false,
          "frequency": "...",
          "transaction_type": "..."
        },
        ...
      ]
    }
    ```
    Do not include any text before or after the JSON code block.
    """
)

pattern_agent = create_react_agent(
    model, 
    tools=[],
    prompt="""
    You are a spending pattern analysis agent. You receive a list of classified transactions (each includes brand, category, frequency).
    Your task is to:
    - Identify repeated spending patterns (e.g. same vendor, similar amount, recurring)
    - Highlight spending outliers or unusual behavior
    
    Return ONLY a structured JSON object with the following exact format:
    
    ```json
    {
      "patterns_detected": [
        {
          "description": "string",
          "frequency": "string",
          "importance": "high/medium/low"
        }
      ],
      "potential_savings": {
        "category1": number,
        "category2": number
      },
      "outliers": [
        {
          "description": "string",
          "amount": number
        }
      ]
    }
    ```
    Do not include any text outside of the JSON code block.
    """

)

researcher_agent = create_react_agent(
    model, 
    tools=[search_for_money_saving_alternatives],
    prompt="""
    You are a research agent that helps users save money.
    
    Given product names or transaction details, search for cheaper or better alternatives.
    Use the provided tools to find real-world options.
    
    Even for small or single transactions, you should still search for alternatives and money-saving tips.
    
    For fast food purchases (like nuggets), look for:
    1. Cheaper fast food alternatives or promotions
    2. Store-bought alternatives that are cheaper
    3. Meal planning tips to save money
    
    Return a concise summary of alternatives and money-saving strategies.
    
    Always perform at least one search, even for small purchases.
    """
)

recommender_agent = create_react_agent(
    model,
    tools=[],
    prompt="""
    You are a recommendation agent. Based on classified transactions, spending patterns, and researched alternatives, write a final recommendation message for the user.
    
    Your output should be short, friendly, and to the point.
    
    Begin with a 20 token MAXIMUM TLDR summary with actionable steps (e.g., "You could save money by preparing food at home instead of buying fast food"). THE RECOMMENDATION SHOULD FOCUS ON THE USER TO SPEND LESS MONEY BUT NOT SWITCH BANKS AND NEITHER WALLETS AND NEITHER CONSOLIDATE OTHER PLATFORMS, WALLETS, BANKS OR SERVICES. ONLY CHANGING THEIR SPENDING LIFESTYLE!
    
    
    Even if there's only one transaction or a small purchase, provide valuable money-saving recommendations.
    For fast food purchases, suggest:
    - Cooking at home
    - Buying in bulk
    - Using coupons/deals
    - Alternative restaurants with better value
    
    Always provide a recommendation, even if the potential savings are small.
    """
)

# Define agent nodes
def classifier_node(state: AgentState) -> Command:
    # Extract transaction data from the user's message if not already done
    if "transaction_data" not in state or not state.get("transaction_data"):
        try:
            user_message = next((m for m in state.get("messages", []) if m.get("role") == "user"), None)
            if user_message:
                # Try to parse as JSON first
                try:
                    transaction_data = json.loads(user_message["content"])
                except json.JSONDecodeError:
                    # If not JSON, just use the message content as-is
                    transaction_data = {"description": user_message["content"]}
                
                # Create a new state with transaction data
                if "transaction_data" not in state:
                    state["transaction_data"] = transaction_data
        except Exception as e:
            print(f"Error extracting transaction data: {e}")
    
    result = classifier_agent.invoke(state)
   
    classification_text = result["messages"][-1].content.strip()
    # Handle potential markdown code fences ```json ... ``` or ``` ... ```
    json_string = classification_text
    if classification_text.startswith("```json"):
        json_string = classification_text[7:-3].strip()
    elif classification_text.startswith("```"):
            json_string = classification_text[3:-3].strip()
    
    # Parse the potentially extracted JSON string
    classification_results = json.loads(json_string)
    
    return Command(
        update={
            "messages": state.get("messages", []) + [
                HumanMessage(content=result["messages"][-1].content, name="Classifier")
            ],
            "classification_results": classification_results
        },
        goto="supervisor",
    )

def pattern_analyzer_node(state: AgentState) -> Command:
    # Include transaction and classification in the input
    input_data = {
        "transactions": state.get("transaction_data", []),
        "classification": state.get("classification_results", {})
    }
    
    state_with_input = {
        "messages": state.get("messages", []) + [
            HumanMessage(content=f"Analyze these transaction patterns: {json.dumps(input_data)}")
        ]
    }
    
    result = pattern_agent.invoke(state_with_input)
    
    pattern_text = result["messages"][-1].content.strip()
    # Handle potential markdown code fences ```json ... ``` or ``` ... ```
    json_string = pattern_text
    if pattern_text.startswith("```json"):
        json_string = pattern_text[7:-3].strip()
    elif pattern_text.startswith("```"):
            json_string = pattern_text[3:-3].strip()
    
    # Parse the potentially extracted JSON string
    pattern_results = json.loads(json_string)
    
    return Command(
        update={
            "messages": state.get("messages", []) + [
                HumanMessage(content=result["messages"][-1].content, name="PatternAnalyzer")
            ],
            "pattern_results": pattern_results
        },
        goto="supervisor",
    )

def researcher_node(state: AgentState) -> Command:
    # Include all previous data in the input
    input_data = {
        "transactions": state.get("transaction_data", []),
        "classification": state.get("classification_results", {}),
        "pattern": state.get("pattern_results", {})
    }
    
    state_with_input = {
        "messages": state.get("messages", []) + [
            HumanMessage(content=f"Research alternatives for: {json.dumps(input_data)}")
        ]
    }
    
    result = researcher_agent.invoke(state_with_input)
    
    return Command(
        update={
            "messages": state.get("messages", []) + [
                HumanMessage(content=result["messages"][-1].content, name="Researcher")
            ],
            "research_results": result["messages"][-1].content
        },
        goto="supervisor",
    )

def recommender_node(state: AgentState) -> Command:
    # Include all previous data in the input
    input_data = {
        "transactions": state.get("transaction_data", []),
        "classification": state.get("classification_results", {}),
        "pattern": state.get("pattern_results", {}),
        "research": state.get("research_results", "")
    }
    
    prompt = f"""
    Based on the following information about multiple transactions, create a friendly, concise money-saving recommendation:
    
    Transactions: {json.dumps(state.get("transaction_data", []))}
    Classification: {json.dumps(state.get("classification_results", {}))}
    Pattern Analysis: {json.dumps(state.get("pattern_results", {}))}
    Research: {state.get("research_results", "")}
    
    Provide specific, actionable recommendations that will help the user save money. Focus on the categories with highest spending and most repetitive transactions.
    """
    
    state_with_input = {
        "messages": state.get("messages", []) + [
            HumanMessage(content=prompt)
        ]
    }
    
    result = recommender_agent.invoke(state_with_input)
    
    return Command(
        update={
            "messages": state.get("messages", []) + [
                HumanMessage(content=result["messages"][-1].content, name="Recommender")
            ],
            "final_recommendation": result["messages"][-1].content
        },
        goto="supervisor",
    )

# Build the graph
builder = StateGraph(AgentState)
builder.add_edge(START, "supervisor")
builder.add_node("supervisor", supervisor_node)
builder.add_node("Classifier", classifier_node)
builder.add_node("PatternAnalyzer", pattern_analyzer_node)
builder.add_node("Researcher", researcher_node)
builder.add_node("Recommender", recommender_node)
graph = builder.compile()


# Function to extract transaction data from Bunq format
def extract_transaction_data(bunq_json_data):
    """
    Extracts relevant transaction data from the Bunq payment JSON format.
    
    Args:
        bunq_json_data: The Bunq payment data in JSON format
        
    Returns:
        dict: Simplified transaction data for analysis
    """
    try:
        # Extract payment information from the Bunq JSON structure
        payment_data = bunq_json_data["Response"][0]["Payment"]
        
        # Create a simplified transaction object
        transaction = {
            "transaction_id": str(payment_data["id"]),
            "date": payment_data["created"],
            "amount": float(payment_data["amount"]["value"]),
            "currency": payment_data["amount"]["currency"],
            "description": payment_data["description"],
            "merchant": payment_data["counterparty_alias"]["display_name"],
            "category": model.invoke(f'Classify the transaction described as "{payment_data["description"]}" into ONE of the following categories: Entertainment, Groceries, Food and Drink, Car Expenses, Shopping, Personal Care, Household Expenses, General, Subscriptions, Cash, Finance, Family, Travel, Pets, Clothing, Gifts, Sports, Electronics, Investments, Culture, Healthcare, Savings, Income. Respond with ONLY the category name.').content,  
            "type": payment_data["type"],
            "sub_type": payment_data["sub_type"]
        }
        
        return transaction
    except Exception as e:
        print(f"Error extracting transaction data: {e}")
        return None

def load_multiple_json_files(file_paths):
    """
    Load multiple JSON files containing Bunq payment data.
    
    Args:
        file_paths: List of paths to JSON files
        
    Returns:
        List of transaction data dictionaries
    """
    transactions = []
    
    for file_path in file_paths:
        try:
            with open(file_path, 'r') as file:
                bunq_data = json.load(file)
                transaction = extract_transaction_data(bunq_data)
                if transaction:
                    transactions.append(transaction)
                    print(f"Successfully loaded transaction from {file_path}")
                else:
                    print(f"Failed to extract transaction data from {file_path}")
        except FileNotFoundError:
            print(f"Error: File {file_path} not found.")
        except json.JSONDecodeError:
            print(f"Error: File {file_path} is not valid JSON.")
    
    return transactions

def analyze_transactions_by_merchant(transactions):
    """
    Group transactions by merchant and calculate total spending
    
    Args:
        transactions: List of transaction dictionaries
        
    Returns:
        dict: Merchant-based analysis
    """
    merchant_analysis = {}
    
    for transaction in transactions:
        merchant = transaction.get("merchant")
        amount = transaction.get("amount", 0)
        
        if merchant not in merchant_analysis:
            merchant_analysis[merchant] = {
                "total_spent": 0,
                "transaction_count": 0,
                "transactions": []
            }
        
        merchant_analysis[merchant]["total_spent"] += amount
        merchant_analysis[merchant]["transaction_count"] += 1
        merchant_analysis[merchant]["transactions"].append(transaction)
    
    return merchant_analysis

def enrich_transactions_with_history(transactions):
    """
    Group transactions by merchant and add transaction history
    
    Args:
        transactions: List of transaction dictionaries
        
    Returns:
        list: List of transactions with historical data added
    """
    # Group by merchant
    merchant_transactions = {}
    for transaction in transactions:
        merchant = transaction.get("merchant")
        if merchant not in merchant_transactions:
            merchant_transactions[merchant] = []
        merchant_transactions[merchant].append(transaction)
    
    # Sort transactions by date for each merchant
    for merchant, txns in merchant_transactions.items():
        sorted_txns = sorted(txns, key=lambda t: t.get("date", ""), reverse=True)
        merchant_transactions[merchant] = sorted_txns
    
    # Enrich transactions with history
    enriched_transactions = []
    for transaction in transactions:
        merchant = transaction.get("merchant")
        merchant_history = merchant_transactions.get(merchant, [])
        
        # Create a copy of the transaction to avoid modifying the original
        enriched_transaction = transaction.copy()
        
        # Add previous transactions excluding the current one
        enriched_transaction["previous_transactions"] = [
            {"merchant": t.get("merchant"), "amount": t.get("amount"), "date": t.get("date")}
            for t in merchant_history
            if t.get("transaction_id") != transaction.get("transaction_id")
        ]
        
        enriched_transactions.append(enriched_transaction)
    
    return enriched_transactions

def analyze_multiple_bunq_transactions(json_file_pattern):
    """
    Analyzes multiple Bunq transactions from JSON files using the multi-agent system.
    
    Args:
        json_file_pattern: Glob pattern to match JSON files containing Bunq payment data
    
    Returns:
        str: A recommendation based on the transaction analysis
    """
    print(f"Looking for Bunq payment data matching {json_file_pattern}...")
    
    # Use glob to find all files matching the pattern
    file_paths = glob.glob(json_file_pattern)
    
    if not file_paths:
        print(f"No files found matching {json_file_pattern}")
        return None
    
    print(f"Found {len(file_paths)} files to analyze.")
    
    # Load data from all JSON files
    transactions = load_multiple_json_files(file_paths)
    
    if not transactions:
        print("Failed to extract any valid transaction data.")
        return None
    
    print(f"Successfully loaded {len(transactions)} transactions.")
    
    # Enrich transactions with historical data
    enriched_transactions = enrich_transactions_with_history(transactions)
    
    # Initial state with transaction data
    input_data: AgentState = {
        "messages": [{"role": "user", "content": json.dumps(enriched_transactions)}],
        "transaction_data": enriched_transactions,
        "classification_results": None,
        "pattern_results": None,
        "research_results": None,
        "final_recommendation": None,
        "next": None
    }
    
    # Run the multi-agent system
    try:
        print("Running analysis through multi-agent system...")
        print("This may take a few minutes depending on the complexity...")
        
        responses = []
        # Stream the results to see progress
        for s in graph.stream(input_data, subgraphs=True):
            if isinstance(s, tuple) and len(s) > 1:
                for key, value in s[1].items():
                    # Add a check to ensure value is not None before trying to access keys
                    if value is None:
                        continue
                        
                    if key in members and isinstance(value, dict) and "messages" in value:
                        messages = value.get("messages", [])
                        if messages and len(messages) > 0:
                            message = messages[-1]
                            response_text = f"{key}: {message.content}"
                            print(response_text)
                            responses.append(response_text)
                    
                    elif key == "supervisor" and isinstance(value, dict) and "next" in value:
                        next_node = value["next"]
                        if next_node != "__end__":
                            print(f"Calling {next_node}")
        
        # Get the final state
        final_state = graph.invoke(input_data)
        
        print("\n" + "="*50)
        print("ANALYSIS COMPLETE")
        print("="*50)
        
        if final_state and isinstance(final_state, dict):
            if "classification_results" in final_state and final_state["classification_results"]:
                print(f"\nCLASSIFICATION RESULTS:")
                for key, value in final_state["classification_results"].items():
                    print(f"  {key}: {value}")
            
            if "pattern_results" in final_state and final_state["pattern_results"]:
                print(f"\nPATTERN ANALYSIS RESULTS:")
                for key, value in final_state["pattern_results"].items():
                    print(f"  {key}: {value}")
            
            if "final_recommendation" in final_state and final_state["final_recommendation"]:
                print(f"\nFINAL RECOMMENDATION:")
                print(final_state["final_recommendation"])
            
            # Save the results to a file
            merchant_analysis = analyze_transactions_by_merchant(transactions)
            
            results = {
                "transactions": enriched_transactions,
                "merchant_analysis": merchant_analysis,
                "classification": final_state.get("classification_results"),
                "pattern_analysis": final_state.get("pattern_results"),
                "research": final_state.get("research_results"),
                "recommendation": final_state.get("final_recommendation")
            }
            
            output_file = "bunq_multiple_analysis_results.json" #OUTPUT
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2)
            
            print(f"\nResults saved to {output_file}")
            
            return final_state.get("final_recommendation") 
        else:
            print("No valid final state was returned from the graph.")
            return None
    except Exception as e:
        import traceback
        print(f"Error during analysis: {str(e)}")
        traceback.print_exc()
        return None

# Main execution
if __name__ == "__main__":
    # Use glob pattern to match multiple JSON files
    analyze_multiple_bunq_transactions("data/*.json") #INPUT
    # analyze_multiple_bunq_transactions("data/list_payment.json")