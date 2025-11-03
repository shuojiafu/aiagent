"""
Unit Tests for Water Trust Chatbot Pipeline
"""

import sys
import os
import pytest

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.pipeline import WaterTrustChatbot, create_chatbot
from src.config import Config
from src.utils.database import setup_database
from src.modules.smm.strategy_extraction import StrategyExtractor
from src.modules.smm.llm_generation import LLMStrategyGenerator
from src.utils.llm_client import MockLLMClient


class TestConfig:
    """Test configuration management"""

    def test_default_config(self):
        config = Config()
        assert config.get('llm.provider') == 'mock'
        assert config.get('database.top_k') == 5

    def test_config_get(self):
        config = Config()
        assert config.get('llm.temperature') == 0.7
        assert config.get('nonexistent.key', 'default') == 'default'

    def test_config_set(self):
        config = Config()
        config.set('custom.key', 'value')
        assert config.get('custom.key') == 'value'


class TestDatabase:
    """Test database operations"""

    def test_database_setup(self):
        db_path = '/tmp/test_water.db'
        if os.path.exists(db_path):
            os.remove(db_path)

        db = setup_database(db_path, add_samples=True)
        assert os.path.exists(db_path)

        # Test search
        results = db.search('chlorine', limit=3)
        assert len(results) > 0
        assert 'content' in results[0]

        db.close()
        os.remove(db_path)


class TestStrategyExtraction:
    """Test strategy extraction"""

    def test_extract_json_strategies(self):
        extractor = StrategyExtractor({'min_strategies': 1, 'max_strategies': 5})

        llm_output = """
        [
            {
                "strategy_type": "Evidence-Based",
                "key_message": "Water is safe",
                "supporting_evidence": "EPA tests regularly",
                "delivery_approach": "Present facts",
                "trust_elements": ["EPA oversight"]
            }
        ]
        """

        strategies = extractor.extract_strategies(llm_output)
        assert len(strategies) > 0
        assert strategies[0]['strategy_type'] == 'Evidence-Based'

    def test_extract_pattern_based(self):
        extractor = StrategyExtractor({'min_strategies': 1, 'max_strategies': 5})

        llm_output = """
        Strategy 1: Authority Appeal
        Key Message: EPA ensures water safety
        Supporting Evidence: Regular testing required
        Delivery Approach: Cite EPA standards
        Trust-Building Elements: Government oversight
        """

        strategies = extractor.extract_strategies(llm_output)
        assert len(strategies) > 0


class TestLLMGeneration:
    """Test LLM strategy generation"""

    def test_strategy_generation(self):
        llm_client = MockLLMClient()
        config = {'temperature': 0.7, 'max_tokens': 1000}
        generator = LLMStrategyGenerator(llm_client, config)

        question = "Is tap water safe?"
        facts = [{'content': 'EPA regulates tap water', 'source': 'EPA'}]

        output = generator.generate_strategies(question, facts)
        assert len(output) > 0
        assert 'strategy' in output.lower()


class TestPipeline:
    """Test main pipeline"""

    def test_create_chatbot(self):
        chatbot = create_chatbot()
        assert isinstance(chatbot, WaterTrustChatbot)

    def test_answer_question(self):
        chatbot = create_chatbot()
        response = chatbot.answer_question("Is my water safe?")

        assert 'answer' in response
        assert 'confidence' in response
        assert 'processing_time' in response
        assert isinstance(response['answer'], str)
        assert len(response['answer']) > 0

    def test_caching(self):
        chatbot = create_chatbot()

        question = "Is chlorine safe?"

        # First call
        response1 = chatbot.answer_question(question)
        time1 = response1['processing_time']

        # Second call (should be cached)
        response2 = chatbot.answer_question(question)
        time2 = response2['processing_time']

        # Cached response should be faster or equal
        assert time2 <= time1

    def test_location_specific(self):
        chatbot = create_chatbot()
        response = chatbot.answer_question(
            "What's in my water?",
            location="TestCity"
        )

        assert response['location'] == "TestCity"

    def test_clear_cache(self):
        chatbot = create_chatbot()
        chatbot.answer_question("Test question")

        stats_before = chatbot.get_stats()
        assert stats_before['cache_size'] > 0

        chatbot.clear_cache()

        stats_after = chatbot.get_stats()
        assert stats_after['cache_size'] == 0


class TestIntegration:
    """Integration tests"""

    def test_full_pipeline(self):
        """Test complete pipeline flow"""
        chatbot = create_chatbot()

        questions = [
            "Is my tap water safe to drink?",
            "Why does my water taste like chlorine?",
            "What contaminants are tested?"
        ]

        for question in questions:
            response = chatbot.answer_question(question)

            # Verify response structure
            assert 'answer' in response
            assert 'confidence' in response
            assert 'sources' in response
            assert 'processing_time' in response

            # Verify content
            assert len(response['answer']) > 50
            assert 0 <= response['confidence'] <= 1

    def test_debug_pipeline(self):
        """Test debug mode pipeline"""
        chatbot = create_chatbot(debug=True)
        response = chatbot.answer_question("Is water safe?")

        assert 'debug' in response
        assert 'qhm_facts_details' in response['debug']
        assert 'smm_strategies_details' in response['debug']


def run_tests():
    """Run all tests"""
    pytest.main([__file__, '-v'])


if __name__ == "__main__":
    run_tests()
