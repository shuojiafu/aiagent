"""
Fact-Check & Information Retrieval Module
Validates strategies against facts and retrieves additional supporting information
"""

from typing import List, Dict, Any, Tuple
import re


class FactChecker:
    """Validates persuasive strategies against factual information"""

    def __init__(self, database_client, web_search_client, config: Dict[str, Any]):
        """
        Initialize Fact Checker

        Args:
            database_client: Client for accessing structured water database
            web_search_client: Client for curated web searches
            config: Configuration dictionary
        """
        self.database = database_client
        self.web_search = web_search_client
        self.config = config
        self.fact_check_threshold = config.get('fact_check_threshold', 0.7)

    def validate_and_enhance_strategies(self,
                                       strategies: List[Dict[str, Any]],
                                       original_facts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Validate strategies against facts and enhance with additional IR

        Args:
            strategies: List of extracted strategies
            original_facts: Facts originally retrieved from QHM

        Returns:
            List of validated and enhanced strategies
        """
        validated_strategies = []

        for strategy in strategies:
            # Check factual accuracy
            validation_result = self._check_factual_accuracy(strategy, original_facts)

            # If valid, enhance with additional information
            if validation_result['is_valid']:
                enhanced_strategy = self._enhance_with_ir(strategy, validation_result)
                enhanced_strategy['validation_score'] = validation_result['confidence']
                enhanced_strategy['fact_check_status'] = 'verified'
                validated_strategies.append(enhanced_strategy)
            else:
                # Flag for review or correction
                strategy['fact_check_status'] = 'failed'
                strategy['validation_issues'] = validation_result.get('issues', [])

                # Try to salvage with corrections
                corrected = self._attempt_correction(strategy, original_facts)
                if corrected:
                    validated_strategies.append(corrected)

        return validated_strategies

    def _check_factual_accuracy(self,
                                strategy: Dict[str, Any],
                                facts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Check if strategy claims are supported by facts

        Args:
            strategy: Strategy to validate
            facts: Available facts

        Returns:
            Validation result dictionary
        """
        # Extract claims from strategy
        claims = self._extract_claims(strategy)

        if not claims:
            return {
                'is_valid': True,
                'confidence': 0.5,
                'issues': [],
                'supporting_facts': []
            }

        # Check each claim against facts
        supported_claims = 0
        supporting_facts = []
        issues = []

        for claim in claims:
            support = self._find_supporting_facts(claim, facts)
            if support:
                supported_claims += 1
                supporting_facts.extend(support)
            else:
                # Check database for verification
                db_support = self._verify_in_database(claim)
                if db_support:
                    supported_claims += 1
                    supporting_facts.append(db_support)
                else:
                    issues.append(f"Claim not verified: {claim}")

        confidence = supported_claims / len(claims) if claims else 0.0
        is_valid = confidence >= self.fact_check_threshold

        return {
            'is_valid': is_valid,
            'confidence': confidence,
            'issues': issues,
            'supporting_facts': supporting_facts
        }

    def _extract_claims(self, strategy: Dict[str, Any]) -> List[str]:
        """Extract verifiable claims from strategy"""
        claims = []

        # Extract from key message
        key_message = strategy.get('key_message', '')
        if key_message:
            # Split by sentences
            sentences = re.split(r'[.!?]+', key_message)
            claims.extend([s.strip() for s in sentences if s.strip()])

        # Extract from supporting evidence
        evidence = strategy.get('supporting_evidence', '')
        if evidence:
            sentences = re.split(r'[.!?]+', evidence)
            claims.extend([s.strip() for s in sentences if s.strip()])

        # Filter out very short claims
        claims = [c for c in claims if len(c.split()) >= 3]

        return claims

    def _find_supporting_facts(self,
                              claim: str,
                              facts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Find facts that support a claim"""
        supporting = []

        claim_words = set(claim.lower().split())

        for fact in facts:
            fact_content = fact.get('content', '').lower()
            fact_words = set(fact_content.split())

            # Calculate word overlap
            overlap = claim_words.intersection(fact_words)
            overlap_ratio = len(overlap) / len(claim_words) if claim_words else 0

            # If significant overlap, consider it supporting
            if overlap_ratio > 0.3:
                supporting.append(fact)

        return supporting

    def _verify_in_database(self, claim: str) -> Dict[str, Any]:
        """Verify claim against database"""
        try:
            # Search database for relevant information
            results = self.database.search(claim, limit=3)

            if results:
                return {
                    'source': 'database_verification',
                    'content': results[0].get('content', ''),
                    'confidence': results[0].get('confidence', 0.8)
                }
        except Exception as e:
            print(f"Database verification error: {str(e)}")

        return None

    def _enhance_with_ir(self,
                        strategy: Dict[str, Any],
                        validation_result: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance strategy with additional information retrieval"""
        enhanced = strategy.copy()

        # Add supporting facts to strategy
        enhanced['supporting_facts'] = validation_result.get('supporting_facts', [])

        # Retrieve additional context if needed
        if len(enhanced['supporting_facts']) < 2:
            additional_info = self._retrieve_additional_info(strategy)
            if additional_info:
                enhanced['additional_context'] = additional_info

        return enhanced

    def _retrieve_additional_info(self, strategy: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Retrieve additional information to support strategy"""
        additional = []

        # Extract key topics from strategy
        topics = self._extract_topics(strategy)

        # Search for each topic
        for topic in topics[:3]:  # Limit to top 3 topics
            try:
                # Try database first
                db_results = self.database.search(topic, limit=2)
                if db_results:
                    additional.extend([{
                        'source': 'database',
                        'topic': topic,
                        'content': r.get('content', '')
                    } for r in db_results])

                # Supplement with curated web search if enabled
                if self.config.get('enable_web_enhancement', False):
                    web_results = self.web_search.search(f"household water {topic}", limit=1)
                    if web_results:
                        additional.extend([{
                            'source': 'web',
                            'topic': topic,
                            'content': r.get('content', ''),
                            'url': r.get('url', '')
                        } for r in web_results])
            except Exception as e:
                print(f"Additional info retrieval error for {topic}: {str(e)}")

        return additional

    def _extract_topics(self, strategy: Dict[str, Any]) -> List[str]:
        """Extract key topics from strategy for IR"""
        # Common water-related topics
        water_topics = [
            'chlorine', 'fluoride', 'lead', 'bacteria', 'contamination',
            'treatment', 'filtration', 'testing', 'pH', 'hardness',
            'disinfection', 'safety', 'quality', 'standards', 'EPA'
        ]

        # Combine strategy text
        text = ' '.join([
            strategy.get('key_message', ''),
            strategy.get('supporting_evidence', ''),
            strategy.get('strategy_type', '')
        ]).lower()

        # Find mentioned topics
        mentioned_topics = [topic for topic in water_topics if topic in text]

        return mentioned_topics

    def _attempt_correction(self,
                           strategy: Dict[str, Any],
                           facts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Attempt to correct a failed strategy"""
        # Try to find relevant facts
        strategy_text = strategy.get('key_message', '')
        relevant_facts = self._find_supporting_facts(strategy_text, facts)

        if relevant_facts:
            # Create corrected version based on facts
            corrected = strategy.copy()
            corrected['supporting_evidence'] = '\n'.join([
                f.get('content', '') for f in relevant_facts[:2]
            ])
            corrected['fact_check_status'] = 'corrected'
            corrected['validation_score'] = 0.6

            return corrected

        return None

    def rank_strategies_by_evidence(self,
                                   strategies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Rank strategies by strength of evidence

        Args:
            strategies: List of validated strategies

        Returns:
            Strategies sorted by evidence strength
        """
        def evidence_score(strategy):
            score = 0.0

            # Validation score
            score += strategy.get('validation_score', 0.0) * 0.4

            # Number of supporting facts
            num_facts = len(strategy.get('supporting_facts', []))
            score += min(num_facts / 5.0, 1.0) * 0.3

            # Has additional context
            if strategy.get('additional_context'):
                score += 0.2

            # Verified status
            if strategy.get('fact_check_status') == 'verified':
                score += 0.1

            return score

        return sorted(strategies, key=evidence_score, reverse=True)
