"""Phasma Trading System integration for the Partnership Engine"""
import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import json
import os

from .integration import PartnershipEngine, monitor_tickers
from ..news_engine_analysis import NewsAnalyzer  # For text analysis

class PhasmaPartnershipEngine:
    """Wrapper to integrate Partnership Engine with Phasma Trading System"""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize with optional config path"""
        self.logger = logging.getLogger(__name__)
        self.config = self._load_config(config_path)
        self.engine = PartnershipEngine()
        # NewsAnalyzer requires a config object; partnership JSON dict is sufficient (analyzer stores it).
        self.news_analyzer = NewsAnalyzer(self.config)
        self.is_running = False
        
    def _load_config(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """Load configuration from file or use defaults"""
        default_config = {
            'enabled': True,
            'scan_interval_minutes': 60,
            'min_impact_score': 7.0,
            'monitored_tickers': ['AMD', 'NVDA', 'PLTR'],
            'alerting': {
                'telegram': {
                    'enabled': True,
                    'bot_token': os.getenv('TELEGRAM_BOT_TOKEN', ''),
                    'chat_id': os.getenv('TELEGRAM_CHAT_ID', '')
                }
            }
        }
        
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    file_config = json.load(f)
                    # Merge with defaults
                    return {**default_config, **file_config}
            except Exception as e:
                self.logger.error(f"Error loading partnership config: {e}")
                
        return default_config
    
    async def analyze_news_item(self, news_item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Analyze a news item for partnership/contract events"""
        if not self.config.get('enabled', True):
            return None
            
        try:
            # NewsAnalyzer expects a dict with title/content (not a plain string).
            pattern_tags, confidence_boost = self.news_analyzer.detect_partnerships_and_contracts(
                news_item
            )
            analyzer_score = min(1.0, float(confidence_boost or 0.0))

            # Analyzer returns additive boosts (e.g. 0.3 + 0.4); treat as 0–1 strength.
            if pattern_tags and analyzer_score >= 0.5:
                primary_type = pattern_tags[0] if pattern_tags else "partnership_signal"
                tickers = []
                sym = news_item.get("symbol")
                if sym:
                    tickers.append(sym)
                event = {
                    "type": primary_type,
                    "confidence": analyzer_score,
                    "source": "news_analyzer",
                    "tickers": tickers,
                    "pattern_tags": pattern_tags,
                    "details": {
                        "title": news_item.get("title"),
                        "url": news_item.get("url"),
                        "published_at": news_item.get("published_at"),
                    },
                    "analysis": {
                        "pattern_strength": analyzer_score,
                    },
                }
                return event
                
            # Otherwise, use the full partnership engine for deeper analysis
            ticker = news_item.get('symbol')
            if not ticker:
                return None
                
            events = await self.engine.scan_ticker(ticker)
            if events:
                return {
                    'type': 'partnership_engine',
                    'confidence': max(e.confidence for e in events),
                    'source': 'partnership_engine',
                    'tickers': [ticker] + [cp.name for e in events for cp in e.counterparties if cp.ticker],
                    'events': [e.to_dict() for e in events],
                    'details': {
                        'title': news_item.get('title'),
                        'url': news_item.get('url')
                    }
                }
                
        except Exception as e:
            self.logger.error(f"Error analyzing news item: {e}")
            
        return None
    
    async def start_monitoring(self):
        """Start continuous monitoring of tickers for partnership events"""
        if not self.config.get('enabled', True):
            self.logger.info("Partnership engine monitoring is disabled")
            return
            
        tickers = self.config.get('monitored_tickers', [])
        interval = self.config.get('scan_interval_minutes', 60)
        
        if not tickers:
            self.logger.warning("No tickers configured for partnership monitoring")
            return
            
        self.is_running = True
        self.logger.info(f"Starting partnership monitoring for {len(tickers)} tickers, checking every {interval} minutes")
        
        # Start the monitoring loop in the background
        asyncio.create_task(self._monitor_loop(tickers, interval))
    
    async def _monitor_loop(self, tickers: List[str], interval_minutes: int):
        """Background monitoring loop"""
        while self.is_running:
            try:
                for ticker in tickers:
                    events = await self.engine.scan_ticker(ticker)
                    for event in events:
                        # Only process high-impact events
                        if event.impact_score >= self.config.get('min_impact_score', 7.0):
                            await self._process_event(event)
                
                # Wait for the next interval
                await asyncio.sleep(interval_minutes * 60)
                
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(60)  # Wait a minute before retrying
    
    async def _process_event(self, event):
        """Process a detected partnership event"""
        # Format the alert message
        alert = self._format_alert(event)
        
        # Log the event
        self.logger.info(f"🔔 Partnership Event: {alert}")
        
        # Send alerts based on configuration
        if self.config.get('alerting', {}).get('telegram', {}).get('enabled', False):
            await self._send_telegram_alert(alert)
    
    def _format_alert(self, event) -> str:
        """Format an event as an alert message"""
        # Format the amount if present
        amount_str = ""
        if hasattr(event, 'financials') and event.financials.amount:
            if event.financials.amount >= 1_000_000_000:
                amount_str = f"${event.financials.amount/1_000_000_000:.2f}B"
            elif event.financials.amount >= 1_000_000:
                amount_str = f"${event.financials.amount/1_000_000:.2f}M"
            else:
                amount_str = f"${event.financials.amount:,.2f}"
        
        # Format counterparties
        counterparties = ", ".join([cp.name for cp in event.counterparties])
        
        # Build the message
        lines = [
            f"🚨 *{event.primary_company} - {event.event_type.value.upper()} DETECTED* 🚨",
            f"*Event Type:* {event.event_type.value.replace('_', ' ').title()}",
            f"*Partners:* {counterparties}",
        ]
        
        if amount_str:
            lines.append(f"*Amount:* {amount_str}")
        
        if hasattr(event, 'contract') and event.contract and hasattr(event.contract, 'agency') and event.contract.agency:
            lines.append(f"*Agency:* {event.contract.agency}")
        
        if hasattr(event, 'announced_date') and event.announced_date:
            if isinstance(event.announced_date, str):
                lines.append(f"*Date:* {event.announced_date}")
            else:
                lines.append(f"*Date:* {event.announced_date.strftime('%Y-%m-%d')}")
        
        if hasattr(event, 'url') and event.url:
            lines.append(f"*Source:* [Link]({event.url})")
        
        if hasattr(event, 'impact_score'):
            lines.append(f"*Impact Score:* {event.impact_score:.1f}/10.0")
        
        return "\n".join(lines)
    
    async def _send_telegram_alert(self, message: str):
        """Send an alert via Telegram"""
        try:
            import requests
            
            bot_token = self.config.get('alerting', {}).get('telegram', {}).get('bot_token')
            chat_id = self.config.get('alerting', {}).get('telegram', {}).get('chat_id')
            
            if not bot_token or not chat_id:
                self.logger.warning("Telegram bot token or chat ID not configured")
                return
                
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            payload = {
                'chat_id': chat_id,
                'text': message,
                'parse_mode': 'Markdown',
                'disable_web_page_preview': True
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as response:
                    if response.status != 200:
                        self.logger.error(f"Failed to send Telegram alert: {await response.text()}")
                        
        except Exception as e:
            self.logger.error(f"Error sending Telegram alert: {e}")
    
    def stop_monitoring(self):
        """Stop the monitoring loop"""
        self.is_running = False
        self.logger.info("Stopped partnership monitoring")
