"""
============================================================
PHASMA AI - DATA INTEGRATION PLAN
============================================================
Using your provided API keys and sources
"""

import requests
import feedparser
import json
from datetime import datetime

# 1. WORLD NEWS API
def test_world_news_api():
    """Test World News API"""
    api_key = "370a193337cf422b9e4df80b0d37613d"
    url = f"https://api.worldnewsapi.com/search-news?api-key={api_key}&text=insider%20trading&source=cnn,bbc,reuters"
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            return {
                'status': 'success',
                'articles': data.get('news', [])[:5],
                'total': len(data.get('news', []))
            }
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

# 2. INSHORTS NEWS API (GitHub)
def test_inshorts_api():
    """Test Inshorts News API from GitHub"""
    # This appears to be a web scraper, not a direct API
    # Would need to implement the scraper from the GitHub repo
    return {
        'status': 'info',
        'message': 'Inshorts requires web scraping implementation',
        'github': 'https://github.com/cyberboysumanjay/Inshorts-News-API'
    }

# 3. GNEWS API
def test_gnews_api():
    """Test GNews API"""
    api_key = "ae4d97e15c89d379dcc9c96174a39ed4"
    url = f"https://gnews.io/api/v4/search?q=insider%20trading%20stock&lang=en&country=us&max=10&apikey={api_key}"
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            return {
                'status': 'success',
                'articles': data.get('articles', [])[:5],
                'total': data.get('totalArticles', 0)
            }
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

# 4. MEDIASTACK API
def test_mediastack_api():
    """Test MediaStack API"""
    api_key = "ca12fc893f4d0ed4e4b3c7d4e72808b9"
    url = f"http://api.mediastack.com/v1/news?access_key={api_key}&keywords=insider%20trading&countries=us&limit=10"
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            return {
                'status': 'success',
                'articles': data.get('data', [])[:5],
                'total': len(data.get('data', []))
            }
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

# 5. CURRENTS API
def test_currents_api():
    """Test Currents API"""
    api_key = "AABfmJz5G8qskiJGNSZxcDXNkzySLreGywQKVloobm-QnEaj"
    url = f"https://api.currentsapi.services/v1/latest-news?apiKey={api_key}&category=business&keywords=insider%20trading"
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            return {
                'status': 'success',
                'articles': data.get('news', [])[:5],
                'total': len(data.get('news', []))
            }
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

# 6. SEC EDGAR RSS (Free)
def fetch_sec_form4():
    """Fetch SEC Form 4 filings"""
    url = "https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&CIK=&type=4&company=&dateb=&owner=include&count=100"
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            # Parse the HTML to extract filing links
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')
            
            filings = []
            # Extract filing links and dates
            # This is simplified - would need full parsing
            return {
                'status': 'success',
                'source': 'SEC EDGAR',
                'message': 'RSS feed accessible, parsing needed'
            }
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

# 7. Seeking Alpha RSS (Free)
def fetch_seeking_alpha_rss():
    """Fetch Seeking Alpha RSS feed"""
    url = "https://seekingalpha.com/feed.xml"
    
    try:
        feed = feedparser.parse(url)
        articles = []
        
        for entry in feed.entries[:5]:
            articles.append({
                'title': entry.title,
                'link': entry.link,
                'published': entry.published,
                'summary': entry.summary[:200] if hasattr(entry, 'summary') else ''
            })
        
        return {
            'status': 'success',
            'source': 'Seeking Alpha RSS',
            'articles': articles,
            'total': len(feed.entries)
        }
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

# 8. Check Library of Congress API
def test_loc_api():
    """Check Library of Congress API for news/government data"""
    url = "https://www.loc.gov/collections/newspapers/?q=insider+trading&fo=json"
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            return {
                'status': 'info',
                'source': 'Library of Congress',
                'message': 'Historical newspapers available',
                'results': data.get('results', {}).get('count', 0)
            }
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

# 9. Check CSE API
def test_cse_api():
    """Check CSE Usearch API"""
    # This appears to be a custom search engine
    return {
        'status': 'info',
        'source': 'CSE Usearch',
        'message': 'Custom search engine - may require registration'
    }

# 10. Check Elon Musk GitHub (for Twitter/X data)
def check_elon_musk_github():
    """Check Elon Musk scraper GitHub"""
    return {
        'status': 'info',
        'source': 'Elon Musk GitHub',
        'message': 'Twitter/X scraper for Elon Musk tweets',
        'potential_use': 'Could be adapted for insider sentiment analysis',
        'github': 'https://github.com/nickatnight/elonmu.sh'
    }

# 11. Check FeedBin API
def check_feedbin_api():
    """Check FeedBin API for RSS aggregation"""
    return {
        'status': 'info',
        'source': 'FeedBin API',
        'message': 'RSS feed reader service - could aggregate multiple news sources',
        'github': 'https://github.com/feedbin/feedbin-api'
    }

# 12. Alternative Options Flow Sources (Free/Cheap)
def find_alternatives_to_unusual_whales():
    """Find alternatives to Unusual Whales"""
    alternatives = [
        {
            'name': 'Yahoo Finance Options',
            'url': 'https://query1.finance.yahoo.com/v7/finance/options/{symbol}',
            'cost': 'Free',
            'notes': 'Basic options data, no unusual flow detection'
        },
        {
            'name': 'Finviz',
            'url': 'https://finviz.com/screener.ashx',
            'cost': 'Free tier available',
            'notes': 'Has unusual volume screener'
        },
        {
            'name': 'Barchart',
            'url': 'https://www.barchart.com/stocks/flows/strange',
            'cost': 'Free tier available',
            'notes': 'Shows unusual options activity'
        },
        {
            'name': 'OptionStrat',
            'url': 'https://optionstrat.com/unusual-options-activity',
            'cost': 'Free',
            'notes': 'Free unusual options scanner'
        }
    ]
    
    return alternatives

# Test all APIs
def test_all_apis():
    """Test all available APIs"""
    results = {}
    
    print("Testing News APIs...")
    results['world_news'] = test_world_news_api()
    results['gnews'] = test_gnews_api()
    results['mediastack'] = test_mediastack_api()
    results['currents'] = test_currents_api()
    
    print("Testing RSS Feeds...")
    results['sec_edgar'] = fetch_sec_form4()
    results['seeking_alpha'] = fetch_seeking_alpha_rss()
    
    print("Checking other sources...")
    results['loc'] = test_loc_api()
    results['cse'] = test_cse_api()
    results['elon_musk'] = check_elon_musk_github()
    results['feedbin'] = check_feedbin_api()
    results['options_alternatives'] = find_alternatives_to_unusual_whales()
    
    return results

if __name__ == "__main__":
    # Run tests
    api_results = test_all_apis()
    
    # Save results
    with open('api_test_results.json', 'w') as f:
        json.dump(api_results, f, indent=2, default=str)
    
    # Print summary
    print("\n" + "="*80)
    print("API TEST SUMMARY")
    print("="*80)
    
    for api, result in api_results.items():
        status = result.get('status', 'info')
        if status == 'success':
            print(f"✅ {api.upper()}: Working - {result.get('total', 0)} items found")
        elif status == 'error':
            print(f"❌ {api.upper()}: Error - {result.get('message', 'Unknown error')}")
        else:
            print(f"ℹ️  {api.upper()}: {result.get('message', 'No data')}")
