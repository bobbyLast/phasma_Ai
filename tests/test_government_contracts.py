"""
Test script for government contract scanning functionality
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to path
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from engines.long_tier.partnership_scanner import PartnershipScanner
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('test_government_contracts.log')
    ]
)
logger = logging.getLogger(__name__)

# Test configuration
TEST_CONFIG = {
    "api_keys": {
        "sam_gov": {
            "api_key": os.getenv("SAM_GOV_API_KEY", "SAM-89369821-caa4-4e0f-a427-b2b842d57177"),
            "base_url": "https://api.sam.gov",
            "enabled": True
        },
        "usaspending": {
            "base_url": "https://api.usaspending.gov",
            "enabled": True
        }
    },
    "monitored_tickers": ["LMT", "BA", "RTX", "GD", "NOC"]  # Defense contractors with government contracts
}

async def log_response(response, url, params):
    """Log detailed response information"""
    logger.info(f"\n--- Request Details ---")
    logger.info(f"URL: {url}")
    logger.info(f"Params: {params}")
    logger.info(f"Status: {response.status}")
    
    try:
        text = await response.text()
        logger.info(f"Response (first 500 chars): {text[:500]}")
        return text
    except Exception as e:
        logger.error(f"Error reading response text: {e}")
        return None

async def test_sam_gov_direct(scanner):
    """Test direct SAM.gov API calls"""
    sam_config = TEST_CONFIG["api_keys"]["sam_gov"]
    base_url = sam_config["base_url"]
    api_key = sam_config["api_key"]
    
    # Test with a known government contractor
    company_name = "LOCKHEED MARTIN"
    url = f"{base_url}/opportunities/v2/search"
    params = {
        'api_key': api_key,
        'limit': 5,
        'q': company_name,
        'postedFrom': (datetime.utcnow() - timedelta(days=30)).strftime('%m/%d/%Y'),
        'postedTo': datetime.utcnow().strftime('%m/%d/%Y'),
        'status': 'active'
    }
    
    logger.info("\n--- Testing SAM.gov API Directly ---")
    try:
        async with scanner.session.get(url, params=params, ssl=False) as response:
            response_text = await log_response(response, url, params)
            
            if response.status == 200:
                try:
                    data = await response.json()
                    logger.info(f"Found {len(data.get('opportunitiesData', []))} opportunities")
                    for opp in data.get('opportunitiesData', [])[:2]:
                        logger.info(f"- {opp.get('title', 'No title')} (${opp.get('awardCeiling', 'N/A')})")
                except Exception as e:
                    logger.error(f"Error parsing JSON: {e}")
                    
    except Exception as e:
        logger.error(f"Error in SAM.gov direct test: {e}", exc_info=True)

async def test_usaspending_direct(scanner):
    """Test direct USAspending API calls"""
    base_url = TEST_CONFIG["api_keys"]["usaspending"]["base_url"]
    
    # Test with a known government contractor
    company_name = "LOCKHEED MARTIN"
    
    # Try awards endpoint
    url = f"{base_url}/api/v2/search/awards/"
    params = {
        'filters': json.dumps({
            'recipient_name': company_name,
            'time_period': [{
                'start_date': (datetime.utcnow() - timedelta(days=30)).strftime('%Y-%m-%d'),
                'end_date': datetime.utcnow().strftime('%Y-%m-%d')
            }]
        }),
        'limit': 5
    }
    
    logger.info("\n--- Testing USAspending API Directly (Awards) ---")
    try:
        async with scanner.session.get(url, params=params, ssl=False) as response:
            response_text = await log_response(response, url, params)
            
            if response.status == 200:
                try:
                    data = await response.json()
                    logger.info(f"Found {len(data.get('results', []))} awards")
                    for award in data.get('results', [])[:2]:
                        logger.info(f"- {award.get('awarding_agency', 'N/A')}: ${award.get('award_amount', 'N/A')}")
                except Exception as e:
                    logger.error(f"Error parsing JSON: {e}")
                    
    except Exception as e:
        logger.error(f"Error in USAspending awards test: {e}", exc_info=True)

async def test_scan_government_contracts():
    """Test the government contract scanning functionality"""
    logger.info("Starting government contracts test...")
    
    # Initialize the scanner
    scanner = PartnershipScanner(TEST_CONFIG)
    await scanner.initialize()
    
    try:
        # Test direct API calls first
        await test_sam_gov_direct(scanner)
        await test_usaspending_direct(scanner)
        
        # Test with defense contractors known to have government contracts
        for symbol in TEST_CONFIG["monitored_tickers"]:
            logger.info(f"\n--- Testing {symbol} with PartnershipScanner ---")
            
            try:
                contracts = await scanner.scan_government_contracts(symbol)
                
                if contracts:
                    logger.info(f"Found {len(contracts)} government contracts/opportunities for {symbol}")
                    for i, contract in enumerate(contracts[:2], 1):  # Limit to first 2 for brevity
                        logger.info(f"\nContract {i}:")
                        logger.info(f"Source: {contract.source}")
                        logger.info(f"Title: {contract.title}")
                        logger.info(f"Description: {contract.description[:200]}...")
                        logger.info(f"Published: {contract.published_at}")
                else:
                    logger.info(f"No government contracts found for {symbol}")
                    
            except Exception as e:
                logger.error(f"Error scanning {symbol}: {e}", exc_info=True)
                
    except Exception as e:
        logger.error(f"Error during test: {e}", exc_info=True)
    finally:
        # Clean up
        await scanner.close()
        logger.info("Test completed.")

if __name__ == "__main__":
    asyncio.run(test_scan_government_contracts())
