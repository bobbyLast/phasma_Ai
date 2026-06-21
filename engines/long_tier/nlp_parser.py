"""
NLP Event Parser
Analyzes news sentiment, event types, and market impact.

EnrichmentGroup — produces EventAnalysis metadata for candidates.
Does not approve trades; final decisions use DecisionGroup / SignalDecision.
"""

from dataclasses import dataclass
from enum import Enum, auto
from typing import Dict, List, Optional, Tuple
import re
import spacy
from datetime import datetime
import logging

class EventType(Enum):
    PARTNERSHIP = auto()
    EARNINGS = auto()
    PRODUCT_LAUNCH = auto()
    REGULATORY = auto()
    MANAGEMENT_CHANGE = auto()
    FINANCING = auto()
    MERGER_ACQUISITION = auto()
    OTHER = auto()

class Sentiment(Enum):
    STRONGLY_POSITIVE = 2
    POSITIVE = 1
    NEUTRAL = 0
    NEGATIVE = -1
    STRONGLY_NEGATIVE = -2

class Certainty(Enum):
    CONFIRMED = 3    # Official announcement
    LIKELY = 2       # Credible source, not officially confirmed
    SPECULATIVE = 1  # Rumors or unverified sources
    UNKNOWN = 0      # Can't determine

@dataclass
class EventAnalysis:
    event_type: EventType
    sentiment: Sentiment
    certainty: Certainty
    key_entities: List[Dict[str, str]]
    impact_score: float  # 0-10 scale
    is_structural: bool  # If true, indicates a structural change (not temporary)
    price_reaction: Optional[float] = None  # Immediate price reaction if available
    summary: Optional[str] = None
    raw_text: Optional[str] = None

class NLPEventParser:
    """
    Analyzes news and events using NLP to determine sentiment, event type, and market impact
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.nlp = self._load_nlp_model()
        
        # Keywords and patterns for event type detection
        self.event_patterns = {
            EventType.PARTNERSHIP: [
                r'partner(?:ship|ed|ing)', 'collaborat', 'joint venture', 'teaming', 
                'alliance', 'strategic agreement', 'distribution deal', 'licensing',
                'reseller', 'supply agreement', 'co-develop', 'co-market', 'teams? up with'
            ],
            EventType.EARNINGS: [
                'earnings', 'financial results', 'revenue', 'EPS', 'profit', 'loss',
                'beats estimates', 'misses estimates', 'quarterly report', 'Q[1-4]',
                'FY\d{2}', 'fiscal year', 'guidance'
            ],
            EventType.PRODUCT_LAUNCH: [
                'launch', 'announce', 'release', 'unveil', 'introduce', 'new product',
                'coming soon', 'preview', 'beta', 'early access', 'now available'
            ],
            EventType.REGULATORY: [
                'FDA', 'approval', 'rejection', 'clinical trial', 'phase [1-4]',
                'SEC', 'investigation', 'lawsuit', 'settlement', 'regulation',
                'compliance', 'warning letter', 'submission', 'NDA', 'BLA'
            ],
            EventType.MANAGEMENT_CHANGE: [
                'CEO', 'CFO', 'CTO', 'appoint', 'resign', 'step down', 'retire',
                'transition', 'new hire', 'leadership change', 'interim', 'promote'
            ],
            EventType.FINANCING: [
                'raise', 'funding', 'financing', 'investment', 'series [A-Z]',
                'capital', 'debt', 'offering', 'shares', 'dilution', 'convertible',
                'private placement', 'public offering'
            ],
            EventType.MERGER_ACQUISITION: [
                'acquire', 'merger', 'takeover', 'buyout', 'purchase', 'deal',
                'buy', 'sell', 'divest', 'spin-off', 'spinout', 'acquisition',
                'strategic alternatives', 'exploring options'
            ]
        }
        
        # Sentiment indicators
        self.positive_indicators = [
            'strong', 'growth', 'increase', 'surge', 'jump', 'soar', 'rally',
            'beat', 'exceed', 'outperform', 'upgrade', 'bullish', 'positive',
            'profit', 'gain', 'success', 'breakthrough', 'innovative', 'leading',
            'record', 'milestone', 'expansion', 'partnership', 'collaboration'
        ]
        
        self.negative_indicators = [
            'decline', 'drop', 'plunge', 'fall', 'downgrade', 'bearish', 'negative',
            'loss', 'miss', 'below', 'weak', 'concern', 'risk', 'challenge',
            'delay', 'cut', 'reduce', 'layoff', 'downsize', 'bankruptcy', 'default',
            'investigation', 'lawsuit', 'recall', 'rejection', 'failure'
        ]
        
        # Certainty indicators
        self.certainty_indicators = {
            'confirm': 3, 'announce': 3, 'report': 3, 'file': 3,
            'suggest': 2, 'indicate': 2, 'likely': 2, 'probable': 2,
            'rumor': 1, 'speculate': 1, 'potential': 1, 'may': 1, 'could': 1
        }
        
        # Structural change indicators (permanent or long-term impact)
        self.structural_indicators = [
            'acquisition', 'merger', 'bankruptcy', 'restructuring', 'pivot',
            'discontinue', 'exit', 'strategic review', 'sale', 'shutdown',
            'recall', 'approval', 'rejection', 'ban', 'regulation', 'lawsuit'
        ]
    
    def _load_nlp_model(self):
        """Load the NLP model"""
        try:
            # Try to load the large model for better accuracy
            return spacy.load("en_core_web_lg")
        except OSError:
            try:
                # Fall back to medium model
                return spacy.load("en_core_web_md")
            except OSError:
                # Fall back to small model
                return spacy.load("en_core_web_sm")
    
    def analyze_text(self, text: str) -> EventAnalysis:
        """
        Analyze a news article or text for events and sentiment
        
        Args:
            text: The text to analyze
            
        Returns:
            EventAnalysis object with analysis results
        """
        if not text or not text.strip():
            return EventAnalysis(
                event_type=EventType.OTHER,
                sentiment=Sentiment.NEUTRAL,
                certainty=Certainty.UNKNOWN,
                key_entities=[],
                impact_score=0.0,
                is_structural=False
            )
        
        # Process text with spaCy
        doc = self.nlp(text)
        
        # Extract key entities
        entities = [
            {"text": ent.text, "label": ent.label_, "start": ent.start_char, "end": ent.end_char}
            for ent in doc.ents
        ]
        
        # Determine event type
        event_type = self._detect_event_type(text)
        
        # Analyze sentiment
        sentiment = self._analyze_sentiment(text)
        
        # Determine certainty
        certainty = self._determine_certainty(text)
        
        # Check for structural changes
        is_structural = self._is_structural_change(text, event_type)
        
        # Calculate impact score (0-10)
        impact_score = self._calculate_impact_score(event_type, sentiment, certainty, is_structural)
        
        # Generate a summary
        summary = self._generate_summary(text, event_type, sentiment, certainty)
        
        return EventAnalysis(
            event_type=event_type,
            sentiment=sentiment,
            certainty=certainty,
            key_entities=entities,
            impact_score=impact_score,
            is_structural=is_structural,
            summary=summary,
            raw_text=text
        )
    
    def _detect_event_type(self, text: str) -> EventType:
        """Detect the type of event described in the text"""
        text_lower = text.lower()
        
        # Check each event type's patterns
        for event_type, patterns in self.event_patterns.items():
            for pattern in patterns:
                if re.search(r'\b' + re.escape(pattern) + r'\b', text_lower):
                    return event_type
        
        return EventType.OTHER
    
    def _analyze_sentiment(self, text: str) -> Sentiment:
        """Analyze the sentiment of the text"""
        positive_count = sum(1 for word in self.positive_indicators if word in text.lower())
        negative_count = sum(1 for word in self.negative_indicators if word in text.lower())
        
        sentiment_score = positive_count - negative_count
        
        if sentiment_score >= 3:
            return Sentiment.STRONGLY_POSITIVE
        elif sentiment_score >= 1:
            return Sentiment.POSITIVE
        elif sentiment_score <= -3:
            return Sentiment.STRONGLY_NEGATIVE
        elif sentiment_score <= -1:
            return Sentiment.NEGATIVE
        else:
            return Sentiment.NEUTRAL
    
    def _determine_certainty(self, text: str) -> Certainty:
        """Determine the certainty level of the information"""
        text_lower = text.lower()
        
        # Check for certainty indicators
        certainty_scores = []
        for indicator, score in self.certainty_indicators.items():
            if indicator in text_lower:
                certainty_scores.append(score)
        
        # Default to UNKNOWN if no indicators found
        if not certainty_scores:
            return Certainty.UNKNOWN
        
        # Return the highest certainty level found
        max_score = max(certainty_scores)
        return Certainty(max_score)
    
    def _is_structural_change(self, text: str, event_type: EventType) -> bool:
        """Determine if the event represents a structural change"""
        # Some event types are always structural
        if event_type in [EventType.MERGER_ACQUISITION, EventType.REGULATORY, 
                         EventType.MANAGEMENT_CHANGE, EventType.FINANCING]:
            return True
        
        # Check for structural indicators in text
        text_lower = text.lower()
        return any(indicator in text_lower for indicator in self.structural_indicators)
    
    def _calculate_impact_score(self, event_type: EventType, sentiment: Sentiment, 
                              certainty: Certainty, is_structural: bool) -> float:
        """Calculate an impact score from 0-10"""
        # Base score based on event type
        event_weights = {
            EventType.MERGER_ACQUISITION: 8.0,
            EventType.REGULATORY: 7.0,
            EventType.PARTNERSHIP: 6.0,
            EventType.PRODUCT_LAUNCH: 5.0,
            EventType.EARNINGS: 4.0,
            EventType.MANAGEMENT_CHANGE: 3.0,
            EventType.FINANCING: 3.0,
            EventType.OTHER: 1.0
        }
        
        # Sentiment multiplier (negative events often have larger impact)
        sentiment_multiplier = {
            Sentiment.STRONGLY_POSITIVE: 1.2,
            Sentiment.POSITIVE: 1.0,
            Sentiment.NEUTRAL: 0.5,
            Sentiment.NEGATIVE: 1.5,
            Sentiment.STRONGLY_NEGATIVE: 2.0
        }
        
        # Certainty adjustment
        certainty_multiplier = {
            Certainty.CONFIRMED: 1.0,
            Certainty.LIKELY: 0.7,
            Certainty.SPECULATIVE: 0.4,
            Certainty.UNKNOWN: 0.2
        }
        
        # Calculate base score
        base_score = event_weights.get(event_type, 1.0)
        
        # Apply multipliers
        score = base_score * sentiment_multiplier.get(sentiment, 1.0)
        score = score * certainty_multiplier.get(certainty, 0.5)
        
        # Boost for structural changes
        if is_structural:
            score = min(10.0, score * 1.3)
        
        return round(min(10.0, max(0.0, score)), 1)
    
    def _generate_summary(self, text: str, event_type: EventType, 
                         sentiment: Sentiment, certainty: Certainty) -> str:
        """Generate a human-readable summary of the analysis"""
        # Get event type name
        event_name = event_type.name.replace('_', ' ').title()
        
        # Get sentiment description
        sentiment_map = {
            Sentiment.STRONGLY_POSITIVE: "strongly positive",
            Sentiment.POSITIVE: "positive",
            Sentiment.NEUTRAL: "neutral",
            Sentiment.NEGATIVE: "negative",
            Sentiment.STRONGLY_NEGATIVE: "strongly negative"
        }
        sentiment_desc = sentiment_map.get(sentiment, "neutral")
        
        # Get certainty description
        certainty_map = {
            Certainty.CONFIRMED: "confirmed",
            Certainty.LIKELY: "likely",
            Certainty.SPECULATIVE: "speculative",
            Certainty.UNKNOWN: "uncertain"
        }
        certainty_desc = certainty_map.get(certainty, "uncertain")
        
        # Generate summary
        summary = (
            f"Event Type: {event_name}\n"
            f"Sentiment: {sentiment_desc.capitalize()}\n"
            f"Certainty: {certainty_desc.capitalize()}"
        )
        
        return summary
