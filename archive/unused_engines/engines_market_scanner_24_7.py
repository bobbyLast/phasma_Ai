"""
24/7 Market Scanner - Global Monitoring System
Implements DeepSeek's tiered alert system for continuous market watching
"""

import logging
import asyncio
from datetime import datetime, time
from typing import Dict, List, Optional
import pytz
from enum import Enum

class AlertTier(Enum):
    """Alert priority levels"""
    TIER_1_IMMEDIATE = "IMMEDIATE_ACTION"  # Wake up the user
    TIER_2_HIGH = "HIGH_PRIORITY"          # Review within 15 mins
    TIER_3_WATCHLIST = "WATCHLIST"         # Monitor closely

class MarketSession(Enum):
    """Global market sessions"""
    ASIA = "ASIA"
    EUROPE = "EUROPE"
    US_PREMARKET = "US_PREMARKET"
    US_REGULAR = "US_REGULAR"
    US_AFTERHOURS = "US_AFTERHOURS"

class Market247Scanner:
    """Continuous market and news monitoring with tiered alerts"""
    
    def __init__(self, config=None, news_engine=None, options_engine=None, telegram_bot=None):
        """Initialize 24/7 scanner"""
        self.config = config or {}
        self.news_engine = news_engine
        self.options_engine = options_engine
        self.telegram_bot = telegram_bot
        self.logger = logging.getLogger(__name__)
        
        # Market sessions definition
        self.sessions = {
            MarketSession.ASIA: {
                'open_time': time(20, 0),   # 8:00 PM EST
                'close_time': time(2, 0),    # 2:00 AM EST
                'focus': ['JPY', 'CNY', 'HKD', 'AUD'],
                'timezone': 'Asia/Tokyo'
            },
            MarketSession.EUROPE: {
                'open_time': time(3, 0),     # 3:00 AM EST
                'close_time': time(11, 0),   # 11:00 AM EST
                'focus': ['EUR', 'GBP', 'DAX', 'FTSE'],
                'timezone': 'Europe/London'
            },
            MarketSession.US_PREMARKET: {
                'open_time': time(4, 0),     # 4:00 AM EST
                'close_time': time(9, 30),   # 9:30 AM EST
                'focus': ['gap_analysis', 'overnight_news'],
                'timezone': 'US/Eastern'
            },
            MarketSession.US_REGULAR: {
                'open_time': time(9, 30),    # 9:30 AM EST
                'close_time': time(16, 0),   # 4:00 PM EST
                'focus': ['main_trading', 'momentum'],
                'timezone': 'US/Eastern'
            },
            MarketSession.US_AFTERHOURS: {
                'open_time': time(16, 0),    # 4:00 PM EST
                'close_time': time(20, 0),   # 8:00 PM EST
                'focus': ['earnings', 'late_news'],
                'timezone': 'US/Eastern'
            }
        }
        
        # Tiered alert triggers
        self.tier_1_triggers = {
            'corporate_actions': [
                'merger_announcement',
                'acquisition_announced',
                'fda_approval',
                'fda_rejection',
                'bankruptcy_filing',
                'major_contract_win',
                'major_contract_loss'
            ],
            'earnings_surprises': [
                'eps_beat_>20%',
                'eps_miss_>20%',
                'revenue_surprise_>15%',
                'guidance_change_>30%'
            ],
            'regulatory_news': [
                'sec_investigation',
                'antitrust_ruling',
                'government_contract'
            ]
        }
        
        self.tier_2_triggers = {
            'technical_breakouts': [
                'multi_month_resistance_break',
                'volume_spike_>500%',
                'ma_golden_cross',
                'ma_death_cross'
            ],
            'options_activity': [
                'sweep_>$1M',
                'unusual_volume_>10x',
                'large_spread_trades'
            ],
            'sector_news': [
                'industry_regulation',
                'supply_chain_disruption',
                'commodity_spike_>10%'
            ]
        }
        
        self.tier_3_triggers = {
            'developing_catalysts': [
                'rumor_from_reliable_source',
                'analyst_upgrade_chain',
                'insider_buying_cluster'
            ],
            'technical_setups': [
                'consolidation_breakout_setup',
                'oversold_bounce_candidate',
                'volatility_compression'
            ]
        }
        
        # Scanning intervals (seconds)
        self.scan_intervals = {
            'news_scan': 10,          # Every 10 seconds
            'options_flow': 60,       # Every minute
            'technical_scan': 300,    # Every 5 minutes
            'sector_momentum': 900    # Every 15 minutes
        }
        
        # Active alerts
        self.active_alerts = []
        self.scanning_active = False
    
    async def start_24_7_monitoring(self):
        """Start continuous 24/7 market monitoring"""
        self.logger.info("Starting 24/7 market monitoring...")
        self.scanning_active = True
        
        # Run all scanners in parallel
        await asyncio.gather(
            self._news_wire_monitor(),
            self._options_flow_analyzer(),
            self._technical_breakout_detector(),
            self._sector_momentum_tracker(),
            self._session_manager(),
            return_exceptions=True
        )
    
    async def stop_monitoring(self):
        """Stop all monitoring"""
        self.scanning_active = False
        self.logger.info("Stopping 24/7 monitoring")
    
    def get_active_session(self) -> Optional[MarketSession]:
        """Get currently active market session"""
        now = datetime.now(pytz.timezone('US/Eastern'))
        current_time = now.time()
        
        for session, info in self.sessions.items():
            open_t = info['open_time']
            close_t = info['close_time']
            
            # Handle sessions that cross midnight
            if open_t > close_t:
                if current_time >= open_t or current_time < close_t:
                    return session
            else:
                if open_t <= current_time < close_t:
                    return session
        
        return None
    
    async def _news_wire_monitor(self):
        """Monitor news feeds continuously"""
        while self.scanning_active:
            try:
                # Scan latest news
                if self.news_engine:
                    news_items = await self._fetch_latest_news()
                    
                    for item in news_items:
                        alert_tier = self._classify_news_alert(item)
                        
                        if alert_tier:
                            await self._trigger_alert(alert_tier, item)
                
                await asyncio.sleep(self.scan_intervals['news_scan'])
                
            except Exception as e:
                self.logger.error(f"News monitor error: {e}")
                await asyncio.sleep(self.scan_intervals['news_scan'])
    
    async def _options_flow_analyzer(self):
        """Monitor unusual options activity"""
        while self.scanning_active:
            try:
                # Check for unusual options flow
                unusual_flow = await self._detect_unusual_flow()
                
                for flow in unusual_flow:
                    alert_tier = self._classify_options_alert(flow)
                    
                    if alert_tier:
                        await self._trigger_alert(alert_tier, flow)
                
                await asyncio.sleep(self.scan_intervals['options_flow'])
                
            except Exception as e:
                self.logger.error(f"Options flow error: {e}")
                await asyncio.sleep(self.scan_intervals['options_flow'])
    
    async def _technical_breakout_detector(self):
        """Scan for technical breakouts"""
        while self.scanning_active:
            try:
                # Scan watchlist for breakouts
                breakouts = await self._scan_technical_breakouts()
                
                for breakout in breakouts:
                    alert_tier = self._classify_technical_alert(breakout)
                    
                    if alert_tier:
                        await self._trigger_alert(alert_tier, breakout)
                
                await asyncio.sleep(self.scan_intervals['technical_scan'])
                
            except Exception as e:
                self.logger.error(f"Technical scan error: {e}")
                await asyncio.sleep(self.scan_intervals['technical_scan'])
    
    async def _sector_momentum_tracker(self):
        """Track sector rotation and momentum"""
        while self.scanning_active:
            try:
                # Analyze sector momentum
                sector_data = await self._analyze_sector_rotation()
                
                strong_sectors = sector_data.get('strong', [])
                weak_sectors = sector_data.get('weak', [])
                
                # Alert on significant shifts
                if strong_sectors or weak_sectors:
                    await self._trigger_alert(
                        AlertTier.TIER_3_WATCHLIST,
                        {
                            'type': 'sector_rotation',
                            'strong': strong_sectors,
                            'weak': weak_sectors
                        }
                    )
                
                await asyncio.sleep(self.scan_intervals['sector_momentum'])
                
            except Exception as e:
                self.logger.error(f"Sector tracking error: {e}")
                await asyncio.sleep(self.scan_intervals['sector_momentum'])
    
    async def _session_manager(self):
        """Manage market session transitions"""
        current_session = None
        
        while self.scanning_active:
            try:
                new_session = self.get_active_session()
                
                if new_session != current_session:
                    self.logger.info(f"Market session changed: {current_session} -> {new_session}")
                    
                    # Send session change notification
                    if self.telegram_bot and new_session:
                        await self._send_session_notification(new_session)
                    
                    current_session = new_session
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                self.logger.error(f"Session manager error: {e}")
                await asyncio.sleep(60)
    
    def _classify_news_alert(self, news_item: Dict) -> Optional[AlertTier]:
        """Classify news item into alert tier"""
        news_type = news_item.get('type', '').lower()
        impact = news_item.get('impact_score', 0)
        
        # Check Tier 1 (Immediate)
        for category, triggers in self.tier_1_triggers.items():
            for trigger in triggers:
                if trigger.lower() in news_type or trigger.lower() in news_item.get('title', '').lower():
                    return AlertTier.TIER_1_IMMEDIATE
        
        # Check Tier 2 (High Priority)
        for category, triggers in self.tier_2_triggers.items():
            for trigger in triggers:
                if trigger.lower() in news_type or impact > 0.7:
                    return AlertTier.TIER_2_HIGH
        
        # Check Tier 3 (Watchlist)
        if impact > 0.5:
            return AlertTier.TIER_3_WATCHLIST
        
        return None
    
    def _classify_options_alert(self, flow: Dict) -> Optional[AlertTier]:
        """Classify options flow into alert tier"""
        premium = flow.get('premium_spent', 0)
        volume_ratio = flow.get('volume_ratio', 1.0)
        
        if premium > 1_000_000:
            return AlertTier.TIER_1_IMMEDIATE
        elif volume_ratio > 10:
            return AlertTier.TIER_2_HIGH
        elif volume_ratio > 5:
            return AlertTier.TIER_3_WATCHLIST
        
        return None
    
    def _classify_technical_alert(self, breakout: Dict) -> Optional[AlertTier]:
        """Classify technical breakout into alert tier"""
        volume_spike = breakout.get('volume_spike', 1.0)
        breakout_type = breakout.get('type', '')
        
        if volume_spike > 5.0 and 'multi_month' in breakout_type:
            return AlertTier.TIER_2_HIGH
        elif volume_spike > 3.0:
            return AlertTier.TIER_3_WATCHLIST
        
        return None
    
    async def _trigger_alert(self, tier: AlertTier, data: Dict):
        """Trigger alert based on tier"""
        alert = {
            'timestamp': datetime.now().isoformat(),
            'tier': tier.value,
            'data': data
        }
        
        self.active_alerts.append(alert)
        
        # Send notifications based on tier
        if tier == AlertTier.TIER_1_IMMEDIATE:
            await self._send_immediate_alert(alert)
        elif tier == AlertTier.TIER_2_HIGH:
            await self._send_high_priority_alert(alert)
        else:
            await self._send_watchlist_alert(alert)
    
    async def _send_immediate_alert(self, alert: Dict):
        """Send TIER 1 immediate action alert"""
        if self.telegram_bot:
            message = f"""
🚨 **IMMEDIATE ACTION REQUIRED** 🚨

{alert['data'].get('title', 'Alert')}

Symbol: {alert['data'].get('symbol', 'N/A')}
Type: {alert['data'].get('type', 'N/A')}
Impact: HIGH

Details: {alert['data'].get('description', 'No details')}

⏰ Action Required: Review within 5 minutes
"""
            await self.telegram_bot.send_message(message)
        
        self.logger.critical(f"TIER 1 ALERT: {alert}")
    
    async def _send_high_priority_alert(self, alert: Dict):
        """Send TIER 2 high priority alert"""
        if self.telegram_bot:
            message = f"""
⚠️ **HIGH PRIORITY**

{alert['data'].get('title', 'Alert')}

Symbol: {alert['data'].get('symbol', 'N/A')}
Type: {alert['data'].get('type', 'N/A')}

📊 Review within 15 minutes
"""
            await self.telegram_bot.send_message(message)
        
        self.logger.warning(f"TIER 2 ALERT: {alert}")
    
    async def _send_watchlist_alert(self, alert: Dict):
        """Send TIER 3 watchlist alert"""
        self.logger.info(f"TIER 3 ALERT: {alert}")
    
    async def _send_session_notification(self, session: MarketSession):
        """Send market session change notification"""
        if self.telegram_bot:
            session_info = self.sessions[session]
            message = f"""
🌍 **Market Session Change**

Now Active: {session.value}
Focus: {', '.join(session_info['focus'])}

Scanning adjusted for this session.
"""
            await self.telegram_bot.send_message(message)
    
    async def _fetch_latest_news(self) -> List[Dict]:
        """Fetch latest news from all sources"""
        # Placeholder - integrate with actual news engine
        return []
    
    async def _detect_unusual_flow(self) -> List[Dict]:
        """Detect unusual options flow"""
        # Placeholder - integrate with options scanner
        return []
    
    async def _scan_technical_breakouts(self) -> List[Dict]:
        """Scan for technical breakouts"""
        # Placeholder - integrate with technical scanner
        return []
    
    async def _analyze_sector_rotation(self) -> Dict:
        """Analyze sector rotation"""
        # Placeholder - integrate with sector analyzer
        return {'strong': [], 'weak': []}
    
    def get_alert_statistics(self, hours: int = 24) -> Dict:
        """Get alert statistics"""
        cutoff = datetime.now() - timedelta(hours=hours)
        recent_alerts = [
            a for a in self.active_alerts
            if datetime.fromisoformat(a['timestamp']) > cutoff
        ]
        
        by_tier = {}
        for alert in recent_alerts:
            tier = alert['tier']
            by_tier[tier] = by_tier.get(tier, 0) + 1
        
        return {
            'total_alerts': len(recent_alerts),
            'by_tier': by_tier,
            'period_hours': hours
        }
