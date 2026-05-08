"""
Phasma AI Brain Module

This module contains all the core AI thinking and decision-making components.
The brain is responsible for:
- Meta-reasoning and signal arbitration
- Market intelligence and analysis
- Signal convergence and synthesis
- Thematic analysis and trend identification

All AI thinking logic is centralized here for clarity and maintainability.
"""

# Core brain components
from .meta_brain import PhasmaMetaBrain, Signal
from .signal_convergence_engine import SignalConvergenceEngine
from .market_intelligence_engine import MarketIntelligenceEngine
from .thematic_analysis_engine import ThematicAnalyzer

__all__ = [
    'PhasmaMetaBrain',
    'Signal',
    'SignalConvergenceEngine',
    'MarketIntelligenceEngine',
    'ThematicAnalyzer'
]
