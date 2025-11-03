"""
Response Merger Module
Merges QHM facts and SMM strategies into cohesive final answer
"""

from typing import List, Dict, Any


class ResponseMerger:
    """Merges retrieved facts and persuasive strategies into final answer"""

    def __init__(self, llm_client, config: Dict[str, Any]):
        """
        Initialize Response Merger

        Args:
            llm_client: Client for LLM API
            config: Configuration dictionary
        """
        self.llm_client = llm_client
        self.config = config
        self.max_strategies = config.get('max_strategies_in_response', 3)
        self.response_style = config.get('response_style', 'balanced')  # balanced, factual, persuasive

    def merge(self,
             user_question: str,
             qhm_facts: List[Dict[str, Any]],
             smm_strategies: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Merge QHM facts and SMM strategies into final answer

        Args:
            user_question: Original user question
            qhm_facts: Facts retrieved from QHM module
            smm_strategies: Validated strategies from SMM module

        Returns:
            Dictionary containing final answer and metadata
        """
        # Select best strategies
        selected_strategies = self._select_strategies(smm_strategies, qhm_facts)

        # Build integrated response
        response_text = self._build_response(
            user_question,
            qhm_facts,
            selected_strategies
        )

        # Add metadata
        response = {
            'answer': response_text,
            'strategies_used': selected_strategies,
            'facts_referenced': qhm_facts,
            'confidence': self._calculate_response_confidence(qhm_facts, selected_strategies),
            'sources': self._extract_sources(qhm_facts, selected_strategies)
        }

        return response

    def _select_strategies(self,
                          strategies: List[Dict[str, Any]],
                          facts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Select best strategies for response"""
        if not strategies:
            return []

        # Score strategies based on multiple factors
        scored_strategies = []
        for strategy in strategies:
            score = 0.0

            # Validation score
            score += strategy.get('validation_score', 0.5) * 0.4

            # Fact alignment
            score += self._calculate_fact_alignment(strategy, facts) * 0.3

            # Strategy diversity (different types preferred)
            score += 0.2  # TODO: Implement diversity scoring

            # Verification status
            if strategy.get('fact_check_status') == 'verified':
                score += 0.1

            scored_strategies.append((score, strategy))

        # Sort and select top strategies
        scored_strategies.sort(reverse=True, key=lambda x: x[0])
        selected = [s[1] for s in scored_strategies[:self.max_strategies]]

        return selected

    def _calculate_fact_alignment(self,
                                 strategy: Dict[str, Any],
                                 facts: List[Dict[str, Any]]) -> float:
        """Calculate how well strategy aligns with available facts"""
        if not facts:
            return 0.0

        strategy_text = ' '.join([
            strategy.get('key_message', ''),
            strategy.get('supporting_evidence', '')
        ]).lower()

        strategy_terms = set(strategy_text.split())

        # Check overlap with facts
        max_overlap = 0.0
        for fact in facts:
            fact_terms = set(fact.get('content', '').lower().split())
            overlap = len(strategy_terms.intersection(fact_terms))
            overlap_ratio = overlap / len(strategy_terms) if strategy_terms else 0
            max_overlap = max(max_overlap, overlap_ratio)

        return max_overlap

    def _build_response(self,
                       question: str,
                       facts: List[Dict[str, Any]],
                       strategies: List[Dict[str, Any]]) -> str:
        """Build integrated response using LLM"""
        # Prepare context
        facts_context = self._format_facts_for_response(facts)
        strategies_context = self._format_strategies_for_response(strategies)

        # Create prompt for response generation
        prompt = self._create_response_prompt(
            question,
            facts_context,
            strategies_context
        )

        # Generate response
        try:
            response = self.llm_client.generate(
                prompt=prompt,
                temperature=0.3,  # Lower temperature for consistency
                max_tokens=1000
            )
            return response
        except Exception as e:
            # Fallback to template-based response
            return self._fallback_response(question, facts, strategies)

    def _format_facts_for_response(self, facts: List[Dict[str, Any]]) -> str:
        """Format facts for inclusion in response prompt"""
        if not facts:
            return "No specific facts available."

        formatted = []
        for i, fact in enumerate(facts[:5], 1):  # Limit to top 5
            content = fact.get('content', '')
            source = fact.get('source', 'database')
            confidence = fact.get('confidence', 'N/A')

            formatted.append(f"{i}. {content} (Source: {source}, Confidence: {confidence})")

        return '\n'.join(formatted)

    def _format_strategies_for_response(self, strategies: List[Dict[str, Any]]) -> str:
        """Format strategies for inclusion in response prompt"""
        if not strategies:
            return "No strategies available."

        formatted = []
        for i, strategy in enumerate(strategies, 1):
            strategy_type = strategy.get('strategy_type', 'General')
            key_message = strategy.get('key_message', '')
            approach = strategy.get('delivery_approach', '')

            formatted.append(
                f"Strategy {i} ({strategy_type}):\n"
                f"  Message: {key_message}\n"
                f"  Approach: {approach}"
            )

        return '\n\n'.join(formatted)

    def _create_response_prompt(self,
                               question: str,
                               facts_context: str,
                               strategies_context: str) -> str:
        """Create prompt for final response generation"""
        style_instructions = self._get_style_instructions()

        prompt = f"""You are a trusted expert on household water quality and safety. Your goal is to provide accurate, reassuring, and helpful information.

User Question: {question}

Available Facts:
{facts_context}

Persuasive Strategies:
{strategies_context}

{style_instructions}

Generate a comprehensive answer that:
1. Directly addresses the user's question
2. Uses the provided facts accurately
3. Incorporates the persuasive strategies naturally
4. Builds trust in household water safety
5. Is empathetic to concerns
6. Provides actionable information if relevant
7. Cites sources appropriately

Keep the response clear, concise, and appropriate for a general audience (2-4 paragraphs).
"""
        return prompt

    def _get_style_instructions(self) -> str:
        """Get style-specific instructions"""
        if self.response_style == 'factual':
            return "Focus primarily on presenting facts clearly and objectively. Use persuasive elements subtly."
        elif self.response_style == 'persuasive':
            return "Emphasize trust-building and persuasive communication while maintaining factual accuracy."
        else:  # balanced
            return "Balance factual information with persuasive elements to inform and build trust."

    def _fallback_response(self,
                          question: str,
                          facts: List[Dict[str, Any]],
                          strategies: List[Dict[str, Any]]) -> str:
        """Generate fallback response without LLM"""
        response_parts = []

        # Opening
        response_parts.append(f"Thank you for your question about household water.")

        # Present facts
        if facts:
            response_parts.append("\nBased on available data:")
            for fact in facts[:3]:
                response_parts.append(f"• {fact.get('content', '')}")

        # Add key messages from strategies
        if strategies:
            response_parts.append("\nKey points to consider:")
            for strategy in strategies[:2]:
                message = strategy.get('key_message', '')
                if message:
                    response_parts.append(f"• {message}")

        # Closing
        response_parts.append("\nFor specific concerns about your water, consult your local water utility or have your water tested.")

        return '\n'.join(response_parts)

    def _calculate_response_confidence(self,
                                      facts: List[Dict[str, Any]],
                                      strategies: List[Dict[str, Any]]) -> float:
        """Calculate overall confidence in response"""
        confidence = 0.0

        # Fact confidence (40%)
        if facts:
            avg_fact_confidence = sum(f.get('confidence', 0.5) for f in facts) / len(facts)
            confidence += avg_fact_confidence * 0.4

        # Strategy validation (40%)
        if strategies:
            avg_strategy_validation = sum(s.get('validation_score', 0.5) for s in strategies) / len(strategies)
            confidence += avg_strategy_validation * 0.4

        # Coverage (20%) - do we have enough information?
        has_facts = len(facts) > 0
        has_strategies = len(strategies) > 0
        if has_facts and has_strategies:
            confidence += 0.2
        elif has_facts or has_strategies:
            confidence += 0.1

        return min(confidence, 1.0)

    def _extract_sources(self,
                        facts: List[Dict[str, Any]],
                        strategies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract all sources used in response"""
        sources = []

        # From facts
        for fact in facts:
            source = {
                'type': 'fact',
                'source': fact.get('source', 'unknown'),
                'confidence': fact.get('confidence', 0.0)
            }
            if 'url' in fact:
                source['url'] = fact['url']
            sources.append(source)

        # From strategies
        for strategy in strategies:
            if 'supporting_facts' in strategy:
                for sf in strategy['supporting_facts']:
                    source = {
                        'type': 'strategy_support',
                        'source': sf.get('source', 'unknown'),
                        'confidence': sf.get('confidence', 0.0)
                    }
                    sources.append(source)

        # Deduplicate
        unique_sources = []
        seen = set()
        for source in sources:
            key = (source['source'], source.get('url', ''))
            if key not in seen:
                seen.add(key)
                unique_sources.append(source)

        return unique_sources

    def generate_followup_questions(self,
                                   user_question: str,
                                   response: Dict[str, Any]) -> List[str]:
        """
        Generate relevant follow-up questions

        Args:
            user_question: Original question
            response: Generated response

        Returns:
            List of suggested follow-up questions
        """
        # TODO: Implement with LLM or rule-based approach
        generic_followups = [
            "How can I test my water at home?",
            "What are the water quality standards in my area?",
            "How often is my water tested?",
            "What should I do if I'm still concerned?"
        ]

        return generic_followups[:3]
