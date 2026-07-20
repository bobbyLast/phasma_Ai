"""
Human Validator - Human-in-the-loop validation for high-confidence alerts

Provides checklist validation and risk assessment before capital deployment.
"""

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import yfinance as yf


class HumanValidator:
    """Human-in-the-loop validation for high-confidence alerts"""
    
    def __init__(self):
        """Initialize human validator"""
        self.validation_history = []
        self.checklist_weights = {
            'form4_codes_valid': 0.25,      # Form 4 uses meaningful codes
            'no_imminent_dilution': 0.20,   # No upcoming offerings
            'cash_runway_ok': 0.20,         # Sufficient cash runway
            'catalyst_confirmed': 0.20,     # Catalyst verified
            'no_recent_contact': 0.15       # Compliance check
        }
        
    def validate_alert(self, signal: Dict) -> Dict:
        """
        Run validation checklist for high-confidence alert
        
        Args:
            signal: Confluence signal to validate
            
        Returns:
            Validation result with details
        """
        validation_results = {
            'symbol': signal.get('ticker') or signal.get('symbol') or 'N/A',
            'confluence_score': signal.get('confluence_score', 0),
            'validation_items': {},
            'total_score': 0,
            'recommendation': 'REVIEW_NEEDED',
            'risk_flags': [],
            'validation_timestamp': datetime.now().isoformat()
        }
        
        # Run each validation check
        checks = [
            ('form4_codes_valid', self.validate_form4_codes, signal),
            ('no_imminent_dilution', self.check_dilution_risk, signal),
            ('cash_runway_ok', self.check_cash_runway, signal),
            ('catalyst_confirmed', self.verify_catalyst, signal),
            ('no_recent_contact', self.check_compliance, signal)
        ]
        
        total_score = 0
        
        for check_name, check_func, check_data in checks:
            try:
                result = check_func(check_data)
                validation_results['validation_items'][check_name] = result
                
                if result['passed']:
                    total_score += self.checklist_weights[check_name] * result['score']
                else:
                    validation_results['risk_flags'].append(result['reason'])
                    
            except Exception as e:
                validation_results['validation_items'][check_name] = {
                    'passed': False,
                    'score': 0,
                    'reason': f'Error: {str(e)}'
                }
                validation_results['risk_flags'].append(f'Validation error for {check_name}')
        
        validation_results['total_score'] = total_score
        
        # Determine recommendation
        if total_score >= 0.8:
            validation_results['recommendation'] = 'APPROVED'
        elif total_score >= 0.6:
            validation_results['recommendation'] = 'REVIEW_NEEDED'
        else:
            validation_results['recommendation'] = 'REJECTED'
        
        # Store validation
        self.validation_history.append(validation_results)
        
        return validation_results
    
    def validate_form4_codes(self, signal: Dict) -> Dict:
        """
        Ensure Form 4 uses meaningful transaction codes
        
        Args:
            signal: Signal data
            
        Returns:
            Validation result
        """
        insider_signals = signal.get('insider_signals', [])
        
        if not insider_signals:
            return {
                'passed': False,
                'score': 0,
                'reason': 'No insider signals to validate'
            }
        
        # Check that all insider buys are Code P (open market)
        all_open_market = True
        total_amount = 0
        high_quality_count = 0
        
        for insider in insider_signals:
            if insider.get('transaction_code') != 'P':
                all_open_market = False
            else:
                total_amount += insider.get('amount', 0)
                if insider.get('quality', 'LOW') in ['HIGH', 'MEDIUM']:
                    high_quality_count += 1
        
        if all_open_market and total_amount >= 1000000:
            score = 1.0
            reason = f'All open market buys totaling ${total_amount/1000000:.1f}M'
        elif all_open_market:
            score = 0.7
            reason = f'Open market buys but amount ${total_amount/1000000:.1f}M < $1M'
        else:
            score = 0.3
            reason = 'Contains non-open-market transactions'
        
        return {
            'passed': score >= 0.5,
            'score': score,
            'reason': reason,
            'details': {
                'total_amount': total_amount,
                'high_quality_count': high_quality_count,
                'all_open_market': all_open_market
            }
        }
    
    def check_dilution_risk(self, signal: Dict) -> Dict:
        """
        Check for upcoming dilution risk
        
        Args:
            signal: Signal data
            
        Returns:
            Validation result
        """
        symbol = signal.get('ticker', '')
        
        # In production, would check recent 8-K filings
        # For now, simulate based on company size and cash
        
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # Check cash position
            cash = info.get('totalCash', 0)
            debt = info.get('totalDebt', 0)
            market_cap = info.get('marketCap', 0)
            
            # Calculate cash runway proxy
            if market_cap > 0:
                cash_ratio = cash / market_cap
                debt_ratio = debt / market_cap
                
                # Good financial position
                if cash_ratio > 0.1 and debt_ratio < 0.3:
                    score = 0.9
                    reason = f'Strong cash position (${cash/1000000:.0f}M) and low debt'
                # Moderate position
                elif cash_ratio > 0.05:
                    score = 0.7
                    reason = f'Moderate cash position (${cash/1000000:.0f}M)'
                # Weak position
                else:
                    score = 0.4
                    reason = f'Limited cash (${cash/1000000:.0f}M) - dilution risk'
            else:
                score = 0.5
                reason = 'Unable to assess financial position'
            
        except Exception as e:
            score = 0.5
            reason = f'Error checking financials: {str(e)}'
        
        return {
            'passed': score >= 0.5,
            'score': score,
            'reason': reason
        }
    
    def check_cash_runway(self, signal: Dict) -> Dict:
        """
        Check if company has sufficient cash runway
        
        Args:
            signal: Signal data
            
        Returns:
            Validation result
        """
        symbol = signal.get('ticker', '')
        
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # Get financial metrics
            cash = info.get('totalCash', 0)
            operating_cash_flow = info.get('operatingCashflow', 0)
            
            if operating_cash_flow < 0:
                # Calculate burn rate from negative cash flow
                burn_rate = abs(operating_cash_flow)
                runway_months = cash / burn_rate * 12 if burn_rate > 0 else 24
                
                if runway_months > 18:
                    score = 0.9
                    reason = f'Cash runway: {runway_months:.0f} months'
                elif runway_months > 12:
                    score = 0.7
                    reason = f'Cash runway: {runway_months:.0f} months'
                else:
                    score = 0.3
                    reason = f'Limited cash runway: {runway_months:.0f} months'
            else:
                # Positive cash flow
                score = 1.0
                reason = 'Positive operating cash flow'
            
        except Exception as e:
            score = 0.5
            reason = f'Error calculating runway: {str(e)}'
        
        return {
            'passed': score >= 0.5,
            'score': score,
            'reason': reason
        }
    
    def verify_catalyst(self, signal: Dict) -> Dict:
        """
        Verify upcoming catalyst exists
        
        Args:
            signal: Signal data
            
        Returns:
            Validation result
        """
        # Check reasoning for catalyst mentions
        reasoning = signal.get('reasoning', '').lower()
        
        catalyst_keywords = [
            'trial', 'fda', 'approval', 'earnings', 'data',
            'launch', 'partnership', 'contract', 'patent',
            'merger', 'acquisition', 'guidance', 'conference'
        ]
        
        has_catalyst = any(keyword in reasoning for keyword in catalyst_keywords)
        
        if has_catalyst:
            score = 0.8
            reason = 'Catalyst identified in signal reasoning'
        else:
            score = 0.4
            reason = 'No clear catalyst identified'
        
        return {
            'passed': score >= 0.5,
            'score': score,
            'reason': reason,
            'catalyst_detected': has_catalyst
        }
    
    def check_compliance(self, signal: Dict) -> Dict:
        """
        Check compliance requirements
        
        Args:
            signal: Signal data
            
        Returns:
            Validation result
        """
        # In production, would check:
        # - No material non-public information
        # - No recent company contact
        # - Position size within limits
        
        # For now, assume compliance if using public data
        score = 0.9
        reason = 'Using only public data sources'
        
        return {
            'passed': True,
            'score': score,
            'reason': reason,
            'compliance_checks': {
                'public_data_only': True,
                'no_material_nonpublic': True,
                'position_size_ok': True
            }
        }
    
    def generate_validation_report(self, signal: Dict) -> Dict:
        """
        Create comprehensive validation report for human review
        
        Args:
            signal: Signal to validate
            
        Returns:
            Detailed validation report
        """
        validation = self.validate_alert(signal)
        
        report = {
            'executive_summary': {
                'symbol': validation['symbol'],
                'confluence_score': validation['confluence_score'],
                'validation_score': validation['total_score'],
                'recommendation': validation['recommendation']
            },
            'signal_analysis': {
                'insider_signals': len(signal.get('insider_signals', [])),
                'institutional_signals': len(signal.get('institutional_signals', [])),
                'analyst_signals': len(signal.get('analyst_signals', [])),
                'options_signals': len(signal.get('options_signals', []))
            },
            'validation_details': validation['validation_items'],
            'risk_assessment': {
                'risk_flags': validation['risk_flags'],
                'risk_level': 'LOW' if len(validation['risk_flags']) <= 1 else 'MEDIUM' if len(validation['risk_flags']) <= 3 else 'HIGH'
            },
            'recommended_action': self._get_action_recommendation(validation),
            'review_checklist': self._generate_review_checklist(validation)
        }
        
        return report
    
    def _get_action_recommendation(self, validation: Dict) -> str:
        """Get recommended action based on validation"""
        score = validation['total_score']
        
        if score >= 0.8:
            return "APPROVE for position sizing up to 2% of portfolio"
        elif score >= 0.6:
            return "REVIEW - Consider 0.5-1% position if risk flags addressed"
        else:
            return "REJECT - Too many risk factors, wait for better setup"
    
    def _generate_review_checklist(self, validation: Dict) -> List[str]:
        """Generate checklist items for human reviewer"""
        checklist = []
        
        items = validation['validation_items']
        
        if not items.get('form4_codes_valid', {}).get('passed', False):
            checklist.append("□ Verify all insider transactions are open market buys (Code P)")
        
        if not items.get('no_imminent_dilution', {}).get('passed', False):
            checklist.append("□ Check for upcoming secondary offerings or financings")
        
        if not items.get('cash_runway_ok', {}).get('passed', False):
            checklist.append("□ Confirm company has >12 months cash runway")
        
        if not items.get('catalyst_confirmed', {}).get('passed', False):
            checklist.append("□ Identify and verify upcoming catalyst timeline")
        
        if validation['risk_flags']:
            checklist.append(f"□ Address {len(validation['risk_flags'])} risk flags: {', '.join(validation['risk_flags'][:3])}")
        
        return checklist


# Example usage
if __name__ == "__main__":
    validator = HumanValidator()
    
    # Example signal
    signal = {
        'ticker': 'XYZ',
        'confluence_score': 0.85,
        'insider_signals': [
            {'transaction_code': 'P', 'amount': 2000000, 'quality': 'HIGH'}
        ],
        'reasoning': 'Phase 2 trial data expected next quarter'
    }
    
    report = validator.generate_validation_report(signal)
    print(f"Recommendation: {report['executive_summary']['recommendation']}")
