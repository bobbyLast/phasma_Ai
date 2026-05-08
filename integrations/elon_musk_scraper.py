
"""
Elon Musk Twitter Scraper
Scrapes Elon Musk's tweets for stock mentions and sentiment
"""

import requests
import re
from datetime import datetime

class ElonMuskScraper:
    def __init__(self):
        self.base_url = "https://nitter.net/elonmusk"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    def get_latest_tweets(self, count=10):
        """Get latest tweets from Elon Musk"""
        try:
            url = f"{self.base_url}?max={count}"
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(response.text, 'html.parser')
                
                tweets = []
                tweet_elements = soup.find_all('div', class_='tweet-content')
                
                for tweet_elem in tweet_elements[:count]:
                    tweet_text = tweet_elem.get_text(strip=True)
                    tweet_time = tweet_elem.find('span', class_='tweet-date')
                    
                    # Extract tickers
                    tickers = re.findall(r'\$[A-Z]{1,5}', tweet_text)
                    
                    # Check for Tesla/crypto mentions
                    tesla_keywords = ['tesla', 'TSLA', 'cybertruck', 'model 3', 'model y']
                    crypto_keywords = ['bitcoin', 'BTC', 'dogecoin', 'DOGE', 'crypto']
                    
                    sentiment = {
                        'tesla_mention': any(kw in tweet_text.lower() for kw in tesla_keywords),
                        'crypto_mention': any(kw in tweet_text.lower() for kw in crypto_keywords),
                        'tickers': tickers
                    }
                    
                    tweets.append({
                        'text': tweet_text,
                        'time': tweet_time.get_text() if tweet_time else '',
                        'sentiment': sentiment
                    })
                
                return tweets
        except Exception as e:
            print(f"Error scraping tweets: {e}")
            return []
    
    def get_market_moving_tweets(self):
        """Get tweets that mention stocks/crypto"""
        tweets = self.get_latest_tweets(20)
        
        market_tweets = []
        for tweet in tweets:
            if (tweet['sentiment']['tesla_mention'] or 
                tweet['sentiment']['crypto_mention'] or 
                tweet['sentiment']['tickers']):
                market_tweets.append(tweet)
        
        return market_tweets

# Usage example
if __name__ == "__main__":
    scraper = ElonMuskScraper()
    tweets = scraper.get_market_moving_tweets()
    
    for tweet in tweets:
        print(f"Tweet: {tweet['text'][:100]}...")
        print(f"Tesla: {tweet['sentiment']['tesla_mention']}")
        print(f"Crypto: {tweet['sentiment']['crypto_mention']}")
        print(f"Tickers: {tweet['sentiment']['tickers']}")
        print("-" * 40)
        