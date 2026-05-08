"""Configuration for the Partnership Engine"""
from typing import Dict, Any
import os

class PartnershipConfig:
    """Configuration settings for partnership detection"""
    
    # API Endpoints
    EDGAR_API = {
        'base_url': 'https://data.sec.gov/submissions/',
        'rate_limit': 10,  # requests per second
        'user_agent': 'phasma_ai (your-email@example.com)'  # SEC requires this
    }
    
    USASPENDING_API = {
        'base_url': 'https://api.usaspending.gov/api/v2/',
        'rate_limit': 5,
        'timeout': 30
    }
    
    SAM_GOV_API = {
        'base_url': 'https://api.sam.gov/opportunities/v2/',
        'api_key': os.getenv('SAM_GOV_API_KEY', ''),
        'rate_limit': 2
    }
    
    # Detection thresholds
    MIN_CONFIDENCE = 0.7
    MIN_IMPACT_SCORE = 7.0
    
    # Entity resolution
    FUZZY_MATCH_THRESHOLD = 0.85
    
    @classmethod
    def update_from_dict(cls, config_dict: Dict[str, Any]):
        """Update config from dictionary"""
        for key, value in config_dict.items():
            if hasattr(cls, key):
                if isinstance(getattr(cls, key), dict) and isinstance(value, dict):
                    getattr(cls, key).update(value)
                else:
                    setattr(cls, key, value)
