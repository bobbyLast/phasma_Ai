"""
Phasma AI - Engines Module
Trading engines and analysis components
"""

import importlib.util
import os

# Import from the new modular news engine
try:
    from .news_engine_core import NewsAPIIntegration
    print("[OK] Successfully loaded NewsAPIIntegration from modular news engine")
except ImportError as e:
    print(f"[ERROR] Failed to load modular news engine: {e}")
    raise ImportError("Could not load NewsAPIIntegration from modular news engine")

# Import new engines
try:
    from .risk_engine import PhasmaRiskEngine
    print("[OK] Successfully loaded PhasmaRiskEngine")
except ImportError as e:
    print(f"[WARN] Failed to load risk engine: {e}")

try:
    from .market_regime import PhasmaMarketRegimeDetector
    print("[OK] Successfully loaded PhasmaMarketRegimeDetector")
except ImportError as e:
    print(f"[WARN] Failed to load market regime detector: {e}")

__all__ = [
    'NewsAPIIntegration',
    'PhasmaRiskEngine',
    'PhasmaMarketRegimeDetector'
]
