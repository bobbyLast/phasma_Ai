"""
Sports Odds API Integration for Phasma AI
Integrates The Odds API for sports betting predictions
"""

import requests
import json
from typing import Dict, List, Optional
from datetime import datetime

class SportsOddsAPI:
    """Integration with The Odds API for sports betting markets"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.base_url = "https://the-odds-api.com/sports-odds-data/bookmaker-apis.html"
        self.session = requests.Session()
        
    def get_daily_fantasy_dfs_sites(self) -> Dict:
        """Get daily fantasy DFS sites data"""
        try:
            # Mock implementation - replace with actual API call
            return {
                "draftkings": "Available",
                "fanduel": "Available", 
                "draftkings_nba": "Active",
                "fanduel_nba": "Active"
            }
        except Exception as e:
            print(f"❌ Sports Odds API Error: {e}")
            return {}
    
    def get_sports_odds(self, sport: str = "NFL") -> Dict:
        """Get current odds for specified sport"""
        try:
            # Mock implementation - replace with actual API call
            return {
                "sport": sport,
                "games_today": 8,
                "featured_games": [
                    {
                        "teams": "Lakers vs Warriors",
                        "odds": {"lakers": -110, "warriors": +110},
                        "over_under": {"total": 220.5, "over": -110, "under": -110}
                    }
                ]
            }
        except Exception as e:
            print(f"❌ Sports Odds API Error: {e}")
            return {}
    
    def analyze_betting_opportunities(self, sport: str = "NFL") -> List[Dict]:
        """Analyze betting opportunities using odds data"""
        odds_data = self.get_sports_odds(sport)
        opportunities = []

        if not odds_data.get("featured_games"):
            return opportunities

        for game in odds_data["featured_games"]:
            # Look for value bets
            teams = game["teams"].split(" vs ")
            odds = game["odds"]

            # Simple value detection (mock logic)
            try:
                # Extract team names and odds more carefully
                team1_name = teams[0].split()[0]  # Get first word of team name
                team2_name = teams[1].split()[0]  # Get first word of team name
                
                team1_odds = odds.get(team1_name.lower(), 0)
                team2_odds = odds.get(team2_name.lower(), 0)
                
                if team1_odds and team2_odds and abs(int(team1_odds) - int(team2_odds)) > 20:
                    opportunities.append({
                        "type": "value_bet",
                        "game": game["teams"],
                        "recommendation": "Consider betting on underdog",
                        "confidence": 65,
                        "reasoning": f"Value detected in {team1_name} vs {team2_name}"
                    })
            except Exception as e:
                print(f"⚠️ Error parsing odds for {game['teams']}: {e}")
                continue

        return opportunities

# Integration function for main.py
def integrate_sports_odds_api(config: Dict) -> SportsOddsAPI:
    """Initialize sports odds API integration"""
    api = SportsOddsAPI(config)
    print("🏈 Sports Odds API Initialized - Betting Intelligence Enabled")
    return api

if __name__ == "__main__":
    # Test the integration
    test_config = {"api_key": "test_key"}
    api = integrate_sports_odds_api(test_config)
    
    # Test getting odds
    nba_odds = api.get_sports_odds("NBA")
    print(f"NBA Odds: {json.dumps(nba_odds, indent=2)}")
    
    # Test DFS sites
    dfs_sites = api.get_daily_fantasy_dfs_sites()
    print(f"DFS Sites: {json.dumps(dfs_sites, indent=2)}")
    
    # Test betting opportunities
    opportunities = api.analyze_betting_opportunities("NFL")
    print(f"Betting Opportunities: {json.dumps(opportunities, indent=2)}")
