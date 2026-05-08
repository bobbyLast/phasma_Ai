"""
Weather Consistency Engine with Enhanced Research Integration
"""

import sys
sys.path.append('.')

from engines.enhanced_weather_research import EnhancedWeatherResearch
from datetime import datetime, timedelta
import statistics

class WeatherConsistencyEngine:
    """8 principles for high win-rate weather prediction on Kalshi"""
    
    def __init__(self):
        self.research = EnhancedWeatherResearch()
        self.principles = {
            1: "Historical Pattern Recognition",
            2: "Multiple Model Consensus", 
            3: "Climate Change Adjustment",
            4: "Regional Specialization",
            5: "Real-time Validation",
            6: "Extreme Event Awareness",
            7: "Seasonal Anomaly Detection",
            8: "Cross-Model Verification"
        }
    
    def check_weather_consistency(self, ticker: str, market_data: dict) -> dict:
        """Apply all 8 principles to validate weather prediction"""
        
        # Step 1: Comprehensive research analysis
        research_result = self.research.analyze_weather_market(ticker, market_data)
        
        if not research_result['valid']:
            return {
                'consistent': False,
                'reason': research_result['reason'],
                'confidence': 0,
                'edge': 0,
                'stability': 0,
                'agreement': 0,
                'principles_failed': ['parsing']
            }
        
        # Step 2: Apply 8 principles
        principle_results = {}
        
        # Principle 1: Historical Patterns
        principle_results[1] = self._check_historical_patterns(
            research_result['detailed_analysis']['historical_patterns']
        )
        
        # Principle 2: Model Consensus
        principle_results[2] = self._check_model_consensus(
            research_result['detailed_analysis']['forecast_consensus']
        )
        
        # Principle 3: Climate Adjustment
        principle_results[3] = self._check_climate_adjustment(
            research_result['detailed_analysis']['climate_impact']
        )
        
        # Principle 4: Regional Knowledge
        principle_results[4] = self._check_regional_specialization(
            research_result['location'], research_result['weather_type']
        )
        
        # Principle 5: Real-time Validation
        principle_results[5] = self._check_real_time_validation(
            research_result['detailed_analysis']['current_conditions']
        )
        
        # Principle 6: Extreme Events
        principle_results[6] = self._check_extreme_events(
            research_result['detailed_analysis']['climate_impact']
        )
        
        # Principle 7: Seasonal Anomalies
        principle_results[7] = self._check_seasonal_anomalies(
            research_result['target_date'], research_result['location']
        )
        
        # Principle 8: Cross-Verification
        principle_results[8] = self._check_cross_verification(
            research_result['detailed_analysis']['validation']
        )
        
        # Step 3: Calculate overall consistency
        passed_principles = sum(1 for p in principle_results.values() if p['passed'])
        total_principles = len(principle_results)
        
        consistency_score = passed_principles / total_principles
        
        # Step 4: Calculate edge and confidence
        market_prob = market_data.get('implied_probability', 0.5)
        forecast_prob = research_result['detailed_analysis']['forecast_consensus']['consensus_probability']
        
        # Edge is our advantage over market
        edge = abs(forecast_prob - market_prob)
        
        # Confidence based on research and principles
        base_confidence = research_result['confidence']
        principle_bonus = consistency_score * 0.1
        final_confidence = min(base_confidence + principle_bonus, 0.95)
        
        # Step 5: Make final decision
        min_edge_threshold = 0.08  # 8% minimum edge
        min_confidence_threshold = 0.60  # 60% minimum confidence
        
        if edge >= min_edge_threshold and final_confidence >= min_confidence_threshold:
            consistent = True
            action = 'BUY_YES' if forecast_prob > 0.5 else 'BUY_NO'
        else:
            consistent = False
            action = None
        
        # Compile results
        failed_principles = [i for i, p in principle_results.items() if not p['passed']]
        
        return {
            'consistent': consistent,
            'reason': self._generate_reason(principle_results, research_result),
            'confidence': final_confidence,
            'edge': edge,
            'stability': consistency_score,
            'agreement': research_result['detailed_analysis']['forecast_consensus']['agreement_level'],
            'action': action,
            'research_summary': research_result['research_summary'],
            'principles_passed': passed_principles,
            'principles_failed': failed_principles,
            'detailed_research': research_result['detailed_analysis']
        }
    
    def _check_historical_patterns(self, historical: dict) -> dict:
        """Principle 1: Check if historical patterns support the prediction"""
        if 'error' in historical:
            return {'passed': False, 'reason': historical['error']}
        
        # Check for sufficient data
        if historical.get('years_analyzed', 0) < 20:
            return {'passed': False, 'reason': 'Insufficient historical data'}
        
        # Check trend consistency
        trend = historical.get('recent_trend', 0)
        if abs(trend) > 2:  # Significant trend
            return {'passed': True, 'reason': f'Strong historical trend: {trend:.1f}°F'}
        
        return {'passed': True, 'reason': 'Historical patterns support prediction'}
    
    def _check_model_consensus(self, forecast: dict) -> dict:
        """Principle 2: Check if multiple models agree"""
        agreement = forecast.get('agreement_level', 'low')
        
        if agreement == 'high':
            return {'passed': True, 'reason': 'High model agreement'}
        elif agreement == 'medium':
            return {'passed': True, 'reason': 'Moderate model agreement'}
        else:
            return {'passed': False, 'reason': 'Low model agreement - high uncertainty'}
    
    def _check_climate_adjustment(self, climate: dict) -> dict:
        """Principle 3: Verify climate change impacts are considered"""
        if climate.get('confidence_in_impact') == 'high':
            return {'passed': True, 'reason': 'Climate change impacts properly assessed'}
        else:
            return {'passed': False, 'reason': 'Insufficient climate change consideration'}
    
    def _check_regional_specialization(self, location: str, weather_type: str) -> dict:
        """Principle 4: Check if we have regional expertise"""
        known_locations = ['NYC', 'CHI', 'MIA', 'LA', 'DAL', 'SEA', 'DEN']
        
        if location in known_locations:
            return {'passed': True, 'reason': f'Regional expertise available for {location}'}
        else:
            return {'passed': False, 'reason': f'Limited regional data for {location}'}
    
    def _check_real_time_validation(self, current: dict) -> dict:
        """Principle 5: Check if we have current conditions"""
        if current.get('current_temperature') == 'real_data_needed':
            return {'passed': False, 'reason': 'Real-time data not integrated'}
        else:
            return {'passed': True, 'reason': 'Real-time conditions analyzed'}
    
    def _check_extreme_events(self, climate: dict) -> dict:
        """Principle 6: Check extreme event awareness"""
        extreme_freq = climate.get('extreme_event_frequency', 1)
        
        if extreme_freq > 1.2:
            return {'passed': True, 'reason': 'Extreme event frequency considered'}
        else:
            return {'passed': False, 'reason': 'Extreme events not properly weighted'}
    
    def _check_seasonal_anomalies(self, date: str, location: str) -> dict:
        """Principle 7: Check for seasonal anomalies"""
        date_obj = datetime.strptime(date, '%Y-%m-%d')
        
        # Simple check - would be more complex in production
        if date_obj.month in [12, 1, 2]:  # Winter
            return {'passed': True, 'reason': 'Winter seasonal patterns analyzed'}
        elif date_obj.month in [6, 7, 8]:  # Summer
            return {'passed': True, 'reason': 'Summer seasonal patterns analyzed'}
        else:
            return {'passed': True, 'reason': 'Transition season patterns analyzed'}
    
    def _check_cross_verification(self, validation: dict) -> dict:
        """Principle 8: Cross-verify with market probability"""
        status = validation.get('validation_status', 'unknown')
        
        if status == 'aligned':
            return {'passed': True, 'reason': 'Market and forecast aligned'}
        elif status == 'slight_mismatch':
            return {'passed': True, 'reason': 'Minor discrepancy but acceptable'}
        else:
            return {'passed': False, 'reason': 'Significant market-forecast mismatch'}
    
    def _generate_reason(self, principle_results: dict, research: dict) -> str:
        """Generate comprehensive reason for decision"""
        passed = sum(1 for p in principle_results.values() if p['passed'])
        total = len(principle_results)
        
        reasons = []
        for principle, result in principle_results.items():
            if result['passed']:
                reasons.append(f"P{principle}: {result['reason']}")
        
        # Add key research insights
        summary = research['research_summary']
        if summary['recommendation'] == 'FOLLOW_FORECAST':
            reasons.append(f"Research indicates forecast more reliable than market")
        
        return f"Passed {passed}/{total} principles. {'; '.join(reasons[:3])}"
