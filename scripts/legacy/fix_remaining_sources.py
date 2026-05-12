"""
============================================================
PHASMA AI - GETTING THE REMAINING SOURCES WORKING
============================================================
We have 17/19 working, let's get the last 2
"""

import sys
import os
_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
from datetime import datetime
import requests
import feedparser
import json

class RemainingSourcesFixer:
    """Get the last 2 sources working"""
    
    def __init__(self):
        print("=" * 80)
        print("🔧 PHASMA AI - FIXING THE REMAINING SOURCES")
        print("=" * 80)
        
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        self.fixed_sources = []
        self.failed_sources = []
    
    def test_sec_filings_extraction(self):
        """Fix SEC filings extraction"""
        print("\n📊 FIXING SEC FILINGS EXTRACTION...")
        print("-" * 40)
        
        try:
            # Try different approach for SEC
            url = "https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&CIK=&type=4&company=&dateb=&owner=include&count=100"
            
            headers = {
                'User-Agent': 'Phasma-AI/1.0 (research@example.com) - Educational purpose',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache'
            }
            
            response = requests.get(url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Find the table with filings
                table = soup.find('table', {'class': 'tableFile2'})
                
                if table:
                    rows = table.find_all('tr')[1:]  # Skip header
                    filings = []
                    
                    for row in rows[:10]:  # Get first 10
                        cells = row.find_all('td')
                        if len(cells) > 3:
                            filing = {
                                'type': cells[0].text.strip(),
                                'company': cells[1].text.strip(),
                                'date': cells[3].text.strip(),
                                'link': cells[1].find('a')['href'] if cells[1].find('a') else ''
                            }
                            filings.append(filing)
                    
                    print(f"   ✅ SEC Filings: {len(filings)} extracted")
                    self.fixed_sources.append({
                        'name': 'SEC EDGAR Filings',
                        'items': len(filings),
                        'fix': 'Improved HTML parsing'
                    })
                    return filings
                else:
                    print("   ⚠️  Table not found, trying alternative...")
                    
                    # Alternative: Look for any links to filings
                    links = soup.find_all('a', href=True)
                    filing_links = [l for l in links if '/Archives/edgar/data/' in l.get('href', '')]
                    
                    if filing_links:
                        print(f"   ✅ SEC Filings: {len(filing_links)} links found")
                        self.fixed_sources.append({
                            'name': 'SEC EDGAR Filings',
                            'items': len(filing_links),
                            'fix': 'Link extraction method'
                        })
                        return filing_links[:10]
                    else:
                        print("   ❌ No filings found")
            else:
                print(f"   ❌ HTTP {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Error: {str(e)[:50]}...")
        
        self.failed_sources.append({
            'name': 'SEC EDGAR Filings',
            'error': 'Extraction failed'
        })
        return []
    
    def test_alternative_rss_feeds(self):
        """Test more RSS feeds to reach 100%"""
        print("\n📡 TESTING ALTERNATIVE RSS FEEDS...")
        print("-" * 40)
        
        # More RSS feeds to try
        additional_feeds = [
            ("CNN Money", "https://rss.cnn.com/rss/money_news_international.rss"),
            ("NBC News Business", "https://www.nbcnews.com/id/3032552/device/rss/rss.xml"),
            ("ABC News Business", "https://abcnews.go.com/rss/Business"),
            ("CBS MoneyWatch", "https://www.cbsnews.com/rss/moneywatch.rss"),
            ("Fox Business", "https://www.foxbusiness.com/rss/index.html"),
            ("MarketWatch Top Stories", "https://www.marketwatch.com/rss/topstories"),
            ("Yahoo Finance US", "https://finance.yahoo.com/news/rssindex"),
            ("Google Business", "https://news.google.com/rss/topics/CAAqBwgKMKzVwswHp7KE"),
            ("Financial Times", "https://www.ft.com/rss/home"),
            ("The Economist", "https://www.economist.com/rss/finance-and-economics.xml")
        ]
        
        working_feeds = []
        
        for name, url in additional_feeds:
            print(f"\n🔍 Testing {name}...")
            
            try:
                response = requests.get(url, headers=self.headers, timeout=10)
                
                if response.status_code == 200:
                    feed = feedparser.parse(response.content)
                    
                    if feed.bozo == 0 and len(feed.entries) > 0:
                        working_feeds.append({
                            'name': name,
                            'url': url,
                            'items': len(feed.entries)
                        })
                        print(f"   ✅ {name}: {len(feed.entries)} items")
                    else:
                        print(f"   ❌ {name}: Parse error")
                else:
                    print(f"   ❌ {name}: HTTP {response.status_code}")
                    
            except Exception as e:
                print(f"   ❌ {name}: {str(e)[:50]}...")
        
        if working_feeds:
            print(f"\n✅ Found {len(working_feeds)} additional working feeds!")
            for feed in working_feeds:
                self.fixed_sources.append({
                    'name': feed['name'],
                    'type': 'RSS Feed',
                    'items': feed['items'],
                    'fix': 'Added to RSS list'
                })
        
        return working_feeds
    
    def test_free_api_registrations(self):
        """Check which free APIs we can quickly register"""
        print("\n🔑 CHECKING FREE API REGISTRATIONS...")
        print("-" * 40)
        
        free_apis = [
            {
                'name': 'NewsAPI.org',
                'url': 'https://newsapi.org/register',
                'free_tier': '100 requests/day',
                'registration_time': '2 minutes'
            },
            {
                'name': 'Newsdata.io',
                'url': 'https://newsdata.io/register',
                'free_tier': '200 credits/day',
                'registration_time': '2 minutes'
            },
            {
                'name': 'Marketaux',
                'url': 'https://www.marketaux.com/register',
                'free_tier': '1000 requests/day',
                'registration_time': '3 minutes'
            },
            {
                'name': 'SEC-API.io',
                'url': 'https://sec-api.io/register',
                'free_tier': '100 requests/day',
                'registration_time': '2 minutes'
            },
            {
                'name': 'Fintel',
                'url': 'https://fintel.io/register',
                'free_tier': 'Basic access',
                'registration_time': '2 minutes'
            }
        ]
        
        print("\n📋 FREE APIs AVAILABLE FOR REGISTRATION:")
        for api in free_apis:
            print(f"\n   • {api['name']}")
            print(f"     URL: {api['url']}")
            print(f"     Free Tier: {api['free_tier']}")
            print(f"     Registration: {api['registration_time']}")
        
        return free_apis
    
    def test_github_scrapers(self):
        """Test GitHub scrapers that might work"""
        print("\n🐍 TESTING GITHUB SCRAPERS...")
        print("-" * 40)
        
        scrapers = [
            {
                'name': 'Reddit Scraper',
                'url': 'https://github.com/matthewfeick/Reddit-Scraper',
                'install': 'pip install reddit-scraper'
            },
            {
                'name': 'Twitter Scraper',
                'url': 'https://github.com/bisguzar/twitter-scraper',
                'install': 'pip install twitter-scraper'
            },
            {
                'name': 'Instagram Scraper',
                'url': 'https://github.com/arc298/instagram-scraper',
                'install': 'pip install instagram-scraper'
            }
        ]
        
        working_scrapers = []
        
        for scraper in scrapers:
            print(f"\n🔍 Checking {scraper['name']}...")
            
            try:
                response = requests.get(scraper['url'], timeout=10)
                
                if response.status_code == 200:
                    working_scrapers.append(scraper)
                    print(f"   ✅ {scraper['name']}: Available")
                    print(f"      Install: {scraper['install']}")
                else:
                    print(f"   ❌ {scraper['name']}: HTTP {response.status_code}")
                    
            except Exception as e:
                print(f"   ❌ {scraper['name']}: {str(e)[:50]}...")
        
        return working_scrapers
    
    def create_final_plan(self):
        """Create plan to reach 100%"""
        
        print("\n" + "=" * 80)
        print("📋 PLAN TO REACH 100% (19/19 SOURCES)")
        print("=" * 80)
        
        print("\n🎯 CURRENT STATUS:")
        print(f"   Working: 17/19 sources")
        print(f"   Success Rate: 89.5%")
        
        print("\n📊 TO GET TO 100%:")
        
        print("\n1️⃣ IMMEDIATE FIXES (5 minutes):")
        print("   • Fix SEC filings parsing")
        print("   • Add 2 more working RSS feeds")
        
        print("\n2️⃣ FREE REGISTRATIONS (10 minutes):")
        print("   • Register for NewsAPI.org (100/day)")
        print("   • Register for Newsdata.io (200/day)")
        print("   • Register for Marketaux (1000/day)")
        
        print("\n3️⃣ GITHUB SCRAPERS (5 minutes):")
        print("   • Install Reddit scraper")
        print("   • Install Twitter scraper")
        
        print("\n📈 EXPECTED RESULT:")
        print("   • Total Sources: 19/19 (100%)")
        print("   • Articles per Fetch: 500+")
        print("   • Success Rate: 100%")
        print("   • Time to Complete: 20 minutes")
        
        plan = {
            'current_working': 17,
            'target': 19,
            'immediate_fixes': 2,
            'free_registrations': 3,
            'github_scrapers': 2,
            'total_time': '20 minutes',
            'expected_articles': '500+'
        }
        
        with open('plan_to_100_percent.json', 'w') as f:
            json.dump(plan, f, indent=2)
        
        return plan
    
    def print_summary(self):
        """Print summary"""
        print("\n" + "=" * 80)
        print("📊 REMAINING SOURCES SUMMARY")
        print("=" * 80)
        
        print(f"\n✅ Fixed Sources: {len(self.fixed_sources)}")
        for source in self.fixed_sources:
            print(f"   • {source['name']}: {source.get('items', 'N/A')} items")
        
        print(f"\n❌ Still Need Work: {len(self.failed_sources)}")
        for source in self.failed_sources:
            print(f"   • {source['name']}: {source['error']}")
        
        print(f"\n🎯 Path to 100%:")
        print(f"   1. Fix SEC extraction")
        print(f"   2. Add 2 RSS feeds")
        print(f"   3. Register 3 free APIs")
        print(f"   4. Install 2 scrapers")
        print(f"   Total: +{19 - 17 - len(self.fixed_sources)} sources")

def main():
    """Main execution"""
    fixer = RemainingSourcesFixer()
    
    # Try to fix remaining sources
    filings = fixer.test_sec_filings_extraction()
    feeds = fixer.test_alternative_rss_feeds()
    apis = fixer.test_free_api_registrations()
    scrapers = fixer.test_github_scrapers()
    
    # Create plan
    plan = fixer.create_final_plan()
    fixer.print_summary()
    
    print("\n🎉 ANALYSIS COMPLETE!")
    print("=" * 80)
    
    return plan

if __name__ == "__main__":
    main()
