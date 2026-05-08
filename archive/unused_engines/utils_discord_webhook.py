""
Discord Webhook Integration
Handles sending formatted messages to Discord via webhooks
"""

import aiohttp
import json
import logging
from typing import Dict, Optional, Any

class DiscordWebhook:
    """Handles sending messages to Discord via webhook"""
    
    def __init__(self, webhook_url: str):
        """Initialize with Discord webhook URL"""
        self.webhook_url = webhook_url
        self.session = None
        self.logger = logging.getLogger(__name__)
    
    async def _ensure_session(self):
        """Ensure we have an active aiohttp session"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
    
    async def send_alert(self, message: str, embed: Optional[Dict[str, Any]] = None) -> bool:
        """
        Send an alert to Discord
        
        Args:
            message: The message to send
            embed: Optional rich embed (see Discord webhook docs)
            
        Returns:
            bool: True if successful, False otherwise
        """
        await self._ensure_session()
        
        payload = {
            'content': message,
            'username': 'Phasma AI Alerts',
            'avatar_url': 'https://i.imgur.com/your-logo.png',  # Replace with your logo
        }
        
        if embed:
            payload['embeds'] = [embed]
        
        try:
            async with self.session.post(
                self.webhook_url,
                data=json.dumps(payload),
                headers={'Content-Type': 'application/json'}
            ) as response:
                if response.status == 204:
                    self.logger.info("Successfully sent Discord alert")
                    return True
                else:
                    error_text = await response.text()
                    self.logger.error(
                        f"Failed to send Discord alert. Status: {response.status}, Response: {error_text}"
                    )
                    return False
                    
        except Exception as e:
            self.logger.error(f"Error sending Discord alert: {e}", exc_info=True)
            return False
    
    async def close(self):
        """Close the aiohttp session"""
        if self.session and not self.session.closed:
            await self.session.close()
    
    def __del__(self):
        """Ensure session is closed when object is destroyed"""
        if self.session and not self.session.closed:
            if self.session._loop.is_running():
                self.session._loop.create_task(self.session.close())

# Example usage
async def example():
    webhook = DiscordWebhook("YOUR_WEBHOOK_URL")
    
    # Simple message
    await webhook.send_alert("🚀 New trading opportunity!")
    
    # Message with embed
    embed = {
        'title': 'NVDA - NVIDIA Corporation',
        'description': 'New partnership with major tech company',
        'color': 0x00ff00,  # Green
        'fields': [
            {'name': 'Entry', 'value': '$450.00', 'inline': True},
            {'name': 'Target', 'value': '$650.00', 'inline': True},
            {'name': 'Upside', 'value': '44.4%', 'inline': True},
            {'name': 'Confidence', 'value': '8.5/10', 'inline': True},
            {'name': 'Time Horizon', 'value': '3-6 months', 'inline': True},
        ],
        'footer': {
            'text': 'Phasma AI | ' + datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')
        }
    }
    
    await webhook.send_alert("📈 New Long Opportunity", embed=embed)
    await webhook.close()

if __name__ == "__main__":
    import asyncio
    asyncio.run(example())
