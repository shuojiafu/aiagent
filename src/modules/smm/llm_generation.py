"""
LLM Generation Module
Generates persuasive strategies using large language models
"""

from typing import List, Dict, Any
import json


class LLMStrategyGenerator:
    """Generates persuasive strategies for building trust in household water"""

    def __init__(self, llm_client, config: Dict[str, Any]):
        """
        Initialize LLM Strategy Generator

        Args:
            llm_client: Client for LLM API (OpenAI, Anthropic, etc.)
            config: Configuration dictionary
        """
        self.llm_client = llm_client
        self.config = config
        self.temperature = config.get('temperature', 0.7)
        self.max_tokens = config.get('max_tokens', 2000)

    def generate_strategies(self,
                          user_question: str,
                          retrieved_facts: List[Dict[str, Any]]) -> str:
        """
        Generate persuasive strategies based on user question and retrieved facts

        Args:
            user_question: The user's question about household water
            retrieved_facts: List of facts retrieved from QHM module

        Returns:
            Raw LLM output containing persuasive strategies
        """
        # Build context from retrieved facts
        facts_context = self._build_facts_context(retrieved_facts)

        # Create prompt for strategy generation
        prompt = self._create_strategy_prompt(user_question, facts_context)

        # Generate strategies using LLM
        try:
            response = self.llm_client.generate(
                prompt=prompt,
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            return response
        except Exception as e:
            raise Exception(f"LLM generation failed: {str(e)}")

    def _build_facts_context(self, facts: List[Dict[str, Any]]) -> str:
        """Build context string from retrieved facts"""
        if not facts:
            return "No specific facts retrieved."

        context_parts = []
        for i, fact in enumerate(facts, 1):
            source = fact.get('source', 'database')
            content = fact.get('content', '')
            confidence = fact.get('confidence', 'N/A')

            context_parts.append(
                f"Fact {i} (Source: {source}, Confidence: {confidence}):\n{content}"
            )

        return "\n\n".join(context_parts)

    def _create_strategy_prompt(self, question: str, facts_context: str) -> str:
        """Create prompt for LLM strategy generation"""
        prompt = f"""You are an expert in building trust in household water systems through persuasive communication.

User Question: {question}

Available Facts:
{facts_context}

Your task is to generate persuasive strategies to answer this question and build trust in household water. For each strategy, provide:

1. Strategy Type (e.g., Authority Appeal, Evidence-Based, Social Proof, Transparency, etc.)
2. Key Message: The main point to communicate
3. Supporting Evidence: How the facts support this message
4. Delivery Approach: How to present this persuasively
5. Trust-Building Elements: Specific elements that build credibility

Generate 3-5 distinct persuasive strategies that:
- Use the available facts accurately
- Build trust in household water safety
- Address potential concerns empathetically
- Are scientifically grounded
- Are appropriate for general public audience

Format your response as a structured list of strategies."""

        return prompt


class MultiStrategyGenerator(LLMStrategyGenerator):
    """Extended generator that can use multiple LLM models"""

    def __init__(self, llm_clients: Dict[str, Any], config: Dict[str, Any]):
        """
        Initialize with multiple LLM clients

        Args:
            llm_clients: Dictionary of LLM clients {name: client}
            config: Configuration dictionary
        """
        self.llm_clients = llm_clients
        self.config = config
        self.temperature = config.get('temperature', 0.7)
        self.max_tokens = config.get('max_tokens', 2000)
        self.primary_model = config.get('primary_model', list(llm_clients.keys())[0])

    def generate_strategies(self,
                          user_question: str,
                          retrieved_facts: List[Dict[str, Any]],
                          model_name: str = None) -> str:
        """
        Generate strategies using specified model or primary model

        Args:
            user_question: The user's question
            retrieved_facts: Retrieved facts from QHM
            model_name: Optional specific model to use

        Returns:
            Raw LLM output with strategies
        """
        model = model_name or self.primary_model

        if model not in self.llm_clients:
            raise ValueError(f"Model {model} not available. Available: {list(self.llm_clients.keys())}")

        self.llm_client = self.llm_clients[model]
        return super().generate_strategies(user_question, retrieved_facts)

    def generate_diverse_strategies(self,
                                   user_question: str,
                                   retrieved_facts: List[Dict[str, Any]]) -> List[str]:
        """
        Generate strategies from multiple models for diversity

        Args:
            user_question: The user's question
            retrieved_facts: Retrieved facts from QHM

        Returns:
            List of strategy outputs from different models
        """
        outputs = []
        for model_name in self.llm_clients.keys():
            try:
                output = self.generate_strategies(
                    user_question,
                    retrieved_facts,
                    model_name
                )
                outputs.append({
                    'model': model_name,
                    'strategies': output
                })
            except Exception as e:
                print(f"Warning: Strategy generation failed for {model_name}: {str(e)}")

        return outputs
