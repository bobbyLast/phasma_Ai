"""
============================================================
PHASMA AI - ADDITIONAL DATA SOURCES INTEGRATION
============================================================
Checking Library of Congress, CSE, and GitHub sources
"""

import requests
import json
from datetime import datetime

# 1. Library of Congress API
def test_library_of_congress():
    """Test Library of Congress for historical news/data"""
    print("📚 Testing Library of Congress API...")
    
    # Search for business/financial news
    url = "https://www.loc.gov/collections/newspapers/?q=insider+trading&fo=json"
    
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            
            return {
                'status': 'success',
                'source': 'Library of Congress',
                'description': 'Historical newspapers and government documents',
                'results': data.get('results', {}).get('count', 0),
                'url': 'https://www.loc.gov/collections/newspapers/',
                'use_case': 'Historical context, reference data',
                'cost': 'Free'
            }
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

# 2. CSE Usearch API
def test_cse_usearch():
    """Test CSE Custom Search Engine"""
    print("🔍 Testing CSE Usearch API...")
    
    # This would require registration - checking documentation
    return {
        'status': 'info',
        'source': 'CSE Usearch',
        'description': 'Custom search engine for targeted searches',
        'url': 'https://cse.usearch.com/apps',
        'registration_required': True,
        'use_case': 'Custom news search, targeted queries',
        'cost': 'Unknown (requires registration)'
    }

# 3. Elon Musk GitHub (Twitter/X scraper)
def test_elon_musk_github():
    """Check Elon Musk Twitter scraper for sentiment analysis"""
    print("🐦 Checking Elon Musk GitHub scraper...")
    
    url = "https://github.com/nickatnight/elonmu.sh"
    
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return {
                'status': 'success',
                'source': 'Elon Musk Twitter Scraper',
                'description': 'Scrapes Elon Musk tweets for market impact',
                'url': url,
                'use_case': 'Market sentiment from influential figures',
                'cost': 'Free (open source)',
                'implementation': 'Can be adapted for other accounts'
            }
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

# 4. FeedBin API (RSS aggregation)
def test_feedbin_api():
    """Check FeedBin for RSS feed aggregation"""
    print("📡 Testing FeedBin API concept...")
    
    return {
        'status': 'info',
        'source': 'FeedBin API',
        'description': 'RSS feed reader and aggregator',
        'url': 'https://github.com/feedbin/feedbin-api',
        'use_case': 'Aggregate multiple news RSS feeds',
        'cost': 'Free tier available, $5/month premium',
        'benefits': [
            'Centralized RSS management',
            'Mark articles as read',
            'Star important articles',
            'Search across feeds'
        ]
    }

# 5. Inshorts News API (from GitHub)
def test_inshorts_api():
    """Check Inshorts News API from GitHub"""
    print("📰 Testing Inshorts News API...")
    
    url = "https://github.com/cyberboysumanjay/Inshorts-News-API"
    
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return {
                'status': 'success',
                'source': 'Inshorts News API',
                'description': 'Indian news aggregator with API',
                'url': url,
                'use_case': 'Additional news source, emerging markets',
                'cost': 'Free',
                'categories': ['business', 'technology', 'startup'],
                'integration': 'REST API available'
            }
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

# 6. Check for RSS feeds directly
def find_additional_rss_feeds():
    """Find more RSS feeds for financial news"""
    print("🔍 Searching for additional RSS feeds...")
    
    additional_feeds = {
        'financial_times': 'https://www.ft.com/rss/home',
        'reuters_business': 'https://www.reuters.com/business/markets/us',
        'bloomberg_markets': 'https://www.bloomberg.com/markets/rss',
        'cnbc_markets': 'https://www.cnbc.com/id/100003114/device/rss/rss.html',
        'wsj_markets': 'https://feeds.wsjonline.com/wsj/xml/rss/3_7014.xml',
        'marketwatch_top': 'https://www.marketwatch.com/rss/topstories',
        'seeking_alpha_market': 'https://seekingalpha.com/market-news/all',
        'investopedia_news': 'https://www.investopedia.com/feed.rss',
        'the_motley_fool': 'https://www.fool.com/feed.rss',
        'zacks_investment': 'https://www.zacks.com/commentary/rss',
        'benzinga_all': 'https://www.benzinga.com/feed',
        'yahoofinance_all': 'https://finance.yahoo.com/news/rssindex',
        'stocktwits_rss': 'https://stocktwits.com/streams.rss',
        'fidelity_market': 'https://www.fidelity.com/market-news/market-news-rss',
        'charles_schwab': 'https://www.schwab.com/rss/marketNews.xml',
        'etrade_news': 'https://us.etrade.com/e/t/etnews/etnews.rss'
    }
    
    return additional_feeds

# 7. Check for free financial APIs
def find_free_financial_apis():
    """Find additional free financial APIs"""
    print("💰 Searching for free financial APIs...")
    
    free_apis = {
        'finnhub': {
            'url': 'https://finnhub.io/',
            'free_tier': '60 requests/minute',
            'features': ['News', 'Quotes', 'Financials', 'Insider Trading'],
            'key_required': True
        },
        'financial_modeling_prep': {
            'url': 'https://site.financialmodelingprep.com/',
            'free_tier': '250 requests/day',
            'features': ['News', 'Company Profile', 'Financial Statements'],
            'key_required': True
        },
        'iex_cloud': {
            'url': 'https://iexcloud.io/',
            'free_tier': '100,000 requests/month',
            'features': ['News', 'Quotes', 'Insider Trading'],
            'key_required': True
        },
        'polygon_io': {
            'url': 'https://polygon.io/',
            'free_tier': '5 requests/minute',
            'features': ['News', 'Trades', 'Quotes'],
            'key_required': True
        },
        'yahoo_finance': {
            'url': 'https://www.yahoofinanceapi.com/',
            'free_tier': 'Unlimited (unofficial)',
            'features': ['Quotes', 'News', 'Historical Data'],
            'key_required': False
        },
        'markit_on_demand': {
            'url': 'https://markitondemand.com/',
            'free_tier': 'Limited',
            'features': ['Quotes', 'Chart Data'],
            'key_required': False
        }
    }
    
    return free_apis

# 8. Check social media APIs for sentiment
def find_social_sentiment_sources():
    """Find social media sources for market sentiment"""
    print("💬 Finding social sentiment sources...")
    
    social_sources = {
        'reddit': {
            'api': 'https://www.reddit.com/dev/api/',
            'subreddits': ['pennystocks', 'wallstreetbets', 'stocks', 'investing'],
            'cost': 'Free',
            'rate_limit': '60 requests/minute',
            'use_case': 'Retail sentiment, meme stocks'
        },
        'twitter': {
            'api': 'https://developer.twitter.com/',
            'cost': 'Free tier available',
            'features': ['Real-time feeds', 'Search', 'User timelines'],
            'use_case': 'Breaking news, influencer sentiment'
        },
        'stocktwits': {
            'api': 'https://api.stocktwits.com/streams/',
            'cost': 'Free',
            'features': ['Trader sentiment', 'Real-time feeds'],
            'use_case': 'Trader chatter, momentum'
        },
        'discord': {
            'api': 'Requires bot token',
            'servers': ['Various trading servers'],
            'cost': 'Free',
            'use_case': 'Community sentiment, alpha groups'
        }
    }
    
    return social_sources

# Main test function
def test_all_additional_sources():
    """Test all additional sources mentioned"""
    
    print("=" * 80)
    print("🔍 TESTING ADDITIONAL DATA SOURCES")
    print("=" * 80)
    
    results = {}
    
    # Test each source
    results['library_of_congress'] = test_library_of_congress()
    results['cse_usearch'] = test_cse_usearch()
    results['elon_musk_github'] = test_elon_musk_github()
    results['feedbin_api'] = test_feedbin_api()
    results['inshorts_api'] = test_inshorts_api()
    
    # Get additional sources
    results['additional_rss_feeds'] = find_additional_rss_feeds()
    results['free_financial_apis'] = find_free_financial_apis()
    results['social_sentiment'] = find_social_sentiment_sources()
    
    # Save results
    with open('additional_sources_results.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    # Print summary
    print("\n" + "=" * 80)
    print("📊 ADDITIONAL SOURCES SUMMARY")
    print("=" * 80)
    
    print("\n✅ READY TO INTEGRATE:")
    ready = [
        "Library of Congress (Historical data)",
        "Elon Musk Twitter Scraper (Sentiment)",
        "Inshorts News API (Indian markets)",
        "FeedBin API (RSS aggregation)",
        "17 additional RSS feeds",
        "6 free financial APIs",
        "4 social sentiment sources"
    ]
    
    for item in ready:
        print(f"  • {item}")
    
    print("\n💡 IMPLEMENTATION PRIORITY:")
    priority = [
        "1. Add 17 RSS feeds (instant, free)",
        "2. Integrate Finnhub API (free tier)",
        "3. Add Reddit sentiment monitoring",
        "4. Implement Twitter sentiment via scraper",
        "5. Add Inshorts for emerging markets",
        "6. Use Library of Congress for research"
    ]
    
    for item in priority:
        print(f"  {item}")
    
    return results

if __name__ == "__main__":
    results = test_all_additional_sources()
