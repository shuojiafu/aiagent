"""
SQL-based RAG Module
Retrieves facts from localized structured database about household water
"""

from typing import List, Dict, Any, Optional
import sqlite3
import json


class SQLRetriever:
    """SQL-based retrieval-augmented generation for household water facts"""

    def __init__(self, database_path: str, config: Dict[str, Any]):
        """
        Initialize SQL Retriever

        Args:
            database_path: Path to SQLite database
            config: Configuration dictionary
        """
        self.database_path = database_path
        self.config = config
        self.conn = None
        self.top_k = config.get('top_k', 5)
        self._connect()

    def _connect(self):
        """Connect to database"""
        try:
            self.conn = sqlite3.connect(self.database_path)
            self.conn.row_factory = sqlite3.Row
        except sqlite3.Error as e:
            raise Exception(f"Database connection failed: {str(e)}")

    def retrieve_facts(self, question: str, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Retrieve relevant facts from database based on question

        Args:
            question: User's question about household water
            filters: Optional filters for retrieval (location, date, etc.)

        Returns:
            List of relevant facts with metadata
        """
        # Extract key terms from question
        key_terms = self._extract_key_terms(question)

        # Build and execute query
        facts = []

        # Try different retrieval strategies
        facts.extend(self._keyword_search(key_terms, filters))
        facts.extend(self._topic_based_search(question, filters))
        facts.extend(self._related_facts_search(facts[:3]))  # Get related to top results

        # Deduplicate and rank
        facts = self._deduplicate_facts(facts)
        facts = self._rank_by_relevance(facts, question)

        return facts[:self.top_k]

    def _extract_key_terms(self, question: str) -> List[str]:
        """Extract key terms from question"""
        # Common stop words
        stop_words = {'is', 'are', 'the', 'a', 'an', 'in', 'on', 'at', 'to', 'for',
                     'of', 'with', 'by', 'from', 'my', 'your', 'our', 'their',
                     'what', 'how', 'why', 'when', 'where', 'can', 'should', 'would'}

        # Tokenize and filter
        terms = question.lower().split()
        key_terms = [t.strip('.,!?') for t in terms if t.lower() not in stop_words and len(t) > 2]

        return key_terms

    def _keyword_search(self, key_terms: List[str], filters: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Search database using keywords"""
        if not key_terms:
            return []

        facts = []

        try:
            cursor = self.conn.cursor()

            # Build search query with full-text search if available
            # Otherwise use LIKE queries
            for term in key_terms[:5]:  # Limit to top 5 terms
                query = """
                    SELECT id, category, topic, content, source, confidence,
                           location, last_updated
                    FROM water_facts
                    WHERE content LIKE ? OR topic LIKE ?
                """
                params = [f'%{term}%', f'%{term}%']

                # Add filters if provided
                if filters:
                    if filters.get('location'):
                        query += " AND location = ?"
                        params.append(filters['location'])
                    if filters.get('category'):
                        query += " AND category = ?"
                        params.append(filters['category'])

                query += " LIMIT 10"

                cursor.execute(query, params)
                rows = cursor.fetchall()

                for row in rows:
                    facts.append({
                        'id': row['id'],
                        'category': row['category'],
                        'topic': row['topic'],
                        'content': row['content'],
                        'source': row['source'],
                        'confidence': row['confidence'],
                        'location': row['location'],
                        'last_updated': row['last_updated'],
                        'retrieval_method': 'keyword',
                        'match_term': term
                    })

        except sqlite3.Error as e:
            print(f"Keyword search error: {str(e)}")

        return facts

    def _topic_based_search(self, question: str, filters: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Search by predefined topics"""
        # Map question to water topics
        topic_keywords = {
            'safety': ['safe', 'danger', 'risk', 'harm', 'toxic'],
            'quality': ['quality', 'clean', 'pure', 'contamination'],
            'treatment': ['treatment', 'process', 'disinfection', 'chlorine', 'filter'],
            'testing': ['test', 'check', 'measure', 'level', 'standard'],
            'contaminants': ['lead', 'bacteria', 'chemical', 'pollutant', 'contaminant'],
            'taste_odor': ['taste', 'smell', 'odor', 'flavor', 'color'],
            'health': ['health', 'disease', 'illness', 'effect', 'impact'],
            'regulations': ['regulation', 'standard', 'EPA', 'law', 'requirement']
        }

        question_lower = question.lower()
        matched_topics = []

        for topic, keywords in topic_keywords.items():
            if any(keyword in question_lower for keyword in keywords):
                matched_topics.append(topic)

        if not matched_topics:
            return []

        facts = []

        try:
            cursor = self.conn.cursor()

            for topic in matched_topics:
                query = """
                    SELECT id, category, topic, content, source, confidence,
                           location, last_updated
                    FROM water_facts
                    WHERE topic = ? OR category = ?
                """
                params = [topic, topic]

                if filters:
                    if filters.get('location'):
                        query += " AND location = ?"
                        params.append(filters['location'])

                query += " LIMIT 5"

                cursor.execute(query, params)
                rows = cursor.fetchall()

                for row in rows:
                    facts.append({
                        'id': row['id'],
                        'category': row['category'],
                        'topic': row['topic'],
                        'content': row['content'],
                        'source': row['source'],
                        'confidence': row['confidence'],
                        'location': row['location'],
                        'last_updated': row['last_updated'],
                        'retrieval_method': 'topic',
                        'match_topic': topic
                    })

        except sqlite3.Error as e:
            print(f"Topic search error: {str(e)}")

        return facts

    def _related_facts_search(self, seed_facts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Find facts related to seed facts"""
        if not seed_facts:
            return []

        facts = []

        try:
            cursor = self.conn.cursor()

            for seed in seed_facts:
                category = seed.get('category')
                topic = seed.get('topic')

                if category or topic:
                    query = """
                        SELECT id, category, topic, content, source, confidence,
                               location, last_updated
                        FROM water_facts
                        WHERE (category = ? OR topic = ?) AND id != ?
                        LIMIT 3
                    """
                    cursor.execute(query, [category, topic, seed.get('id')])
                    rows = cursor.fetchall()

                    for row in rows:
                        facts.append({
                            'id': row['id'],
                            'category': row['category'],
                            'topic': row['topic'],
                            'content': row['content'],
                            'source': row['source'],
                            'confidence': row['confidence'],
                            'location': row['location'],
                            'last_updated': row['last_updated'],
                            'retrieval_method': 'related',
                            'related_to': seed.get('id')
                        })

        except sqlite3.Error as e:
            print(f"Related facts search error: {str(e)}")

        return facts

    def _deduplicate_facts(self, facts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate facts"""
        seen_ids = set()
        unique_facts = []

        for fact in facts:
            fact_id = fact.get('id')
            if fact_id not in seen_ids:
                seen_ids.add(fact_id)
                unique_facts.append(fact)

        return unique_facts

    def _rank_by_relevance(self, facts: List[Dict[str, Any]], question: str) -> List[Dict[str, Any]]:
        """Rank facts by relevance to question"""
        question_terms = set(self._extract_key_terms(question))

        for fact in facts:
            score = 0.0

            # Base confidence score
            score += fact.get('confidence', 0.5) * 0.3

            # Content relevance
            content_terms = set(fact.get('content', '').lower().split())
            term_overlap = len(question_terms.intersection(content_terms))
            score += (term_overlap / max(len(question_terms), 1)) * 0.4

            # Retrieval method bonus
            method = fact.get('retrieval_method', '')
            if method == 'keyword':
                score += 0.2
            elif method == 'topic':
                score += 0.15

            # Recency bonus (if last_updated available)
            # TODO: Add date-based scoring

            fact['relevance_score'] = score

        return sorted(facts, key=lambda x: x.get('relevance_score', 0), reverse=True)

    def get_location_specific_facts(self, location: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get location-specific water facts

        Args:
            location: Location identifier
            limit: Maximum number of facts to return

        Returns:
            List of location-specific facts
        """
        facts = []

        try:
            cursor = self.conn.cursor()
            query = """
                SELECT id, category, topic, content, source, confidence,
                       location, last_updated
                FROM water_facts
                WHERE location = ?
                ORDER BY confidence DESC
                LIMIT ?
            """
            cursor.execute(query, [location, limit])
            rows = cursor.fetchall()

            for row in rows:
                facts.append({
                    'id': row['id'],
                    'category': row['category'],
                    'topic': row['topic'],
                    'content': row['content'],
                    'source': row['source'],
                    'confidence': row['confidence'],
                    'location': row['location'],
                    'last_updated': row['last_updated']
                })

        except sqlite3.Error as e:
            print(f"Location-specific search error: {str(e)}")

        return facts

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
