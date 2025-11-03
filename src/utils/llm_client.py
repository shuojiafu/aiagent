"""
LLM Client Utilities
Provides unified interface for various LLM providers
"""

from typing import Dict, Any, Optional
import os


class BaseLLMClient:
    """Base class for LLM clients"""

    def generate(self, prompt: str, temperature: float = 0.7, max_tokens: int = 1000) -> str:
        """Generate text from prompt"""
        raise NotImplementedError


class OpenAIClient(BaseLLMClient):
    """OpenAI API client"""

    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4"):
        """
        Initialize OpenAI client

        Args:
            api_key: OpenAI API key (or set OPENAI_API_KEY env var)
            model: Model name to use
        """
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        self.model = model

        if not self.api_key:
            raise ValueError("OpenAI API key required")

        try:
            import openai
            self.client = openai.OpenAI(api_key=self.api_key)
        except ImportError:
            raise ImportError("openai package required. Install with: pip install openai")

    def generate(self, prompt: str, temperature: float = 0.7, max_tokens: int = 1000) -> str:
        """Generate text using OpenAI API"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content
        except Exception as e:
            raise Exception(f"OpenAI API error: {str(e)}")


class AnthropicClient(BaseLLMClient):
    """Anthropic Claude API client"""

    def __init__(self, api_key: Optional[str] = None, model: str = "claude-3-sonnet-20240229"):
        """
        Initialize Anthropic client

        Args:
            api_key: Anthropic API key (or set ANTHROPIC_API_KEY env var)
            model: Model name to use
        """
        self.api_key = api_key or os.getenv('ANTHROPIC_API_KEY')
        self.model = model

        if not self.api_key:
            raise ValueError("Anthropic API key required")

        try:
            import anthropic
            self.client = anthropic.Anthropic(api_key=self.api_key)
        except ImportError:
            raise ImportError("anthropic package required. Install with: pip install anthropic")

    def generate(self, prompt: str, temperature: float = 0.7, max_tokens: int = 1000) -> str:
        """Generate text using Anthropic API"""
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            raise Exception(f"Anthropic API error: {str(e)}")


class MockLLMClient(BaseLLMClient):
    """Mock LLM client for testing"""

    def __init__(self, model: str = "mock"):
        self.model = model

    def generate(self, prompt: str, temperature: float = 0.7, max_tokens: int = 1000) -> str:
        """Generate mock response"""
        if "strategy" in prompt.lower():
            return """Strategy 1: Evidence-Based Trust Building
Key Message: Your tap water meets rigorous safety standards and is regularly tested.
Supporting Evidence: EPA regulations require testing for over 90 contaminants, and local utilities publish results regularly.
Delivery Approach: Present factual testing data with reassuring context about regulatory oversight.
Trust-Building Elements: Cite specific EPA standards, mention frequency of testing, reference transparency of results

Strategy 2: Transparency and Accessibility
Key Message: Water quality information is publicly available and local utilities are accountable.
Supporting Evidence: Annual water quality reports (Consumer Confidence Reports) are sent to all customers and posted online.
Delivery Approach: Direct users to their local utility's website and explain how to interpret quality reports.
Trust-Building Elements: Emphasize transparency, accessibility of information, accountability

Strategy 3: Risk Perspective
Key Message: Tap water is one of the most regulated and tested consumer products.
Supporting Evidence: More stringent standards than bottled water, continuous monitoring vs. periodic testing.
Delivery Approach: Compare tap water safety to other beverages and provide perspective on risk.
Trust-Building Elements: Comparative safety data, regulatory rigor, expert consensus"""
        else:
            return """Based on the available information, tap water from municipal systems is generally safe to drink. Public water systems are required to meet strict EPA standards and are regularly tested for contaminants. Your local water utility publishes annual water quality reports that detail test results. If you have specific concerns, you can request additional testing or install a home filter certified for your particular concern."""


def create_llm_client(provider: str = "mock", **kwargs) -> BaseLLMClient:
    """
    Factory function to create LLM client

    Args:
        provider: LLM provider name ('openai', 'anthropic', 'mock')
        **kwargs: Additional arguments for client initialization

    Returns:
        Initialized LLM client
    """
    if provider.lower() == "openai":
        return OpenAIClient(**kwargs)
    elif provider.lower() == "anthropic":
        return AnthropicClient(**kwargs)
    elif provider.lower() == "mock":
        return MockLLMClient(**kwargs)
    else:
        raise ValueError(f"Unknown provider: {provider}. Available: openai, anthropic, mock")
