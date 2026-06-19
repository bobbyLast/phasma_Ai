"""
Alert Router - Priority-based alert system with multi-channel delivery
"""
import os
from dotenv import load_dotenv

load_dotenv()
from enum import Enum
from typing import Dict, List, Optional
from datetime import datetime
import asyncio

class AlertPriority(Enum):
    CRITICAL = "CRITICAL"  # Immediate action required
    HIGH = "HIGH"         # Important signal
    WATCH = "WATCH"       # Monitor closely
    INFO = "INFO"         # FYI only

class AlertChannel(Enum):
    TELEGRAM = "telegram"
    UMBRA_VOICE = "umbra_voice"  # For smart glasses
    EMAIL = "email"
    DESKTOP = "desktop"
    LOG = "log"

class AlertRouter:
    """
    Routes alerts based on priority, content, and user preferences
    """
    def __init__(self):
        self.telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID')
        self.active_channels = self._load_channel_preferences()
        self.telegram_bot = None
        self._init_telegram_bot()

    def _init_telegram_bot(self):
        """Initialize Telegram bot for actual message sending"""
        try:
            from telegram_bot import get_telegram_bot
            self.telegram_bot = get_telegram_bot()
        except Exception as e:
            print(f"⚠️ AlertRouter: Could not initialize Telegram bot: {e}")
            self.telegram_bot = None

    def _load_channel_preferences(self) -> Dict[AlertPriority, List[AlertChannel]]:
        """Load user preferences for which channels get which priorities"""
        return {
            AlertPriority.CRITICAL: [AlertChannel.TELEGRAM, AlertChannel.UMBRA_VOICE],
            AlertPriority.HIGH: [AlertChannel.TELEGRAM],
            AlertPriority.WATCH: [AlertChannel.EMAIL],
            AlertPriority.INFO: [AlertChannel.LOG]
        }

    async def route_alert(self, alert_data: Dict) -> None:
        """
        Route an alert to appropriate channels based on priority
        """
        priority = alert_data.get('priority', AlertPriority.INFO)
        channels = self.active_channels.get(priority, [AlertChannel.LOG])

        # Add context and metadata
        enriched_alert = self._enrich_alert(alert_data)

        # Route to each channel
        for channel in channels:
            await self._send_to_channel(channel, enriched_alert)

    def _enrich_alert(self, alert_data: Dict) -> Dict:
        """Add context, timestamp, and metadata to alert"""
        enriched = alert_data.copy()
        enriched.update({
            'timestamp': datetime.now().isoformat(),
            'alert_id': f"{alert_data.get('symbol', 'SYSTEM')}_{int(datetime.now().timestamp())}",
            'context': self._build_context(alert_data),
            'action_suggestion': self._suggest_action(alert_data)
        })
        return enriched

    def _build_context(self, alert_data: Dict) -> str:
        """Build contextual information strip"""
        symbol = alert_data.get('symbol', 'N/A')
        trigger = alert_data.get('trigger_reason', 'Unknown')

        context_parts = []

        # Volume context
        volume = alert_data.get('volume_info')
        if volume:
            context_parts.append(f"Vol: {volume}")

        # Float context
        float_info = alert_data.get('float_info')
        if float_info:
            context_parts.append(f"Float: {float_info}")

        # Sentiment/social context
        sentiment = alert_data.get('sentiment_score')
        if sentiment:
            context_parts.append(f"Sentiment: {sentiment}")

        # Options context
        options_flow = alert_data.get('options_flow')
        if options_flow:
            context_parts.append(f"Options: {options_flow}")

        context = " | ".join(context_parts) if context_parts else "Standard signal"
        return f"{symbol}: {trigger} | {context}"

    def _suggest_action(self, alert_data: Dict) -> str:
        """Suggest next action based on alert type"""
        alert_type = alert_data.get('type', 'signal')

        suggestions = {
            'volatility_burst': "Review chart immediately - potential breakout",
            'entry_signal': f"Consider entry with {alert_data.get('position_size', 'N/A')} contracts",
            'exit_signal': "Execute exit strategy as planned",
            'risk_alert': "Reduce position or exit if conditions deteriorate",
            'system_health': "Check system status and data feeds"
        }

        return suggestions.get(alert_type, "Monitor closely")

    async def _send_to_channel(self, channel: AlertChannel, alert: Dict) -> None:
        """Send alert to specific channel"""
        try:
            if channel == AlertChannel.TELEGRAM:
                await self._send_telegram(alert)
            elif channel == AlertChannel.UMBRA_VOICE:
                await self._send_umbra_voice(alert)
            elif channel == AlertChannel.EMAIL:
                await self._send_email(alert)
            elif channel == AlertChannel.LOG:
                self._log_alert(alert)
        except Exception as e:
            print(f"Alert routing error to {channel.value}: {e}")

    async def _send_telegram(self, alert: Dict) -> None:
        """Send to Telegram"""
        if not self.telegram_bot:
            print(f"⚠️ AlertRouter: Telegram bot not available")
            return

        message = self._format_telegram_message(alert)

        # Actually send to Telegram
        try:
            result = self.telegram_bot.send_message(message)
            if result:
                print(f"✅ AlertRouter: Telegram alert sent for {alert.get('symbol', 'SYSTEM')}")
            else:
                print(f"⚠️ AlertRouter: Failed to send Telegram alert")
        except Exception as e:
            print(f"⚠️ AlertRouter: Telegram send error: {e}")

    async def _send_umbra_voice(self, alert: Dict) -> None:
        """Send voice alert to smart glasses"""
        voice_message = f"Alert: {alert.get('symbol', 'System')} - {alert.get('trigger_reason', 'Update')}"
        print(f"🗣️ UMBRA VOICE: {voice_message}")

    async def _send_email(self, alert: Dict) -> None:
        """Send email digest"""
        # Email implementation would go here
        print(f"📧 EMAIL ALERT: {alert.get('symbol', 'System')} queued for digest")

    def _log_alert(self, alert: Dict) -> None:
        """Log to system logs"""
        log_entry = f"[ALERT] {alert['timestamp']} - {alert['context']}"
        print(f"📝 {log_entry}")

    def _format_telegram_message(self, alert: Dict) -> str:
        """Format alert for Telegram"""
        priority_emoji = {
            AlertPriority.CRITICAL: "🚨",
            AlertPriority.HIGH: "⚡",
            AlertPriority.WATCH: "👀",
            AlertPriority.INFO: "ℹ️"
        }

        emoji = priority_emoji.get(alert.get('priority'), "📢")

        message = f"{emoji} **{alert.get('priority', 'ALERT').value}**\n"
        message += f"🎯 {alert.get('context', 'System alert')}\n"
        message += f"💡 {alert.get('action_suggestion', 'Monitor')}\n"

        if alert.get('pop'):
            message += f"📊 POP: {alert['pop']:.1f}%\n"

        if alert.get('position_size'):
            message += f"💰 Size: {alert['position_size']}\n"

        return message

# Global instance
_alert_router = None

def get_alert_router() -> AlertRouter:
    """Get singleton alert router"""
    global _alert_router
    if _alert_router is None:
        _alert_router = AlertRouter()
    return _alert_router
