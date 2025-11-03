"""
Strategy Extraction Module
Extracts and structures persuasive strategies from LLM outputs
"""

from typing import List, Dict, Any
import re
import json


class StrategyExtractor:
    """Extracts structured strategies from raw LLM outputs"""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Strategy Extractor

        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.min_strategies = config.get('min_strategies', 1)
        self.max_strategies = config.get('max_strategies', 5)

    def extract_strategies(self, llm_output: str) -> List[Dict[str, Any]]:
        """
        Extract structured strategies from LLM output

        Args:
            llm_output: Raw output from LLM generation

        Returns:
            List of structured strategy dictionaries
        """
        # Try multiple extraction methods
        strategies = []

        # Method 1: Try to parse as JSON if present
        json_strategies = self._extract_json_strategies(llm_output)
        if json_strategies:
            strategies.extend(json_strategies)

        # Method 2: Pattern-based extraction for structured text
        if not strategies:
            strategies = self._extract_pattern_based(llm_output)

        # Method 3: Fallback to section-based extraction
        if not strategies:
            strategies = self._extract_section_based(llm_output)

        # Validate and clean strategies
        strategies = self._validate_strategies(strategies)

        return strategies[:self.max_strategies]

    def _extract_json_strategies(self, text: str) -> List[Dict[str, Any]]:
        """Try to extract JSON-formatted strategies"""
        try:
            # Look for JSON blocks
            json_match = re.search(r'\[.*\]', text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(0))

            # Look for individual JSON objects
            json_objects = re.findall(r'\{[^{}]*\}', text)
            if json_objects:
                return [json.loads(obj) for obj in json_objects]
        except json.JSONDecodeError:
            pass

        return []

    def _extract_pattern_based(self, text: str) -> List[Dict[str, Any]]:
        """Extract strategies using pattern matching"""
        strategies = []

        # Pattern for numbered strategies
        strategy_blocks = re.split(r'\n\s*(?:Strategy|#)\s*\d+', text)

        for block in strategy_blocks[1:]:  # Skip first split (before any strategy)
            strategy = self._parse_strategy_block(block)
            if strategy:
                strategies.append(strategy)

        return strategies

    def _parse_strategy_block(self, block: str) -> Dict[str, Any]:
        """Parse a single strategy block into structured format"""
        strategy = {
            'strategy_type': '',
            'key_message': '',
            'supporting_evidence': '',
            'delivery_approach': '',
            'trust_elements': []
        }

        # Extract strategy type
        type_match = re.search(r'(?:Strategy\s*Type|Type)\s*:?\s*(.+?)(?:\n|$)', block, re.IGNORECASE)
        if type_match:
            strategy['strategy_type'] = type_match.group(1).strip()

        # Extract key message
        message_match = re.search(r'(?:Key\s*Message|Message)\s*:?\s*(.+?)(?:\n(?:[A-Z]|\d)|$)', block, re.IGNORECASE | re.DOTALL)
        if message_match:
            strategy['key_message'] = message_match.group(1).strip()

        # Extract supporting evidence
        evidence_match = re.search(r'(?:Supporting\s*Evidence|Evidence)\s*:?\s*(.+?)(?:\n(?:[A-Z]|\d)|$)', block, re.IGNORECASE | re.DOTALL)
        if evidence_match:
            strategy['supporting_evidence'] = evidence_match.group(1).strip()

        # Extract delivery approach
        delivery_match = re.search(r'(?:Delivery\s*Approach|Approach)\s*:?\s*(.+?)(?:\n(?:[A-Z]|\d)|$)', block, re.IGNORECASE | re.DOTALL)
        if delivery_match:
            strategy['delivery_approach'] = delivery_match.group(1).strip()

        # Extract trust-building elements
        trust_match = re.search(r'(?:Trust[-\s]*Building\s*Elements?|Trust\s*Elements?)\s*:?\s*(.+?)(?:\n\n|$)', block, re.IGNORECASE | re.DOTALL)
        if trust_match:
            trust_text = trust_match.group(1).strip()
            # Split by bullet points, numbers, or newlines
            trust_items = re.split(r'[-•*\n]\s*', trust_text)
            strategy['trust_elements'] = [item.strip() for item in trust_items if item.strip()]

        # Return strategy if it has meaningful content
        if strategy['key_message'] or strategy['strategy_type']:
            return strategy

        return None

    def _extract_section_based(self, text: str) -> List[Dict[str, Any]]:
        """Fallback: Extract strategies by identifying major sections"""
        # Split by double newlines to get paragraphs
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]

        strategies = []
        current_strategy = None

        for para in paragraphs:
            # Check if this is a new strategy header
            if re.match(r'^(?:Strategy|Approach|Method)\s*\d+', para, re.IGNORECASE):
                if current_strategy:
                    strategies.append(current_strategy)
                current_strategy = {
                    'strategy_type': 'General',
                    'key_message': para,
                    'supporting_evidence': '',
                    'delivery_approach': '',
                    'trust_elements': []
                }
            elif current_strategy:
                # Add to current strategy's supporting evidence
                if not current_strategy['supporting_evidence']:
                    current_strategy['supporting_evidence'] = para
                else:
                    current_strategy['supporting_evidence'] += '\n' + para

        if current_strategy:
            strategies.append(current_strategy)

        return strategies

    def _validate_strategies(self, strategies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validate and clean extracted strategies"""
        valid_strategies = []

        for strategy in strategies:
            # Ensure all required fields exist
            if not isinstance(strategy, dict):
                continue

            # Add default values for missing fields
            validated = {
                'strategy_type': strategy.get('strategy_type', 'General'),
                'key_message': strategy.get('key_message', ''),
                'supporting_evidence': strategy.get('supporting_evidence', ''),
                'delivery_approach': strategy.get('delivery_approach', ''),
                'trust_elements': strategy.get('trust_elements', [])
            }

            # Skip if no meaningful content
            if not validated['key_message'] and not validated['supporting_evidence']:
                continue

            # Clean up whitespace
            validated['key_message'] = ' '.join(validated['key_message'].split())
            validated['supporting_evidence'] = ' '.join(validated['supporting_evidence'].split())
            validated['delivery_approach'] = ' '.join(validated['delivery_approach'].split())

            valid_strategies.append(validated)

        return valid_strategies

    def merge_diverse_strategies(self,
                                strategy_outputs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Merge strategies from multiple model outputs

        Args:
            strategy_outputs: List of outputs from different models

        Returns:
            Merged and deduplicated list of strategies
        """
        all_strategies = []

        for output in strategy_outputs:
            model_name = output.get('model', 'unknown')
            strategies_text = output.get('strategies', '')

            strategies = self.extract_strategies(strategies_text)

            # Add source model to each strategy
            for strategy in strategies:
                strategy['source_model'] = model_name
                all_strategies.append(strategy)

        # Deduplicate based on key_message similarity
        unique_strategies = self._deduplicate_strategies(all_strategies)

        return unique_strategies

    def _deduplicate_strategies(self, strategies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate or highly similar strategies"""
        if not strategies:
            return []

        unique = [strategies[0]]

        for strategy in strategies[1:]:
            is_duplicate = False
            current_msg = strategy['key_message'].lower()

            for existing in unique:
                existing_msg = existing['key_message'].lower()

                # Simple similarity check (can be enhanced with embeddings)
                if self._calculate_similarity(current_msg, existing_msg) > 0.8:
                    is_duplicate = True
                    break

            if not is_duplicate:
                unique.append(strategy)

        return unique

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate simple word overlap similarity"""
        if not text1 or not text2:
            return 0.0

        words1 = set(text1.split())
        words2 = set(text2.split())

        intersection = words1.intersection(words2)
        union = words1.union(words2)

        return len(intersection) / len(union) if union else 0.0
