"""
Catalyst Tracker - Identify and track upcoming market-moving events
Monitors Fed meetings, earnings, legislation, crypto events, and economic data
"""

import logging
import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import calendar

@dataclass
class Catalyst:
    """Individual market catalyst"""
    id: str
    title: str
    description: str
    date: datetime
    asset_type: str  # ALL/STOCK/CRYPTO/COMMODITY
    category: str  # MACRO/EARNINGS/LEGISLATION/ECONOMIC/TECHNICAL
    impact_potential: str  # HIGH/MEDIUM/LOW
    probability: float  # 0-1
    expected_outcome: str
    assets_affected: List[str]
    status: str  # UPCOMING/IN_PROGRESS/COMPLETED
    
@dataclass
class CatalystAlert:
    """Alert for approaching catalyst"""
    catalyst: Catalyst
    days_until: int
    urgency: str  # HIGH/MEDIUM/LOW
    action_suggestion: str

class CatalystTracker:
    """Track upcoming market-moving catalysts"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Catalyst database
        self.catalysts = []
        self.alert_history = []
        
        # Event sources
        self.event_sources = {
            'fed_meetings': 'https://api.federalreserve.gov/v1',
            'earnings': 'https://api.earnings.com/v1',
            'crypto_events': 'https://api.cryptoevents.com/v1',
            'economic_calendar': 'https://api.economiccalendar.com/v1'
        }
        
        # Initialize with known catalysts
        self._initialize_known_catalysts()
        
        print("[CATALYST] Catalyst Tracker initialized")
        print(f"[CATALYST] Tracking {len(self.catalysts)} known catalysts")
    
    def _initialize_known_catalysts(self):
        """Initialize with known upcoming catalysts"""
        
        # Federal Reserve Meetings 2026
        fed_dates = [
            (datetime(2026, 3, 18), "March FOMC Meeting"),
            (datetime(2026, 5, 6), "May FOMC Meeting"),
            (datetime(2026, 6, 17), "June FOMC Meeting"),
            (datetime(2026, 7, 29), "July FOMC Meeting"),
            (datetime(2026, 9, 16), "September FOMC Meeting"),
            (datetime(2026, 11, 4), "November FOMC Meeting"),
            (datetime(2026, 12, 15), "December FOMC Meeting")
        ]
        
        for date, title in fed_dates:
            self.catalysts.append(Catalyst(
                id=f"fed_{date.strftime('%Y%m%d')}",
                title=title,
                description="Federal Reserve FOMC meeting to decide on interest rates",
                date=date,
                asset_type="ALL",
                category="MACRO",
                impact_potential="HIGH",
                probability=0.9,
                expected_outcome="Potential rate cuts under new Chair Warsh",
                assets_affected=["ALL"],
                status="UPCOMING"
            ))
        
        # Crypto-specific catalysts
        crypto_catalysts = [
            (datetime(2026, 1, 15), "Clarity Act Senate Markup", "Crypto market structure bill markup in Senate", "CRYPTO", "LEGISLATION"),
            (datetime(2026, 2, 28), "Bitcoin Conference 2026", "Major industry conference with regulatory announcements", "CRYPTO", "TECHNICAL"),
            (datetime(2026, 4, 15), "Ethereum Shanghai Upgrade", "Major network upgrade affecting staking", "CRYPTO", "TECHNICAL"),
            (datetime(2026, 6, 30), "MiCA Regulation Implementation", "EU crypto regulation fully implemented", "CRYPTO", "LEGISLATION"),
        ]
        
        for date, title, desc, asset_type, category in crypto_catalysts:
            self.catalysts.append(Catalyst(
                id=f"crypto_{date.strftime('%Y%m%d')}",
                title=title,
                description=desc,
                date=date,
                asset_type=asset_type,
                category=category,
                impact_potential="HIGH",
                probability=0.7,
                expected_outcome="Market volatility and potential trend changes",
                assets_affected=["BTC", "ETH", "CRYPTO"],
                status="UPCOMING"
            ))
        
        # Economic data releases
        economic_releases = [
            (datetime(2026, 2, 14), "CPI Data Release", "Consumer Price Index inflation data", "ALL", "ECONOMIC", "HIGH"),
            (datetime(2026, 2, 28), "PCE Data Release", "Fed's preferred inflation measure", "ALL", "ECONOMIC", "HIGH"),
            (datetime(2026, 3, 8), "Jobs Report", "Non-farm payrolls and unemployment", "ALL", "ECONOMIC", "HIGH"),
            (datetime(2026, 3, 15), "Retail Sales", "Consumer spending data", "ALL", "ECONOMIC", "MEDIUM"),
        ]
        
        for date, title, desc, asset_type, category, impact in economic_releases:
            self.catalysts.append(Catalyst(
                id=f"econ_{date.strftime('%Y%m%d')}",
                title=title,
                description=desc,
                date=date,
                asset_type=asset_type,
                category=category,
                impact_potential=impact,
                probability=0.95,
                expected_outcome="Market reaction to economic data",
                assets_affected=["SPY", "QQQ", "BTC", "GOLD"],
                status="UPCOMING"
            ))
    
    def get_upcoming_catalysts(self, days: int = 30, asset_type: str = "ALL") -> List[Catalyst]:
        """Get upcoming catalysts within specified days"""
        cutoff = datetime.now() + timedelta(days=days)
        
        filtered = [
            c for c in self.catalysts 
            if c.date <= cutoff 
            and c.status == "UPCOMING"
            and (asset_type == "ALL" or c.asset_type == asset_type)
        ]
        
        # Sort by date
        filtered.sort(key=lambda x: x.date)
        
        return filtered
    
    def get_catalysts_for_asset(self, symbol: str, asset_type: str) -> List[Catalyst]:
        """Get catalysts specifically affecting an asset"""
        relevant = []
        
        for catalyst in self.catalysts:
            if catalyst.status == "UPCOMING":
                # Check if asset is directly affected
                if symbol in catalyst.assets_affected or "ALL" in catalyst.assets_affected:
                    relevant.append(catalyst)
                
                # Check asset type matching
                if asset_type == "CRYPTO" and catalyst.asset_type in ["CRYPTO", "ALL"]:
                    relevant.append(catalyst)
                elif asset_type == "STOCK" and catalyst.asset_type in ["STOCK", "ALL"]:
                    relevant.append(catalyst)
        
        return sorted(relevant, key=lambda x: x.date)
    
    def analyze_catalyst_impact(self, symbol: str, asset_type: str) -> Dict:
        """Analyze potential impact of upcoming catalysts on an asset"""
        print(f"\n[CATALYST] Analyzing catalyst impact for {symbol}")
        print("-" * 50)
        
        # Get relevant catalysts
        catalysts = self.get_catalysts_for_asset(symbol, asset_type)
        
        analysis = {
            'symbol': symbol,
            'asset_type': asset_type,
            'upcoming_catalysts': catalysts,
            'high_impact_events': [],
            'catalyst_density': {},
            'risk_factors': [],
            'opportunities': [],
            'recommendation': '',
            'time_horizon_impact': {
                '1_week': [],
                '1_month': [],
                '3_months': []
            }
        }
        
        # Categorize catalysts by time horizon
        now = datetime.now()
        for catalyst in catalysts:
            days_until = (catalyst.date - now).days
            
            if days_until <= 7:
                analysis['time_horizon_impact']['1_week'].append(catalyst)
            elif days_until <= 30:
                analysis['time_horizon_impact']['1_month'].append(catalyst)
            elif days_until <= 90:
                analysis['time_horizon_impact']['3_months'].append(catalyst)
            
            # High impact events
            if catalyst.impact_potential == "HIGH":
                analysis['high_impact_events'].append(catalyst)
        
        # Calculate catalyst density
        analysis['catalyst_density'] = {
            'next_week': len(analysis['time_horizon_impact']['1_week']),
            'next_month': len(analysis['time_horizon_impact']['1_month']),
            'next_quarter': len(analysis['time_horizon_impact']['3_months'])
        }
        
        # Identify risks and opportunities
        for catalyst in catalysts:
            if catalyst.category in ["MACRO", "ECONOMIC"]:
                if catalyst.impact_potential == "HIGH":
                    analysis['risk_factors'].append({
                        'catalyst': catalyst.title,
                        'risk': "Market volatility around economic data",
                        'mitigation': "Reduce position size before event"
                    })
            
            if catalyst.category in ["LEGISLATION"] and asset_type == "CRYPTO":
                analysis['opportunities'].append({
                    'catalyst': catalyst.title,
                    'opportunity': "Positive regulatory clarity could boost prices",
                    'strategy': "Position for upside if probability > 70%"
                })
        
        # Generate recommendation
        analysis['recommendation'] = self._generate_catalyst_recommendation(analysis)
        
        # Print summary
        self._print_catalyst_analysis(analysis)
        
        return analysis
    
    def _generate_catalyst_recommendation(self, analysis: Dict) -> str:
        """Generate trading recommendation based on catalysts"""
        high_impact_count = len(analysis['high_impact_events'])
        catalyst_density = analysis['catalyst_density']
        
        # High catalyst density = be cautious
        if catalyst_density['next_week'] >= 3:
            return "REDUCE_EXPOSURE - Too many upcoming events"
        
        # High impact events soon = wait for clarity
        if catalyst_density['next_week'] >= 1 and high_impact_count >= 1:
            return "WAIT_FOR_EVENT - High impact event imminent"
        
        # Moderate activity with positive catalysts
        if catalyst_density['next_month'] >= 2 and len(analysis['opportunities']) > len(analysis['risk_factors']):
            return "POSITION_FOR_UPSIDE - Favorable catalyst environment"
        
        # Low activity = normal trading
        if catalyst_density['next_month'] <= 1:
            return "NORMAL_TRADING - Low catalyst impact"
        
        return "CAUTIOUS - Mixed catalyst signals"
    
    def add_custom_catalyst(self, catalyst: Catalyst):
        """Add a custom catalyst to track"""
        self.catalysts.append(catalyst)
        print(f"[CATALYST] Added custom catalyst: {catalyst.title}")
    
    def update_catalyst_status(self, catalyst_id: str, status: str, outcome: str = ""):
        """Update catalyst status after event occurs"""
        for catalyst in self.catalysts:
            if catalyst.id == catalyst_id:
                catalyst.status = status
                if outcome:
                    catalyst.expected_outcome = outcome
                print(f"[CATALYST] Updated {catalyst.title}: {status}")
                break
    
    def get_catalyst_calendar(self, month: int, year: int) -> Dict:
        """Get calendar view of catalysts for a month"""
        cal = calendar.monthcalendar(year, month)
        month_name = calendar.month_name[month]
        
        calendar_data = {
            'month': month_name,
            'year': year,
            'weeks': []
        }
        
        for week in cal:
            week_data = []
            for day in week:
                if day == 0:
                    week_data.append({'day': None, 'catalysts': []})
                else:
                    date = datetime(year, month, day)
                    day_catalysts = [
                        c for c in self.catalysts 
                        if c.date.date() == date.date()
                    ]
                    week_data.append({
                        'day': day,
                        'catalysts': day_catalysts
                    })
            calendar_data['weeks'].append(week_data)
        
        return calendar_data
    
    def check_approaching_alerts(self, days_threshold: int = 3) -> List[CatalystAlert]:
        """Check for catalysts approaching within threshold"""
        alerts = []
        now = datetime.now()
        
        for catalyst in self.catalysts:
            if catalyst.status == "UPCOMING":
                days_until = (catalyst.date - now).days
                
                if days_until <= days_threshold and days_until >= 0:
                    urgency = "HIGH" if days_until <= 1 else "MEDIUM" if days_until <= 2 else "LOW"
                    
                    action = self._get_action_suggestion(catalyst)
                    
                    alerts.append(CatalystAlert(
                        catalyst=catalyst,
                        days_until=days_until,
                        urgency=urgency,
                        action_suggestion=action
                    ))
        
        return sorted(alerts, key=lambda x: x.days_until)
    
    def _get_action_suggestion(self, catalyst: Catalyst) -> str:
        """Get action suggestion for a catalyst"""
        if catalyst.category == "MACRO" and catalyst.impact_potential == "HIGH":
            return "Reduce leverage, consider hedging"
        elif catalyst.category == "EARNINGS":
            return "Check options flow for unusual activity"
        elif catalyst.category == "LEGISLATION":
            return "Monitor news for last-minute developments"
        elif catalyst.category == "TECHNICAL":
            return "Watch for technical breakouts/breakdowns"
        else:
            return "Stay alert for market reaction"
    
    def _print_catalyst_analysis(self, analysis: Dict):
        """Print catalyst analysis summary"""
        print(f"\n[CATALYST ANALYSIS FOR {analysis['symbol']}]")
        print("-" * 50)
        
        print(f"Upcoming Catalysts: {len(analysis['upcoming_catalysts'])}")
        print(f"High Impact Events: {len(analysis['high_impact_events'])}")
        
        density = analysis['catalyst_density']
        print(f"\nCatalyst Density:")
        print(f"  Next Week: {density['next_week']} events")
        print(f"  Next Month: {density['next_month']} events")
        print(f"  Next Quarter: {density['next_quarter']} events")
        
        if analysis['high_impact_events']:
            print(f"\nHIGH IMPACT EVENTS:")
            for event in analysis['high_impact_events'][:3]:
                days_until = (event.date - datetime.now()).days
                print(f"  • {event.title} ({days_until} days)")
        
        print(f"\nRECOMMENDATION: {analysis['recommendation']}")
        print("-" * 50)
    
    def generate_catalyst_report(self, days: int = 30) -> str:
        """Generate a comprehensive catalyst report"""
        upcoming = self.get_upcoming_catalysts(days)
        
        report = f"""
CATALYST REPORT - Next {days} Days
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}

SUMMARY:
- Total Catalysts: {len(upcoming)}
- High Impact: {len([c for c in upcoming if c.impact_potential == 'HIGH'])}
- Medium Impact: {len([c for c in upcoming if c.impact_potential == 'MEDIUM'])}
- Low Impact: {len([c for c in upcoming if c.impact_potential == 'LOW'])}

BY CATEGORY:
- Macro/Economic: {len([c for c in upcoming if c.category in ['MACRO', 'ECONOMIC']])}
- Legislation: {len([c for c in upcoming if c.category == 'LEGISLATION'])}
- Technical: {len([c for c in upcoming if c.category == 'TECHNICAL'])}
- Earnings: {len([c for c in upcoming if c.category == 'EARNINGS'])}

UPCOMING EVENTS:
"""
        
        for catalyst in upcoming[:10]:  # Top 10
            days_until = (catalyst.date - datetime.now()).days
            report += f"\n{days_until:2d} days | {catalyst.title:30s} | {catalyst.impact_potential:7s} | {catalyst.category:12s}"
        
        return report
