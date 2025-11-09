"""
Main Pipeline Orchestrator
Coordinates QHM and SMM modules to generate final responses
"""

# test

from typing import Dict, Any, List, Optional
import time
import hashlib
import json
import os

from src.config import Config, load_config
from src.utils.llm_client import create_llm_client
from src.utils.database import DatabaseManager, setup_database

# QHM imports
from src.modules.qhm.sql_rag import SQLRetriever
from src.modules.qhm.web_search import CuratedWebSearch, MockSearchClient

# SMM imports
from src.modules.smm.llm_generation import LLMStrategyGenerator
from src.modules.smm.strategy_extraction import StrategyExtractor
from src.modules.smm.fact_check_ir import FactChecker

# Merger import
from src.modules.merger.response_merger import ResponseMerger


class WaterTrustChatbot:
    """
    Main pipeline for Zero-shot Persuasive Chatbot
    Coordinates QHM and SMM to build trust in household water
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize Water Trust Chatbot

        Args:
            config_path: Path to configuration file
        """
        # Load configuration
        self.config = load_config(config_path)

        # Initialize components
        self._initialize_components()

        # Cache for responses
        self.cache = {} if self.config.get('pipeline.enable_caching', True) else None
        self.cache_ttl = self.config.get('pipeline.cache_ttl', 3600)

    def _initialize_components(self):
        """Initialize all pipeline components"""
        # Initialize LLM clients
        llm_config = self.config.get('llm', {})
        provider = llm_config.get('provider', 'mock')

        # Build kwargs based on provider
        if provider == 'azure':
            self.llm_client = create_llm_client(
                provider='azure',
                api_key=llm_config.get('api_key'),
                endpoint=llm_config.get('endpoint'),
                deployment_name=llm_config.get('deployment_name'),
                api_version=llm_config.get('api_version', '2024-02-15-preview')
            )
        else:  # mock
            self.llm_client = create_llm_client(provider='mock')

        # Initialize database
        db_path = self.config.get('database.path', 'data/water_facts.db')
        if not os.path.exists(db_path):
            print(f"Initializing database at {db_path}")
            setup_database(db_path, add_samples=True)

        self.database = DatabaseManager(db_path)

        # Initialize web search
        web_search_config = self.config.get('web_search', {})
        mock_search = MockSearchClient()
        self.web_search = CuratedWebSearch(mock_search, web_search_config)

        # Initialize QHM components
        qhm_config = self.config.get('qhm', {})
        db_config = self.config.get('database', {})
        self.sql_retriever = SQLRetriever(db_path, db_config)

        # Initialize SMM components
        smm_config = self.config.get('smm', {})
        self.strategy_generator = LLMStrategyGenerator(self.llm_client, llm_config)
        self.strategy_extractor = StrategyExtractor(smm_config)
        self.fact_checker = FactChecker(self.database, self.web_search, smm_config)

        # Initialize merger
        merger_config = self.config.get('merger', {})
        self.response_merger = ResponseMerger(self.llm_client, merger_config)

        print("✓ All components initialized successfully")

    def answer_question(self,
                       question: str,
                       location: Optional[str] = None,
                       user_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Answer user question about household water

        Args:
            question: User's question
            location: Optional location for localized facts
            user_context: Optional additional user context

        Returns:
            Dictionary containing answer and metadata
        """
        print(f"\n{'='*60}")
        print(f"Processing question: {question}")
        print(f"{'='*60}\n")

        # Check cache
        if self.cache is not None:
            cache_key = self._generate_cache_key(question, location)
            cached = self._get_cached_response(cache_key)
            if cached:
                print("✓ Using cached response")
                return cached

        start_time = time.time()

        # Phase 1: Question Handling Module (QHM)
        print("Phase 1: Question Handling Module")
        print("-" * 60)
        qhm_facts = self._run_qhm(question, location, user_context)
        print(f"✓ Retrieved {len(qhm_facts)} facts from QHM")

        # Phase 2: Strategy Maintenance Module (SMM)
        print("\nPhase 2: Strategy Maintenance Module")
        print("-" * 60)
        smm_strategies = self._run_smm(question, qhm_facts)
        print(f"✓ Generated and validated {len(smm_strategies)} strategies")

        # Phase 3: Response Merging
        print("\nPhase 3: Response Merging")
        print("-" * 60)
        final_response = self._merge_response(question, qhm_facts, smm_strategies)
        print("✓ Final response generated")

        # Add metadata
        final_response['processing_time'] = time.time() - start_time
        final_response['question'] = question
        final_response['location'] = location

        # Cache response
        if self.cache is not None:
            self._cache_response(cache_key, final_response)

        print(f"\n{'='*60}")
        print(f"Processing completed in {final_response['processing_time']:.2f}s")
        print(f"{'='*60}\n")

        return final_response

    def _run_qhm(self,
                question: str,
                location: Optional[str],
                user_context: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Run Question Handling Module

        Args:
            question: User's question
            location: Location filter
            user_context: Additional context

        Returns:
            List of retrieved facts
        """
        all_facts = []

        # Stage 1: SQL-based RAG
        print("  Stage 1: SQL-based RAG")
        filters = {'location': location} if location else None
        sql_facts = self.sql_retriever.retrieve_facts(question, filters)
        print(f"    - Retrieved {len(sql_facts)} facts from database")
        all_facts.extend(sql_facts)

        # Stage 2: Curated Web Search (if enabled)
        if self.config.get('qhm.enable_web_search', True):
            print("  Stage 2: Curated Web Search")
            web_facts = self.web_search.search(question, filters)
            print(f"    - Retrieved {len(web_facts)} facts from web")
            all_facts.extend(web_facts)

        return all_facts

    def _run_smm(self,
                question: str,
                qhm_facts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Run Strategy Maintenance Module

        Args:
            question: User's question
            qhm_facts: Facts from QHM

        Returns:
            List of validated strategies
        """
        # Stage 1: LLM Generation
        print("  Stage 1: LLM Strategy Generation")
        llm_output = self.strategy_generator.generate_strategies(question, qhm_facts)
        print("    - Generated strategies from LLM")

        # Stage 2: Strategy Extraction
        print("  Stage 2: Strategy Extraction")
        extracted_strategies = self.strategy_extractor.extract_strategies(llm_output)
        print(f"    - Extracted {len(extracted_strategies)} strategies")

        # Stage 3: Fact-Check & IR
        print("  Stage 3: Fact-Check & Information Retrieval")
        validated_strategies = self.fact_checker.validate_and_enhance_strategies(
            extracted_strategies,
            qhm_facts
        )
        print(f"    - Validated {len(validated_strategies)} strategies")

        # Rank by evidence strength
        ranked_strategies = self.fact_checker.rank_strategies_by_evidence(validated_strategies)

        return ranked_strategies

    def _merge_response(self,
                       question: str,
                       qhm_facts: List[Dict[str, Any]],
                       smm_strategies: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Merge QHM facts and SMM strategies into final response

        Args:
            question: User's question
            qhm_facts: Facts from QHM
            smm_strategies: Strategies from SMM

        Returns:
            Final response dictionary
        """
        print("  Merging facts and strategies...")
        response = self.response_merger.merge(question, qhm_facts, smm_strategies)
        return response

    def _generate_cache_key(self, question: str, location: Optional[str]) -> str:
        """Generate cache key for question"""
        key_data = f"{question}|{location or ''}"
        return hashlib.md5(key_data.encode()).hexdigest()

    def _get_cached_response(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get cached response if available and not expired"""
        if cache_key in self.cache:
            cached_data = self.cache[cache_key]
            if time.time() - cached_data['timestamp'] < self.cache_ttl:
                return cached_data['response']
            else:
                # Expired, remove from cache
                del self.cache[cache_key]
        return None

    def _cache_response(self, cache_key: str, response: Dict[str, Any]):
        """Cache response"""
        self.cache[cache_key] = {
            'response': response,
            'timestamp': time.time()
        }

    def get_stats(self) -> Dict[str, Any]:
        """Get chatbot statistics"""
        return {
            'cache_size': len(self.cache) if self.cache else 0,
            'config': self.config.to_dict()
        }

    def clear_cache(self):
        """Clear response cache"""
        if self.cache:
            self.cache.clear()
            print("✓ Cache cleared")


class DebugPipeline(WaterTrustChatbot):
    """Extended pipeline with detailed debugging information"""

    def answer_question(self,
                       question: str,
                       location: Optional[str] = None,
                       user_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Answer question with detailed debugging info"""
        response = super().answer_question(question, location, user_context)

        # Add debugging information
        response['debug'] = {
            'qhm_facts_details': response.get('facts_referenced', []),
            'smm_strategies_details': response.get('strategies_used', []),
            'config_snapshot': self.config.to_dict()
        }

        return response

    def export_pipeline_state(self, filepath: str):
        """Export current pipeline state for debugging"""
        state = {
            'config': self.config.to_dict(),
            'stats': self.get_stats(),
            'timestamp': time.time()
        }

        with open(filepath, 'w') as f:
            json.dump(state, f, indent=2)

        print(f"✓ Pipeline state exported to {filepath}")


def create_chatbot(config_path: Optional[str] = None, debug: bool = False) -> WaterTrustChatbot:
    """
    Factory function to create chatbot instance

    Args:
        config_path: Path to configuration file
        debug: Whether to create debug-enabled pipeline

    Returns:
        WaterTrustChatbot instance
    """
    if debug:
        return DebugPipeline(config_path)
    else:
        return WaterTrustChatbot(config_path)
