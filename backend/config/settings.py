"""
Configuration loading module
"""
from .agent_config import get_config

# Export main configuration (lazy loading)
config = get_config()