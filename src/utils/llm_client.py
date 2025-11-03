"""
LLM Client Utilities
Provides interface for Azure OpenAI API
"""

from typing import Dict, Any, Optional
import os


class BaseLLMClient:
    """Base class for LLM clients"""

    def generate(self, prompt: str, temperature: float = 0.7, max_tokens: int = 1000) -> str:
        """Generate text from prompt"""
        raise NotImplementedError


class AzureOpenAIClient(BaseLLMClient):
    """Azure OpenAI API client"""

    def __init__(self,
                 api_key: Optional[str] = None,
                 endpoint: Optional[str] = None,
                 deployment_name: Optional[str] = None,
                 api_version: str = "2024-02-15-preview"):
        """
        Initialize Azure OpenAI client

        Args:
            api_key: Azure OpenAI API key (or set AZURE_OPENAI_API_KEY env var)
            endpoint: Azure OpenAI endpoint (or set AZURE_OPENAI_ENDPOINT env var)
            deployment_name: Deployment name (or set AZURE_OPENAI_DEPLOYMENT_NAME env var)
            api_version: API version to use
        """
        self.api_key = api_key or os.getenv('AZURE_OPENAI_API_KEY')
        self.endpoint = endpoint or os.getenv('AZURE_OPENAI_ENDPOINT')
        self.deployment_name = deployment_name or os.getenv('AZURE_OPENAI_DEPLOYMENT_NAME')
        self.api_version = api_version

        if not self.api_key:
            raise ValueError("Azure OpenAI API key required. Set AZURE_OPENAI_API_KEY environment variable.")

        if not self.endpoint:
            raise ValueError("Azure OpenAI endpoint required. Set AZURE_OPENAI_ENDPOINT environment variable.")

        if not self.deployment_name:
            raise ValueError("Azure OpenAI deployment name required. Set AZURE_OPENAI_DEPLOYMENT_NAME environment variable.")

        try:
            from openai import AzureOpenAI
            self.client = AzureOpenAI(
                api_key=self.api_key,
                api_version=self.api_version,
                azure_endpoint=self.endpoint
            )
        except ImportError:
            raise ImportError("openai package required. Install with: pip install openai")

    def generate(self, prompt: str, temperature: float = 0.7, max_tokens: int = 1000) -> str:
        """Generate text using Azure OpenAI API"""
        try:
            response = self.client.chat.completions.create(
                model=self.deployment_name,  # Azure uses deployment name as model
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content
        except Exception as e:
            raise Exception(f"Azure OpenAI API error: {str(e)}")


class MockLLMClient(BaseLLMClient):
    """Mock LLM client for testing without Azure API"""

    def __init__(self):
        self.model = "mock"

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
        provider: LLM provider name ('azure' or 'mock')
        **kwargs: Additional arguments for client initialization

    Returns:
        Initialized LLM client
    """
    if provider.lower() == "azure":
        return AzureOpenAIClient(**kwargs)
    elif provider.lower() == "mock":
        return MockLLMClient(**kwargs)
    else:
        raise ValueError(f"Unknown provider: {provider}. Available: azure, mock")
