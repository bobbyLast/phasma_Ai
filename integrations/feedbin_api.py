
# FeedBin API Integration Example
import requests
import base64

class FeedBinAPI:
    def __init__(self, username, password):
        self.auth = base64.b64encode(f"{username}:{password}".encode()).decode()
        self.headers = {
            'Authorization': f'Basic {self.auth}',
            'Content-Type': 'application/json'
        }
        self.base_url = 'https://api.feedbin.com/v2/'
    
    def add_subscription(self, feed_url):
        """Add RSS feed to FeedBin"""
        url = f"{self.base_url}subscriptions.json"
        data = {'feed_url': feed_url}
        response = requests.post(url, headers=self.headers, json=data)
        return response.json()
    
    def get_entries(self, since=None):
        """Get entries from feeds"""
        url = f"{self.base_url}entries.json"
        if since:
            url += f"?since={since}"
        response = requests.get(url, headers=self.headers)
        return response.json()
    
    def get_unread_count(self):
        """Get unread entries count"""
        url = f"{self.base_url}unread_entries.json"
        response = requests.get(url, headers=self.headers)
        return len(response.json())
        