"""
Curated Web Search Module
Supplements database facts with verified web sources about household water
"""

from typing import List, Dict, Any, Optional
import json
import re


class CuratedWebSearch:
    """Curated web search for household water information"""

    def __init__(self, search_client, config: Dict[str, Any]):
        """
        Initialize Curated Web Search

        Args:
            search_client: Client for web search API
            config: Configuration dictionary
        """
        self.search_client = search_client
        self.config = config
        self.max_results = config.get('max_results', 3)
        self.trusted_domains = config.get('trusted_domains', self._get_default_trusted_domains())
        self.enable_search = config.get('enable_web_search', True)

    def _get_default_trusted_domains(self) -> List[str]:
        """Get default list of trusted domains for water information"""
        return [
            'epa.gov',
            'cdc.gov',
            'who.int',
            'awwa.org',  # American Water Works Association
            'water.usgs.gov',
            'waterrf.org',  # Water Research Foundation
            'nrdc.org',
            'ewg.org'  # Environmental Working Group
        ]

    def search(self, question: str, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Search curated web sources for household water information

        Args:
            question: User's question
            filters: Optional search filters

        Returns:
            List of search results from trusted sources
        """
        if not self.enable_search:
            return []

        # Build search query
        query = self._build_search_query(question, filters)

        # Execute search
        results = self._execute_search(query)

        # Filter and validate results
        curated_results = self._curate_results(results)

        return curated_results[:self.max_results]

    def _build_search_query(self, question: str, filters: Optional[Dict[str, Any]]) -> str:
        """Build optimized search query"""
        # Base query
        query = f"household water {question}"

        # Add domain restrictions in query
        domain_filter = ' OR '.join([f'site:{domain}' for domain in self.trusted_domains[:3]])
        query = f"({query}) ({domain_filter})"

        # Add additional filters
        if filters:
            if filters.get('recent_only'):
                query += " after:2020"

            if filters.get('location'):
                query += f" {filters['location']}"

        return query

    def _execute_search(self, query: str) -> List[Dict[str, Any]]:
        """Execute web search"""
        try:
            results = self.search_client.search(
                query=query,
                num_results=self.max_results * 2  # Get extra for filtering
            )
            return results
        except Exception as e:
            print(f"Web search error: {str(e)}")
            return []

    def _curate_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter and validate search results"""
        curated = []

        for result in results:
            # Extract URL and check if from trusted domain
            url = result.get('url', '')
            if not self._is_trusted_domain(url):
                continue

            # Extract and clean content
            content = self._extract_clean_content(result)
            if not content or len(content) < 50:
                continue

            # Validate content relevance
            if not self._is_water_related(content):
                continue

            # Structure result
            curated.append({
                'source': 'web_search',
                'url': url,
                'title': result.get('title', ''),
                'content': content,
                'snippet': result.get('snippet', ''),
                'confidence': self._calculate_source_confidence(url),
                'domain': self._extract_domain(url)
            })

        return curated

    def _is_trusted_domain(self, url: str) -> bool:
        """Check if URL is from a trusted domain"""
        url_lower = url.lower()
        return any(domain in url_lower for domain in self.trusted_domains)

    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL"""
        match = re.search(r'https?://(?:www\.)?([^/]+)', url)
        return match.group(1) if match else ''

    def _extract_clean_content(self, result: Dict[str, Any]) -> str:
        """Extract and clean content from search result"""
        # Try to get full content, fall back to snippet
        content = result.get('content', '') or result.get('snippet', '')

        # Clean HTML tags if present
        content = re.sub(r'<[^>]+>', '', content)

        # Clean extra whitespace
        content = ' '.join(content.split())

        return content

    def _is_water_related(self, content: str) -> bool:
        """Validate that content is water-related"""
        water_keywords = [
            'water', 'tap', 'drinking', 'municipal', 'treatment',
            'contaminant', 'quality', 'safety', 'chlorine', 'fluoride',
            'EPA', 'testing', 'filter', 'purification'
        ]

        content_lower = content.lower()
        keyword_count = sum(1 for keyword in water_keywords if keyword in content_lower)

        # Require at least 3 water-related keywords
        return keyword_count >= 3

    def _calculate_source_confidence(self, url: str) -> float:
        """Calculate confidence score based on source"""
        # Government sources highest confidence
        if any(domain in url for domain in ['epa.gov', 'cdc.gov', 'who.int', 'usgs.gov']):
            return 0.95

        # Professional associations
        if any(domain in url for domain in ['awwa.org', 'waterrf.org']):
            return 0.90

        # Reputable NGOs
        if any(domain in url for domain in ['nrdc.org', 'ewg.org']):
            return 0.85

        # Default for other trusted sources
        return 0.75

    def search_specific_topic(self, topic: str, location: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Search for specific water topic

        Args:
            topic: Specific topic (e.g., 'lead', 'chlorine', 'bacteria')
            location: Optional location filter

        Returns:
            List of relevant search results
        """
        query = f"household water {topic}"
        if location:
            query += f" {location}"

        filters = {'recent_only': True}
        return self.search(query, filters)

    def get_regulatory_info(self, contaminant: str) -> List[Dict[str, Any]]:
        """
        Get regulatory information for specific contaminant

        Args:
            contaminant: Name of contaminant

        Returns:
            List of regulatory information from official sources
        """
        # Focus on EPA and CDC
        query = f"EPA drinking water standards {contaminant} site:epa.gov OR site:cdc.gov"

        try:
            results = self.search_client.search(query=query, num_results=5)
            return self._curate_results(results)
        except Exception as e:
            print(f"Regulatory info search error: {str(e)}")
            return []

    def verify_claim(self, claim: str) -> Dict[str, Any]:
        """
        Verify a specific claim about water

        Args:
            claim: Claim to verify

        Returns:
            Verification result with supporting sources
        """
        # Search for information about the claim
        results = self.search(claim, filters={'recent_only': True})

        if not results:
            return {
                'verified': False,
                'confidence': 0.0,
                'sources': []
            }

        # Check if results support the claim
        supporting_sources = []
        for result in results:
            # Simple keyword matching (can be enhanced with NLU)
            if self._check_claim_support(claim, result['content']):
                supporting_sources.append(result)

        verified = len(supporting_sources) >= 2  # At least 2 sources support
        confidence = min(len(supporting_sources) / 3.0, 1.0)

        return {
            'verified': verified,
            'confidence': confidence,
            'sources': supporting_sources
        }

    def _check_claim_support(self, claim: str, content: str) -> bool:
        """Check if content supports claim"""
        # Extract key terms from claim
        claim_terms = set(claim.lower().split())
        content_terms = set(content.lower().split())

        # Calculate overlap
        overlap = claim_terms.intersection(content_terms)
        overlap_ratio = len(overlap) / len(claim_terms) if claim_terms else 0

        # Require significant overlap
        return overlap_ratio > 0.5


class MockSearchClient:
    """Mock search client for testing without API"""

    def search(self, query: str, num_results: int = 5) -> List[Dict[str, Any]]:
        """Mock search returning sample results"""
        return [
            {
                'url': 'https://www.epa.gov/ground-water-and-drinking-water',
                'title': 'Drinking Water Safety | EPA',
                'snippet': 'EPA ensures tap water is safe to drink. The Safe Drinking Water Act requires EPA to set standards for drinking water quality.',
                'content': 'EPA ensures tap water from public water systems is safe to drink. The Safe Drinking Water Act requires EPA to set standards for drinking water quality and oversee the states, localities, and water suppliers who implement those standards.'
            },
            {
                'url': 'https://www.cdc.gov/healthywater/drinking/',
                'title': 'Drinking Water | CDC',
                'snippet': 'Information about drinking water quality, treatment, and safety from CDC.',
                'content': 'Drinking water quality varies from place to place, depending on the condition of the source water and the treatment it receives. CDC provides information about water treatment and testing.'
            }
        ]
