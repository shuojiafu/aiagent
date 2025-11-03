"""
Example Usage of Water Trust Chatbot
Demonstrates how to use the pipeline
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.pipeline import create_chatbot


def example_basic_usage():
    """Example: Basic usage with mock LLM"""
    print("="*70)
    print("Example 1: Basic Usage")
    print("="*70)

    # Create chatbot with default config (uses mock LLM)
    chatbot = create_chatbot()

    # Ask a question
    question = "Is my tap water safe to drink?"
    response = chatbot.answer_question(question)

    # Print response
    print("\n📝 Question:", question)
    print("\n💬 Answer:")
    print(response['answer'])
    print("\n📊 Confidence:", f"{response['confidence']:.2%}")
    print(f"⏱️  Processing Time: {response['processing_time']:.2f}s")


def example_with_location():
    """Example: Using location-specific data"""
    print("\n\n" + "="*70)
    print("Example 2: Location-Specific Query")
    print("="*70)

    chatbot = create_chatbot()

    question = "What contaminants are tested in my water?"
    location = "Portland"

    response = chatbot.answer_question(question, location=location)

    print("\n📝 Question:", question)
    print("📍 Location:", location)
    print("\n💬 Answer:")
    print(response['answer'])
    print("\n📚 Sources:")
    for i, source in enumerate(response['sources'][:3], 1):
        print(f"  {i}. {source['source']} (confidence: {source['confidence']:.2%})")


def example_multiple_questions():
    """Example: Multiple questions in one session"""
    print("\n\n" + "="*70)
    print("Example 3: Multiple Questions (with caching)")
    print("="*70)

    chatbot = create_chatbot()

    questions = [
        "Why does my water taste like chlorine?",
        "Is fluoride in water safe?",
        "How often is tap water tested?",
        "Is fluoride in water safe?"  # Duplicate to test caching
    ]

    for i, question in enumerate(questions, 1):
        print(f"\n--- Question {i} ---")
        print(f"Q: {question}")

        response = chatbot.answer_question(question)

        print(f"A: {response['answer'][:150]}...")
        print(f"⏱️  Time: {response['processing_time']:.2f}s")


def example_debug_mode():
    """Example: Using debug mode for detailed information"""
    print("\n\n" + "="*70)
    print("Example 4: Debug Mode")
    print("="*70)

    # Create chatbot in debug mode
    chatbot = create_chatbot(debug=True)

    question = "What are the EPA standards for drinking water?"
    response = chatbot.answer_question(question)

    print("\n📝 Question:", question)
    print("\n💬 Answer:")
    print(response['answer'])

    # Debug information
    print("\n🔍 Debug Information:")
    print(f"  - Facts used: {len(response['debug']['qhm_facts_details'])}")
    print(f"  - Strategies used: {len(response['debug']['smm_strategies_details'])}")

    print("\n  Strategies Details:")
    for i, strategy in enumerate(response['debug']['smm_strategies_details'], 1):
        print(f"    {i}. Type: {strategy.get('strategy_type', 'N/A')}")
        print(f"       Validation: {strategy.get('validation_score', 0):.2%}")


def example_custom_config():
    """Example: Using custom configuration"""
    print("\n\n" + "="*70)
    print("Example 5: Custom Configuration")
    print("="*70)

    # Create chatbot with custom config file
    config_path = "config/config.yaml"
    chatbot = create_chatbot(config_path=config_path)

    # Show stats
    stats = chatbot.get_stats()
    print("\n⚙️  Chatbot Configuration:")
    print(f"  - LLM Provider: {stats['config']['llm']['provider']}")
    print(f"  - Response Style: {stats['config']['merger']['response_style']}")
    print(f"  - Caching: {stats['config']['pipeline']['enable_caching']}")

    # Ask question
    question = "Can lead get into my drinking water?"
    response = chatbot.answer_question(question)

    print("\n📝 Question:", question)
    print("\n💬 Answer:")
    print(response['answer'])


def example_batch_processing():
    """Example: Batch processing multiple questions"""
    print("\n\n" + "="*70)
    print("Example 6: Batch Processing")
    print("="*70)

    chatbot = create_chatbot()

    questions = [
        "Is tap water better than bottled water?",
        "What is chlorine doing in my water?",
        "How do I know if my water is contaminated?"
    ]

    results = []
    for question in questions:
        response = chatbot.answer_question(question)
        results.append({
            'question': question,
            'answer': response['answer'],
            'confidence': response['confidence']
        })

    # Display summary
    print("\n📊 Batch Processing Results:")
    print("-" * 70)
    for i, result in enumerate(results, 1):
        print(f"\n{i}. {result['question']}")
        print(f"   Confidence: {result['confidence']:.2%}")
        print(f"   Answer: {result['answer'][:100]}...")

    print(f"\n✓ Processed {len(results)} questions")


def main():
    """Run all examples"""
    print("\n" + "🚰 " * 20)
    print(" " * 15 + "WATER TRUST CHATBOT EXAMPLES")
    print("🚰 " * 20 + "\n")

    # Run examples
    example_basic_usage()
    example_with_location()
    example_multiple_questions()
    example_debug_mode()
    example_custom_config()
    example_batch_processing()

    print("\n\n" + "="*70)
    print("All examples completed!")
    print("="*70)


if __name__ == "__main__":
    main()
