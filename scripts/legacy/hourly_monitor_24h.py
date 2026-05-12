"""
24-Hour Monitoring System with Memory
Tracks processed news, analyzed stocks, and monitors uncertain opportunities
"""

import asyncio
import sys
import os
_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
from datetime import datetime, timedelta
from typing import List, Dict, Set, Optional
import json
import time

class HourlyMonitor:
    """24-hour monitoring system with persistent memory"""
    
    def __init__(self, config):
        self.config = config
        
        # Memory storage
        self.memory_file = "monitoring_memory.json"
        self.memory = self._load_memory()
        
        # Current session tracking
        self.current_news_hashed = set()
        self.current_stocks_analyzed = set()
        self.monitoring_candidates = {}  # Stocks to watch individually
        
        # Monitoring thresholds
        self.uncertainty_threshold = 0.5  # Below this = monitor individually
        self.monitoring_duration = 6  # hours to monitor uncertain stocks
        
        # Initialize components
        self._initialize_components()
    
    def _initialize_components(self):
        """Initialize necessary components"""
        print("\n🔧 Initializing 24-Hour Monitor...")
        
        # Price fetcher for real-time monitoring
        from utils.price_fetcher import get_price_fetcher
        self.price_fetcher = get_price_fetcher()
        
        # Unified brain for analysis
        from brain.unified_meta_brain import UnifiedMetaBrain
        self.unified_brain = UnifiedMetaBrain(self.config)
        
        # News sources
        from engines.news_engine_integrated import IntegratedNewsSources
        self.news_sources = IntegratedNewsSources(self.config)
        
        print("   ✅ Price Fetcher - Real-time monitoring")
        print("   ✅ Unified Brain - Analysis engine")
        print("   ✅ News Sources - 20+ feeds")
    
    def _load_memory(self) -> Dict:
        """Load persistent memory"""
        default_memory = {
            'processed_news_hashes': [],
            'analyzed_stocks': [],
            'monitoring_history': [],
            'last_run': None,
            'session_count': 0
        }
        
        try:
            with open(self.memory_file, 'r') as f:
                return json.load(f)
        except:
            return default_memory
    
    def _save_memory(self):
        """Save persistent memory"""
        # Update last run
        self.memory['last_run'] = datetime.now().isoformat()
        
        with open(self.memory_file, 'w') as f:
            json.dump(self.memory, f, indent=2)
    
    def _hash_news_item(self, news_item: Dict) -> str:
        """Create hash for news item to avoid duplicates"""
        import hashlib
        
        content = f"{news_item.get('title', '')}{news_item.get('summary', '')}{news_item.get('symbol', '')}"
        return hashlib.md5(content.encode()).hexdigest()
    
    async def run_24hour_cycle(self) -> Dict:
        """Run complete 24-hour monitoring cycle"""
        
        print("=" * 80)
        print("⏰ 24-HOUR MONITORING CYCLE STARTED")
        print("=" * 80)
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Memory: {len(self.memory['processed_news_hashes'])} news processed before")
        print(f"Monitoring: {len(self.memory['analyzed_stocks'])} stocks analyzed before")
        print("=" * 80)
        
        # Track cycle metrics
        cycle_stats = {
            'start_time': datetime.now(),
            'hours_completed': 0,
            'news_processed': 0,
            'new_news': 0,
            'stocks_analyzed': 0,
            'monitoring_candidates': 0,
            'confirmed_runs': 0,
            'price_alerts': 0
        }
        
        # Run 24 hourly cycles
        for hour in range(24):
            print(f"\n🕐 HOUR {hour + 1}/24")
            print("-" * 40)
            
            # 1. Fetch and process news
            hour_stats = await self._process_hourly_news()
            
            # 2. Monitor individual candidates
            monitoring_stats = await self._monitor_candidates()
            
            # 3. Check for confirmed runs
            run_stats = await self._check_confirmed_runs()
            
            # Update cycle stats
            cycle_stats['news_processed'] += hour_stats['news_processed']
            cycle_stats['new_news'] += hour_stats['new_news']
            cycle_stats['stocks_analyzed'] += hour_stats['stocks_analyzed']
            cycle_stats['monitoring_candidates'] += monitoring_stats['candidates']
            cycle_stats['confirmed_runs'] += run_stats['confirmed']
            cycle_stats['price_alerts'] += monitoring_stats['alerts']
            cycle_stats['hours_completed'] = hour + 1
            
            # Hourly summary
            print(f"\n   Hour {hour + 1} Summary:")
            print(f"   📰 News: {hour_stats['new_news']} new / {hour_stats['news_processed']} total")
            print(f"   📊 Stocks: {hour_stats['stocks_analyzed']} analyzed")
            print(f"   👀 Monitoring: {monitoring_stats['candidates']} candidates")
            print(f"   🚨 Alerts: {monitoring_stats['alerts']} price movements")
            
            # Save progress
            self._save_memory()
            
            # Wait for next hour (simulate - in production would be 3600 seconds)
            if hour < 23:  # Don't wait after last hour
                print(f"\n   ⏳ Waiting 60 seconds for next hour...")
                await asyncio.sleep(60)  # 1 minute for demo, use 3600 for production
        
        # Final summary
        await self._generate_final_report(cycle_stats)
        
        return cycle_stats
    
    async def _process_hourly_news(self) -> Dict:
        """Process news for current hour"""
        
        print("   📰 Processing hourly news...")
        
        # Fetch fresh news
        news_items = await self.news_sources.fetch_all_integrated_sources()
        
        stats = {
            'news_processed': len(news_items),
            'new_news': 0,
            'stocks_analyzed': 0
        }
        
        # Process each news item
        for item in news_items:
            news_hash = self._hash_news_item(item)
            
            # Check if already processed
            if news_hash in self.memory['processed_news_hashes']:
                continue
            
            # New news found
            stats['new_news'] += 1
            self.current_news_hashed.add(news_hash)
            self.memory['processed_news_hashes'].append(news_hash)
            
            # Analyze the stock
            symbol = item.get('symbol', '')
            if symbol and symbol not in self.current_stocks_analyzed:
                await self._analyze_news_item(item)
                stats['stocks_analyzed'] += 1
                self.current_stocks_analyzed.add(symbol)
                if symbol not in self.memory['analyzed_stocks']:
                    self.memory['analyzed_stocks'].append(symbol)
        
        print(f"   ✅ Processed {stats['new_news']} new news items")
        return stats
    
    async def _analyze_news_item(self, news_item: Dict):
        """Analyze individual news item"""
        
        symbol = news_item.get('symbol', '')
        if not symbol:
            return
        
        # Quick confidence check
        confidence = news_item.get('confidence', 0.5)
        
        if confidence < self.uncertainty_threshold:
            # Uncertain - add to monitoring
            if symbol not in self.monitoring_candidates:
                self.monitoring_candidates[symbol] = {
                    'initial_news': news_item,
                    'confidence': confidence,
                    'start_time': datetime.now(),
                    'price_history': [],
                    'alerts_triggered': []
                }
                print(f"   👀 Added {symbol} to monitoring (confidence: {confidence:.1%})")
        else:
            # High confidence - potential run
            print(f"   🚀 High confidence signal: {symbol} ({confidence:.1%})")
    
    async def _monitor_candidates(self) -> Dict:
        """Monitor stocks with uncertain signals"""
        
        stats = {
            'candidates': len(self.monitoring_candidates),
            'alerts': 0
        }
        
        if not self.monitoring_candidates:
            return stats
        
        print(f"   👀 Monitoring {len(self.monitoring_candidates)} candidates...")
        
        # Check each candidate
        for symbol, data in list(self.monitoring_candidates.items()):
            # Get current price
            price = self.price_fetcher.get_real_price(symbol)
            if price:
                current_price = float(price)
                data['price_history'].append({
                    'price': current_price,
                    'timestamp': datetime.now()
                })
                
                # Check for significant movement
                if len(data['price_history']) > 1:
                    prev_price = data['price_history'][0]['price']
                    change_pct = (current_price - prev_price) / prev_price
                    
                    # Alert on 5% movement
                    if abs(change_pct) >= 0.05:
                        direction = "↑" if change_pct > 0 else "↓"
                        alert = f"{direction} {symbol}: {change_pct:.1%} (${prev_price:.2f} → ${current_price:.2f})"
                        print(f"   🚨 {alert}")
                        data['alerts_triggered'].append(alert)
                        stats['alerts'] += 1
                        
                        # Remove if confirmed movement
                        if abs(change_pct) >= 0.10:  # 10% confirmed
                            print(f"   ✅ Confirmed movement in {symbol} - removing from monitoring")
                            del self.monitoring_candidates[symbol]
            
            # Remove old candidates (after monitoring_duration hours)
            if (datetime.now() - data['start_time']).total_seconds() > (self.monitoring_duration * 3600):
                print(f"   ⏰ {symbol} monitoring expired")
                del self.monitoring_candidates[symbol]
        
        return stats
    
    async def _check_confirmed_runs(self) -> Dict:
        """Check for confirmed bull runs from monitoring"""
        
        stats = {'confirmed': 0}
        
        # In production, this would run full analysis on alerted stocks
        # For now, just count alerts as potential confirms
        for symbol, data in self.monitoring_candidates.items():
            if len(data['alerts_triggered']) > 0:
                stats['confirmed'] += 1
        
        return stats
    
    async def _generate_final_report(self, cycle_stats: Dict):
        """Generate final 24-hour report"""
        
        print("\n" + "=" * 80)
        print("📊 24-HOUR MONITORING COMPLETE")
        print("=" * 80)
        
        duration = datetime.now() - cycle_stats['start_time']
        
        print(f"\n⏰ Duration: {duration}")
        print(f"📰 Total News Processed: {cycle_stats['news_processed']}")
        print(f"🆕 New News Found: {cycle_stats['new_news']}")
        print(f"📊 Stocks Analyzed: {cycle_stats['stocks_analyzed']}")
        print(f"👀 Monitoring Candidates: {cycle_stats['monitoring_candidates']}")
        print(f"🚨 Price Alerts: {cycle_stats['price_alerts']}")
        print(f"🚀 Confirmed Runs: {cycle_stats['confirmed_runs']}")
        
        # Memory efficiency
        memory_efficiency = (cycle_stats['new_news'] / max(cycle_stats['news_processed'], 1)) * 100
        print(f"\n💾 Memory Efficiency: {memory_efficiency:.1f}% new news (avoided duplicates)")
        
        # Still monitoring
        if self.monitoring_candidates:
            print(f"\n👀 Still Monitoring: {len(self.monitoring_candidates)} stocks")
            for symbol, data in self.monitoring_candidates.items():
                print(f"   • {symbol}: {len(data['price_history'])} price points, {len(data['alerts_triggered'])} alerts")
        
        # Save final memory state
        self.memory['session_count'] += 1
        self._save_memory()
        
        print(f"\n✅ Session #{self.memory['session_count']} complete")
        print(f"💾 Memory saved to {self.memory_file}")

# Main execution
async def run_24hour_monitor():
    """Run 24-hour monitoring cycle"""
    
    print("=" * 80)
    print("⏰ STARTING 24-HOUR MONITORING SYSTEM")
    print("=" * 80)
    print("Features:")
    print("✅ Remembers processed news (no duplicates)")
    print("✅ Tracks analyzed stocks")
    print("✅ Monitors uncertain stocks individually")
    print("✅ Price movement alerts")
    print("✅ Persistent memory storage")
    print("=" * 80)
    
    # Load config
    from config.secure_config import config
    
    # Initialize and run
    monitor = HourlyMonitor(config)
    results = await monitor.run_24hour_cycle()
    
    return results

if __name__ == "__main__":
    results = asyncio.run(run_24hour_monitor())
    
    print(f"\n🎉 24-Hour Complete!")
    print(f"📊 Processed {results['news_processed']} news items")
    print(f"🚀 Found {results['confirmed_runs']} confirmed runs")
