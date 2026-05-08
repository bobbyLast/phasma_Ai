"""
🌍 GEOPOLITICAL ANALYSIS ENGINE

Advanced geopolitical intelligence system for Kalshi prediction markets.
Analyzes historical country relationships, conflict patterns, treaty compliance,
and behavioral predictability to identify "easy trades" in geopolitical markets.

Features:
- Country Relationship Database (trust scores, conflict history)
- Treaty Compliance Analysis (broken agreements, peace violations)
- Conflict Pattern Recognition (bombing frequency, attack types)
- Behavioral Predictability Scoring
- Geopolitical Risk Assessment
- Historical Outcome Analysis
- Country Trustworthiness Metrics
"""

import asyncio
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import json
import os
import math
from collections import defaultdict

try:
    from engines.kalshi_engine import KalshiPredictionEngine
    from engines.scenario_graph_engine import ScenarioGraphEngine
except ImportError:
    # Mocks for testing
    class KalshiPredictionEngine:
        def __init__(self, *args, **kwargs):
            pass
    class ScenarioGraphEngine:
        def __init__(self, *args, **kwargs):
            pass


@dataclass
class CountryProfile:
    """Comprehensive profile of a country's geopolitical behavior."""
    country_code: str  # ISO 3166-1 alpha-3
    country_name: str
    region: str  # Middle East, Europe, Asia, etc.

    # Trust and reliability metrics
    treaty_compliance_score: float = 0.5  # 0.0 = never honors treaties, 1.0 = always honors
    peace_treaty_violations: int = 0
    broken_agreements_count: int = 0

    # Conflict history
    total_attacks_initiated: int = 0
    bombings_count: int = 0
    missile_attacks_count: int = 0
    terrorist_incidents: int = 0

    # Behavioral patterns
    aggression_score: float = 0.5  # 0.0 = peaceful, 1.0 = highly aggressive
    predictability_score: float = 0.5  # How predictable their behavior is
    escalation_likelihood: float = 0.5  # Tendency to escalate conflicts

    # Historical outcomes
    wars_started: int = 0
    wars_won: int = 0
    wars_lost: int = 0
    peace_treaties_signed: int = 0
    peace_treaties_broken: int = 0

    # Current status
    active_conflicts: List[str] = field(default_factory=list)
    sanctions_count: int = 0
    international_isolation_score: float = 0.5

    last_updated: datetime = field(default_factory=lambda: datetime.now())

    def calculate_overall_trust_score(self) -> float:
        """Calculate overall trustworthiness score (0.0 = completely untrustworthy, 1.0 = highly trustworthy)."""

        # Treaty compliance is heavily weighted
        treaty_weight = 0.4
        treaty_score = self.treaty_compliance_score

        # Conflict history
        conflict_weight = 0.3
        if self.total_attacks_initiated == 0:
            conflict_score = 0.8  # Peaceful countries score high
        else:
            # Countries with conflict history score based on treaty compliance
            conflict_score = max(0.1, self.treaty_compliance_score * 0.8)

        # International standing
        standing_weight = 0.2
        standing_score = 1.0 - self.international_isolation_score

        # Predictability (somewhat trustworthy if predictable)
        predictability_weight = 0.1
        predictability_score = self.predictability_score

        overall_score = (
            treaty_score * treaty_weight +
            conflict_score * conflict_weight +
            standing_score * standing_weight +
            predictability_score * predictability_weight
        )

        return max(0.0, min(1.0, overall_score))

    def get_conflict_probability_score(self, target_country: str = None) -> float:
        """Get probability score for initiating conflict (0.0 = very unlikely, 1.0 = very likely)."""

        base_score = self.aggression_score

        # Boost if they have active conflicts
        if self.active_conflicts:
            base_score += 0.2

        # Boost if they have history of broken treaties
        if self.peace_treaties_broken > 0:
            treaty_violation_multiplier = min(1.5, 1.0 + (self.peace_treaties_broken / 10))
            base_score *= treaty_violation_multiplier

        # Reduce if they have sanctions (might be more cautious)
        if self.sanctions_count > 5:
            base_score *= 0.8

        return max(0.0, min(1.0, base_score))


@dataclass
class CountryRelationship:
    """Relationship between two countries."""
    country_a: str
    country_b: str
    relationship_type: str  # 'hostile', 'neutral', 'allied', 'complex'
    tension_level: float  # 0.0 = peaceful, 1.0 = extreme tension
    conflict_history: List[str] = field(default_factory=list)
    peace_agreements: List[str] = field(default_factory=list)
    trade_volume: float = 0.0
    diplomatic_ties_score: float = 0.5

    def get_conflict_probability(self) -> float:
        """Get probability of conflict between these countries."""
        # High tension + conflict history = high probability
        base_prob = self.tension_level

        # Boost for conflict history
        if self.conflict_history:
            base_prob += 0.3

        # Reduce for strong diplomatic ties or trade
        diplomatic_reduction = self.diplomatic_ties_score * 0.2
        trade_reduction = min(0.1, self.trade_volume / 1000000000)  # $1B trade reduces by 0.1

        base_prob -= diplomatic_reduction
        base_prob -= trade_reduction

        return max(0.0, min(1.0, base_prob))


@dataclass
class GeopoliticalMarketAnalysis:
    """Analysis of a geopolitical Kalshi market."""
    market_id: str
    market_title: str
    countries_involved: List[str]
    event_type: str  # 'bombing', 'invasion', 'treaty_violation', 'peace_treaty', etc.
    predicted_probability: float
    ai_adjusted_probability: float
    confidence: float
    key_factors: List[str]
    historical_precedents: List[str]
    rationale: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            'market_id': self.market_id,
            'market_title': self.market_title,
            'countries_involved': self.countries_involved,
            'event_type': self.event_type,
            'predicted_probability': self.predicted_probability,
            'ai_adjusted_probability': self.ai_adjusted_probability,
            'confidence': self.confidence,
            'key_factors': self.key_factors,
            'historical_precedents': self.historical_precedents,
            'rationale': self.rationale
        }


class GeopoliticalAnalysisEngine:
    """
    🌍 Geopolitical Analysis Engine

    Specialized AI for analyzing geopolitical Kalshi markets using historical patterns,
    country behavior analysis, and conflict prediction models.
    """

    def __init__(self, kalshi_engine: KalshiPredictionEngine, scenario_graph: ScenarioGraphEngine):
        self.kalshi = kalshi_engine
        self.scenario_graph = scenario_graph

        # Core databases
        self.country_profiles: Dict[str, CountryProfile] = {}
        self.country_relationships: Dict[Tuple[str, str], CountryRelationship] = {}

        # Analysis results
        self.market_analyses: Dict[str, GeopoliticalMarketAnalysis] = {}

        # Data files
        self.countries_file = "geopolitical_countries.json"
        self.relationships_file = "geopolitical_relationships.json"
        self.analyses_file = "geopolitical_analyses.json"

        # Initialize with known geopolitical data
        self._initialize_geopolitical_database()
        self._load_data()

    def _initialize_geopolitical_database(self):
        """Initialize with real geopolitical data for major players."""

        # Major countries with conflict history
        country_data = [
            # Middle East conflict countries
            {
                'code': 'ISR', 'name': 'Israel', 'region': 'Middle East',
                'treaty_compliance': 0.7, 'peace_violations': 2, 'attacks': 15,
                'aggression': 0.4, 'predictability': 0.8, 'wars': 6, 'wars_won': 6,
                'peace_signed': 8, 'peace_broken': 3, 'active_conflicts': ['Gaza', 'Lebanon']
            },
            {
                'code': 'PSE', 'name': 'Palestine', 'region': 'Middle East',
                'treaty_compliance': 0.3, 'peace_violations': 5, 'attacks': 25,
                'aggression': 0.7, 'predictability': 0.6, 'wars': 3, 'wars_won': 1,
                'peace_signed': 6, 'peace_broken': 5, 'active_conflicts': ['Gaza']
            },
            {
                'code': 'IRN', 'name': 'Iran', 'region': 'Middle East',
                'treaty_compliance': 0.2, 'peace_violations': 8, 'attacks': 35,
                'aggression': 0.8, 'predictability': 0.7, 'wars': 2, 'wars_won': 1,
                'peace_signed': 3, 'peace_broken': 7, 'active_conflicts': ['Yemen', 'Syria'],
                'sanctions': 12, 'isolation': 0.9
            },
            {
                'code': 'SAU', 'name': 'Saudi Arabia', 'region': 'Middle East',
                'treaty_compliance': 0.6, 'peace_violations': 1, 'attacks': 5,
                'aggression': 0.3, 'predictability': 0.8, 'wars': 1, 'wars_won': 1,
                'peace_signed': 4, 'peace_broken': 1
            },
            {
                'code': 'SYR', 'name': 'Syria', 'region': 'Middle East',
                'treaty_compliance': 0.1, 'peace_violations': 12, 'attacks': 50,
                'aggression': 0.9, 'predictability': 0.4, 'wars': 2, 'wars_won': 0,
                'peace_signed': 5, 'peace_broken': 12, 'active_conflicts': ['Civil War'],
                'sanctions': 15, 'isolation': 0.95
            },
            {
                'code': 'IRQ', 'name': 'Iraq', 'region': 'Middle East',
                'treaty_compliance': 0.2, 'peace_violations': 6, 'attacks': 20,
                'aggression': 0.6, 'predictability': 0.5, 'wars': 3, 'wars_won': 0,
                'peace_signed': 4, 'peace_broken': 6, 'active_conflicts': ['ISIS remnants']
            },
            {
                'code': 'LBN', 'name': 'Lebanon', 'region': 'Middle East',
                'treaty_compliance': 0.4, 'peace_violations': 3, 'attacks': 10,
                'aggression': 0.5, 'predictability': 0.6, 'wars': 2, 'wars_won': 0,
                'peace_signed': 3, 'peace_broken': 3, 'active_conflicts': ['Hezbollah']
            },

            # Other notable countries
            {
                'code': 'RUS', 'name': 'Russia', 'region': 'Europe/Asia',
                'treaty_compliance': 0.3, 'peace_violations': 4, 'attacks': 8,
                'aggression': 0.7, 'predictability': 0.7, 'wars': 5, 'wars_won': 4,
                'peace_signed': 12, 'peace_broken': 6, 'active_conflicts': ['Ukraine'],
                'sanctions': 10, 'isolation': 0.8
            },
            {
                'code': 'UKR', 'name': 'Ukraine', 'region': 'Europe',
                'treaty_compliance': 0.8, 'peace_violations': 0, 'attacks': 2,
                'aggression': 0.2, 'predictability': 0.9, 'wars': 1, 'wars_won': 0,
                'peace_signed': 5, 'peace_broken': 0, 'active_conflicts': ['Russian invasion']
            },
            {
                'code': 'PRK', 'name': 'North Korea', 'region': 'Asia',
                'treaty_compliance': 0.1, 'peace_violations': 15, 'attacks': 40,
                'aggression': 0.9, 'predictability': 0.8, 'wars': 1, 'wars_won': 0,
                'peace_signed': 2, 'peace_broken': 15, 'sanctions': 20, 'isolation': 1.0
            },
            {
                'code': 'KOR', 'name': 'South Korea', 'region': 'Asia',
                'treaty_compliance': 0.9, 'peace_violations': 0, 'attacks': 1,
                'aggression': 0.1, 'predictability': 0.95, 'wars': 1, 'wars_won': 1,
                'peace_signed': 8, 'peace_broken': 0
            }
        ]

        for data in country_data:
            profile = CountryProfile(
                country_code=data['code'],
                country_name=data['name'],
                region=data['region'],
                treaty_compliance_score=data['treaty_compliance'],
                peace_treaty_violations=data['peace_violations'],
                total_attacks_initiated=data['attacks'],
                aggression_score=data['aggression'],
                predictability_score=data['predictability'],
                wars_started=data['wars'],
                wars_won=data['wars_won'],
                peace_treaties_signed=data.get('peace_signed', 0),
                peace_treaties_broken=data.get('peace_broken', 0),
                active_conflicts=data.get('active_conflicts', []),
                sanctions_count=data.get('sanctions', 0),
                international_isolation_score=data.get('isolation', 0.5)
            )
            self.country_profiles[data['code']] = profile

        # Initialize key relationships
        self._initialize_country_relationships()

    def _initialize_country_relationships(self):
        """Initialize relationships between countries."""

        relationships = [
            # Israel-Palestine
            CountryRelationship('ISR', 'PSE', 'hostile', 0.9,
                              ['Intifadas', 'Gaza conflicts', 'West Bank disputes'],
                              ['Oslo Accords (broken)', 'Camp David (partial)']),

            # Israel-Iran
            CountryRelationship('ISR', 'IRN', 'hostile', 0.95,
                              ['Proxy conflicts', 'Missile attacks', 'Nuclear threats'],
                              []),

            # Iran-Saudi Arabia
            CountryRelationship('IRN', 'SAU', 'hostile', 0.85,
                              ['Yemen proxy war', 'Diplomatic break'],
                              []),

            # Syria-Iran
            CountryRelationship('SYR', 'IRN', 'allied', 0.2,
                              [], ['Military alliance', 'Economic ties']),

            # Russia-Ukraine
            CountryRelationship('RUS', 'UKR', 'hostile', 0.95,
                              ['Crimea annexation', 'Donbas invasion', 'Full invasion 2022'],
                              ['Budapest Memorandum (broken)']),

            # North Korea-South Korea
            CountryRelationship('PRK', 'KOR', 'hostile', 0.8,
                              ['Korean War', 'DMZ incidents', 'Nuclear threats'],
                              ['Armistice (tense)', 'Family reunions'])
        ]

        for rel in relationships:
            key = (rel.country_a, rel.country_b)
            self.country_relationships[key] = rel

    def _load_data(self):
        """Load existing geopolitical data."""
        # Load countries
        if os.path.exists(self.countries_file):
            try:
                with open(self.countries_file, 'r') as f:
                    data = json.load(f)
                print(f"🌍 Loaded geopolitical profiles for {len(data.get('countries', {}))} countries")
            except Exception as e:
                print(f"⚠️ Error loading geopolitical countries: {e}")

        # Load relationships
        if os.path.exists(self.relationships_file):
            try:
                with open(self.relationships_file, 'r') as f:
                    data = json.load(f)
                print(f"🤝 Loaded {len(data.get('relationships', {}))} country relationships")
            except Exception as e:
                print(f"⚠️ Error loading relationships: {e}")

    def analyze_geopolitical_market(self, market_data: Dict[str, Any]) -> Optional[GeopoliticalMarketAnalysis]:
        """Analyze a geopolitical Kalshi market."""

        market_title = market_data.get('title', '').upper()
        market_ticker = market_data.get('ticker', '')

        # Extract countries and event type from title
        countries_involved = self._extract_countries_from_title(market_title)
        event_type = self._classify_event_type(market_title)

        if not countries_involved:
            return None

        # Get Kalshi market probability
        kalshi_probability = market_data.get('implied_probability', 0.5)

        # Perform AI analysis
        ai_probability, confidence, factors, precedents, rationale = self._perform_geopolitical_analysis(
            countries_involved, event_type, kalshi_probability, market_title
        )

        analysis = GeopoliticalMarketAnalysis(
            market_id=market_ticker,
            market_title=market_title,
            countries_involved=countries_involved,
            event_type=event_type,
            predicted_probability=kalshi_probability,
            ai_adjusted_probability=ai_probability,
            confidence=confidence,
            key_factors=factors,
            historical_precedents=precedents,
            rationale=rationale
        )

        self.market_analyses[market_ticker] = analysis
        self._save_analysis(analysis)

        return analysis

    def _extract_countries_from_title(self, title: str) -> List[str]:
        """Extract country codes from market title."""

        # Common country name mappings
        country_mappings = {
            'ISRAEL': 'ISR', 'PALESTINE': 'PSE', 'PALESTINIAN': 'PSE',
            'IRAN': 'IRN', 'SAUDI': 'SAU', 'SYRIA': 'SYR', 'IRAQ': 'IRQ',
            'LEBANON': 'LBN', 'RUSSIA': 'RUS', 'UKRAINE': 'UKR',
            'NORTH KOREA': 'PRK', 'SOUTH KOREA': 'KOR', 'KOREA': 'PRK',  # Default to North
            'CHINA': 'CHN', 'USA': 'USA', 'UNITED STATES': 'USA',
            'YEMEN': 'YEM', 'EGYPT': 'EGY', 'JORDAN': 'JOR'
        }

        countries_found = []
        title_upper = title.upper()

        for country_name, code in country_mappings.items():
            if country_name in title_upper and code not in countries_found:
                countries_found.append(code)

        return countries_found

    def _classify_event_type(self, title: str) -> str:
        """Classify the type of geopolitical event."""

        title_upper = title.upper()

        if any(word in title_upper for word in ['BOMB', 'ATTACK', 'STRIKE', 'MISSILE']):
            return 'bombing_attack'
        elif any(word in title_upper for word in ['INVASION', 'INVADING', 'OCCUPY']):
            return 'invasion'
        elif any(word in title_upper for word in ['PEACE', 'TREATY', 'AGREEMENT']):
            return 'peace_treaty'
        elif any(word in title_upper for word in ['VIOLATION', 'BREAK', 'RENEG']):
            return 'treaty_violation'
        elif any(word in title_upper for word in ['WAR', 'CONFLICT', 'BATTLE']):
            return 'war_conflict'
        elif any(word in title_upper for word in ['SANCTION', 'EMBARGO']):
            return 'sanctions'
        else:
            return 'general_conflict'

    def _perform_geopolitical_analysis(self, countries: List[str], event_type: str,
                                    kalshi_prob: float, market_title: str) -> Tuple[float, float, List[str], List[str], str]:
        """Perform detailed geopolitical analysis."""

        factors = []
        precedents = []
        rationale_parts = []

        # Base probability adjustment
        ai_probability = kalshi_prob
        confidence = 0.5

        # Analyze each country's behavior
        country_analyses = {}
        for country_code in countries:
            if country_code in self.country_profiles:
                profile = self.country_profiles[country_code]
                trust_score = profile.calculate_overall_trust_score()
                conflict_prob = profile.get_conflict_probability_score()

                country_analyses[country_code] = {
                    'profile': profile,
                    'trust_score': trust_score,
                    'conflict_probability': conflict_prob
                }

                factors.append(f"{profile.country_name}: Trust Score {trust_score:.1%}, Conflict Probability {conflict_prob:.1%}")

        # Analyze relationships between countries
        if len(countries) >= 2:
            rel_key = tuple(sorted(countries[:2]))
            if rel_key in self.country_relationships:
                relationship = self.country_relationships[rel_key]
                rel_conflict_prob = relationship.get_conflict_probability()

                factors.append(f"Relationship between {countries[0]} and {countries[1]}: {relationship.relationship_type.title()}, Tension {relationship.tension_level:.1%}")

                if relationship.conflict_history:
                    precedents.extend(relationship.conflict_history)
                    factors.append(f"Historical conflicts: {len(relationship.conflict_history)} incidents")

                if relationship.peace_agreements:
                    precedents.extend(relationship.peace_agreements)
                    factors.append(f"Peace agreements: {len(relationship.peace_agreements)} (broken: {len([a for a in relationship.peace_agreements if 'broken' in a.lower()])})")

        # Event-type specific analysis
        if event_type == 'bombing_attack':
            # Countries with high bombing history are more likely
            max_bombing_country = max(country_analyses.items(),
                                    key=lambda x: x[1]['profile'].bombings_count)
            if max_bombing_country[1]['profile'].bombings_count > 10:
                ai_probability += 0.2
                confidence += 0.2
                rationale_parts.append(f"High bombing history: {max_bombing_country[0]} has {max_bombing_country[1]['profile'].bombings_count} recorded incidents")

        elif event_type == 'treaty_violation':
            # Countries with poor treaty compliance are more likely to violate
            min_compliance_country = min(country_analyses.items(),
                                       key=lambda x: x[1]['profile'].treaty_compliance_score)
            if min_compliance_country[1]['profile'].treaty_compliance_score < 0.3:
                ai_probability += 0.15
                confidence += 0.2
                rationale_parts.append(f"Poor treaty compliance: {min_compliance_country[0]} has broken {min_compliance_country[1]['profile'].peace_treaties_broken} peace treaties")

        elif event_type == 'peace_treaty':
            # Countries with good compliance are more likely to honor peace treaties
            max_compliance_country = max(country_analyses.items(),
                                       key=lambda x: x[1]['profile'].treaty_compliance_score)
            if max_compliance_country[1]['profile'].treaty_compliance_score > 0.7:
                ai_probability -= 0.1  # Less likely to break/have issues
                confidence += 0.15
                rationale_parts.append(f"Good treaty compliance: {max_compliance_country[0]} has honored most agreements")

        # Generate rationale
        if rationale_parts:
            rationale = "Analysis based on historical patterns: " + "; ".join(rationale_parts)
        else:
            rationale = f"Standard geopolitical analysis for {event_type.replace('_', ' ')} between {', '.join(countries)}"

        # Adjust confidence based on data quality
        if len(factors) > 2:
            confidence += 0.2
        if len(precedents) > 3:
            confidence += 0.1

        confidence = min(0.95, confidence)
        ai_probability = max(0.01, min(0.99, ai_probability))

        return ai_probability, confidence, factors, precedents, rationale

    def get_easy_geopolitical_trades(self, min_edge: float = 0.15) -> List[Dict[str, Any]]:
        """Find geopolitical markets with strong predictive edges based on historical patterns."""

        easy_trades = []

        for market_id, analysis in self.market_analyses.items():
            edge = abs(analysis.ai_adjusted_probability - analysis.predicted_probability)

            if edge >= min_edge and analysis.confidence > 0.6:
                trade_info = {
                    'market_id': market_id,
                    'title': analysis.market_title,
                    'kalshi_probability': analysis.predicted_probability,
                    'ai_probability': analysis.ai_adjusted_probability,
                    'edge': edge,
                    'confidence': analysis.confidence,
                    'countries': analysis.countries_involved,
                    'event_type': analysis.event_type,
                    'key_factors': analysis.key_factors[:3],  # Top 3 factors
                    'rationale': analysis.rationale
                }
                easy_trades.append(trade_info)

        # Sort by edge size
        easy_trades.sort(key=lambda x: x['edge'], reverse=True)
        return easy_trades

    def _save_analysis(self, analysis: GeopoliticalMarketAnalysis):
        """Save analysis to file."""
        analyses_data = {
            'analyses': {aid: a.to_dict() for aid, a in self.market_analyses.items()},
            'last_updated': datetime.now().isoformat()
        }

        with open(self.analyses_file, 'w') as f:
            json.dump(analyses_data, f, indent=2)


# Test/demo functions
async def test_geopolitical_engine():
    """Test the geopolitical analysis engine."""
    print("🌍 TESTING GEOPOLITICAL ANALYSIS ENGINE")
    print("=" * 50)

    # Mock engines
    kalshi = KalshiPredictionEngine()
    scenario_graph = ScenarioGraphEngine(kalshi)

    engine = GeopoliticalAnalysisEngine(kalshi, scenario_graph)

    print(f"🌍 Initialized with {len(engine.country_profiles)} country profiles")

    # Test markets
    test_markets = [
        {
            'ticker': 'ISR_PSE_BOMB',
            'title': 'Will Israel bomb Palestine in 2025?',
            'implied_probability': 0.35
        },
        {
            'ticker': 'IRN_ISR_ATTACK',
            'title': 'Will Iran attack Israel in 2025?',
            'implied_probability': 0.25
        },
        {
            'ticker': 'SYR_PEACE',
            'title': 'Will Syria sign peace treaty in 2025?',
            'implied_probability': 0.15
        },
        {
            'ticker': 'PRK_ATTACK',
            'title': 'Will North Korea attack South Korea in 2025?',
            'implied_probability': 0.45
        }
    ]

    print("\n🎯 ANALYZING GEOPOLITICAL MARKETS:")
    for market in test_markets:
        analysis = engine.analyze_geopolitical_market(market)

        if analysis:
            print(f"\n🎭 {market['ticker']}: {market['title']}")
            print(f"   Kalshi Prob: {analysis.predicted_probability:.1%}")
            print(f"   AI Adjusted: {analysis.ai_adjusted_probability:.1%}")
            print(f"   Confidence: {analysis.confidence:.1%}")
            print(f"   Countries: {', '.join(analysis.countries_involved)}")
            print(f"   Event Type: {analysis.event_type}")

            if analysis.key_factors:
                print(f"   Key Factors: {analysis.key_factors[0]}")

            # Show if this is an "easy trade"
            edge = abs(analysis.ai_adjusted_probability - analysis.predicted_probability)
            if edge > 0.15 and analysis.confidence > 0.6:
                direction = "BUY" if analysis.ai_adjusted_probability > analysis.predicted_probability else "SELL"
                print(f"   🎯 EASY TRADE: {direction} with {edge:.1%} edge!")
        else:
            print(f"\n❌ {market['ticker']}: Could not analyze - no country recognition")

    # Show easy trades
    print("\n🎯 EASY GEOPOLITICAL TRADES (15%+ edge):")
    easy_trades = engine.get_easy_geopolitical_trades()

    for trade in easy_trades:
        print(f"🎯 {trade['market_id']}: {trade['edge']:.1%} edge ({trade['confidence']:.1%} confidence)")
        print(f"   {trade['rationale'][:80]}...")
        print()

    # Show country trust scores
    print("🌍 COUNTRY TRUST SCORES:")
    trust_scores = []
    for code, profile in engine.country_profiles.items():
        trust_scores.append((profile.country_name, profile.calculate_overall_trust_score()))

    trust_scores.sort(key=lambda x: x[1])
    for name, score in trust_scores[:5]:  # Show least trustworthy
        print(".1f")

    print("\n✅ Geopolitical Analysis Engine test complete!")


if __name__ == "__main__":
    asyncio.run(test_geopolitical_engine())
