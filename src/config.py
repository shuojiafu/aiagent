"""
Configuration Management
Loads and manages system configuration
"""

import yaml
from typing import Dict, Any
import os


class Config:
    """Configuration manager for the water trust chatbot"""

    def __init__(self, config_path: str = None):
        """
        Initialize configuration

        Args:
            config_path: Path to YAML config file
        """
        self.config_path = config_path
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file or use defaults"""
        if self.config_path and os.path.exists(self.config_path):
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f)
        else:
            return self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            'llm': {
                'provider': 'mock',  # 'openai', 'anthropic', or 'mock'
                'model': 'gpt-4',
                'temperature': 0.7,
                'max_tokens': 2000,
                'primary_model': 'gpt-4'
            },
            'database': {
                'path': 'data/water_facts.db',
                'top_k': 5
            },
            'web_search': {
                'enable': True,
                'max_results': 3,
                'trusted_domains': [
                    'epa.gov',
                    'cdc.gov',
                    'who.int',
                    'awwa.org',
                    'water.usgs.gov',
                    'waterrf.org'
                ]
            },
            'smm': {
                'min_strategies': 1,
                'max_strategies': 5,
                'fact_check_threshold': 0.7,
                'enable_web_enhancement': False
            },
            'qhm': {
                'enable_web_search': True
            },
            'merger': {
                'max_strategies_in_response': 3,
                'response_style': 'balanced'  # 'factual', 'persuasive', or 'balanced'
            },
            'pipeline': {
                'enable_caching': True,
                'cache_ttl': 3600  # seconds
            }
        }

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value

        Args:
            key: Dot-separated key path (e.g., 'llm.temperature')
            default: Default value if key not found

        Returns:
            Configuration value
        """
        keys = key.split('.')
        value = self.config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def set(self, key: str, value: Any):
        """
        Set configuration value

        Args:
            key: Dot-separated key path
            value: Value to set
        """
        keys = key.split('.')
        config = self.config

        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        config[keys[-1]] = value

    def save(self, path: str = None):
        """
        Save configuration to file

        Args:
            path: Path to save to (uses self.config_path if not provided)
        """
        save_path = path or self.config_path
        if not save_path:
            raise ValueError("No path specified for saving config")

        with open(save_path, 'w') as f:
            yaml.dump(self.config, f, default_flow_style=False)

    def to_dict(self) -> Dict[str, Any]:
        """Get configuration as dictionary"""
        return self.config.copy()


def load_config(config_path: str = None) -> Config:
    """
    Load configuration

    Args:
        config_path: Path to config file (optional)

    Returns:
        Config object
    """
    return Config(config_path)
