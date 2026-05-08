"""
Partnership Scanner for Early Deal Detection
Scans multiple data sources for partnership announcements and strategic deals
"""

import re
import asyncio
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple
import aiohttp
import json
import logging

class PartnerTier(Enum):
    TIER_1 = 1  # Major tech (NVDA, AAPL, MSFT, etc.)
    TIER_2 = 2  # Established companies
    TIER_3 = 3  # Mid-cap companies
    TIER_4 = 4  # Small-cap companies
    TIER_5 = 5  # Micro-cap and unknown

@dataclass
class Partnership:
    source: str
    title: str
    description: str
    published_at: datetime
    companies: List[Tuple[str, str]]  # List of (company_name, ticker) tuples
    partner_tier: PartnerTier
    source_credibility: float  # 0-1 scale
    raw_data: dict = None

class PartnershipScanner:
    """Scans for partnership announcements and strategic deals"""
    
    def __init__(self, config: dict):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.session = None
        self.tier1_partners = self._load_tier1_partners()
        
        # Compile regex patterns for partnership detection
        self.partnership_phrases = [
            r'partner(?:ship|ed)?(?: with|ing)?\s+(?:the\s+)?([A-Z][\w\s\.&]+)(?:\s+for|\s+in|\s+on|\s+to|\s+with|\s+regarding|,|$)',
            r'collaborat(?:e|ing|ion)(?:\s+with|\s+between)?\s+([A-Z][\w\s\.&]+)(?:\s+and\s+([A-Z][\w\s\.&]+))?',
            r'joint(?:ly)?\s+(?:venture|partnership|announcement)(?:\s+with|\s+between)?\s+([A-Z][\w\s\.&]+)(?:\s+and\s+([A-Z][\w\s\.&]+))?',
            r'sign(?:ed|s)?\s+(?:a\s+)?(?:partnership|deal|agreement)(?:\s+with|\s+between)?\s+([A-Z][\w\s\.&]+)',
            r'teams?\s+up\s+with\s+([A-Z][\w\s\.&]+)',
            r'exclusive\s+(?:partnership|license|agreement)(?:\s+with|\s+between)?\s+([A-Z][\w\s\.&]+)',
        ]
        self.patterns = [re.compile(p, re.IGNORECASE) for p in self.partnership_phrases]
        
        # Keywords that indicate partnership news
        self.keywords = {
            'partnership', 'collaborat', 'joint venture', 'teaming', 'alliance',
            'strategic agreement', 'distribution deal', 'licensing deal', 'reseller',
            'supply agreement', 'manufacturing deal', 'co-develop', 'co-market',
            'partners with', 'teams up with', 'extends partnership', 'renewed agreement'
        }
    
    async def initialize(self):
        """Initialize async resources with custom SSL context and rate limiting"""
        import ssl
        import certifi
        
        # Rate limiting state
        self.last_request_time = 0
        self.min_request_interval = 2.0  # Minimum seconds between requests
        
        # Create a custom SSL context that uses the system certs
        ssl_context = ssl.create_default_context(cafile=certifi.where())
        
        # Create a TCPConnector with our custom SSL context
        connector = aiohttp.TCPConnector(
            ssl=ssl_context,
            limit=10,  # Limit concurrent connections
            force_close=True,
            enable_cleanup_closed=True
        )
        
        # Create a session with the custom connector and timeouts
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=aiohttp.ClientTimeout(total=30),  # 30 second timeout
            trust_env=True,  # Respect environment proxy settings
            headers={
                'User-Agent': 'PhasmaAIPartnershipScanner/1.0',
                'Accept': 'application/json'
            }
        )
        
    async def _rate_limit(self):
        """Enforce rate limiting between requests"""
        import time
        now = time.time()
        time_since_last = now - self.last_request_time
        
        if time_since_last < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last
            await asyncio.sleep(sleep_time)
            
        self.last_request_time = time.time()
        
    async def _make_request(self, url: str, params: dict = None, method: str = 'GET', 
                          json_data: dict = None, max_retries: int = 3, backoff_factor: float = 1.5) -> dict:
        """
        Make an HTTP request with retry logic and rate limiting
        
        Args:
            url: The URL to request
            params: Query parameters for GET requests
            method: HTTP method (GET, POST, etc.)
            json_data: JSON payload for POST/PUT requests
            max_retries: Maximum number of retry attempts
            backoff_factor: Multiplier for exponential backoff
            
        Returns:
            Parsed JSON response or None if request failed
        """
        import random
        
        for attempt in range(max_retries):
            try:
                await self._rate_limit()
                
                # Log request details for debugging
                self.logger.debug(f"Making {method} request to {url}")
                if params:
                    self.logger.debug(f"Params: {params}")
                if json_data:
                    self.logger.debug(f"JSON Payload: {json_data}")
                
                # Make the request with appropriate parameters
                request_params = {
                    'method': method,
                    'url': url,
                    'ssl': False
                }
                
                if method.upper() in ['GET', 'DELETE']:
                    request_params['params'] = params
                else:
                    if json_data:
                        request_params['json'] = json_data
                    else:
                        request_params['data'] = params
                
                async with self.session.request(**request_params) as response:
                    # Handle rate limiting (429)
                    if response.status == 429:
                        retry_after = float(response.headers.get('Retry-After', 5))
                        wait_time = retry_after * (1 + random.random() * 0.1)  # Add jitter
                        self.logger.warning(f"Rate limited. Waiting {wait_time:.2f} seconds...")
                        await asyncio.sleep(wait_time)
                        continue
                    
                    # Log response status
                    self.logger.debug(f"Response status: {response.status}")
                    
                    # Handle successful response
                    if response.status == 200:
                        try:
                            return await response.json()
                        except Exception as e:
                            self.logger.error(f"Failed to parse JSON response: {e}")
                            text = await response.text()
                            self.logger.debug(f"Response text: {text[:500]}...")
                            return None
                    
                    # Handle server errors with retry
                    if response.status >= 500:
                        text = await response.text()
                        self.logger.warning(f"Server error {response.status}: {text[:200]}")
                        if attempt < max_retries - 1:  # Don't sleep on last attempt
                            continue
                    
                    # Handle client errors (don't retry)
                    if 400 <= response.status < 500:
                        text = await response.text()
                        self.logger.warning(f"Client error {response.status}: {text[:200]}")
                        return None
                    
                    # For other status codes, log and continue
                    self.logger.warning(f"Unexpected status {response.status}")
                    return None
                
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                self.logger.error(f"Request error (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt == max_retries - 1:  # Last attempt
                    raise
                
                # Exponential backoff with jitter
                sleep_time = (backoff_factor ** attempt) * (0.5 + random.random() * 0.5)
                await asyncio.sleep(sleep_time)
            
            except Exception as e:
                self.logger.error(f"Unexpected error in _make_request: {e}", exc_info=True)
                if attempt == max_retries - 1:  # Last attempt
                    raise
                
                # Exponential backoff with jitter
                sleep_time = (backoff_factor ** attempt) * (0.5 + random.random() * 0.5)
                await asyncio.sleep(sleep_time)
        
        return None
    
    async def close(self):
        """Clean up resources"""
        if self.session:
            await self.session.close()
    
    def _load_tier1_partners(self) -> Set[str]:
        """Load list of tier 1 partners"""
        return {
            'nvidia', 'microsoft', 'apple', 'amazon', 'google', 'alphabet', 'meta',
            'intel', 'amd', 'qualcomm', 'samsung', 'tsmc', 'oracle', 'ibm', 'salesforce',
            'adobe', 'cisco', 'netflix', 'tesla', 'nvidia corporation', 'microsoft corporation',
            'apple inc', 'amazon.com', 'alphabet inc', 'meta platforms', 'intel corporation',
            'advanced micro devices', 'qualcomm incorporated', 'samsung electronics',
            'taiwan semiconductor', 'oracle corporation', 'international business machines',
            'salesforce.com', 'adobe inc', 'cisco systems', 'netflix inc', 'tesla inc'
        }
    
    def _extract_companies(self, text: str) -> List[Tuple[str, str]]:
        """Extract company names from text"""
        # Simple implementation - would be enhanced with NER in production
        companies = []
        for pattern in self.patterns:
            matches = pattern.findall(text)
            for match in matches:
                if isinstance(match, tuple):
                    companies.extend([m.strip() for m in match if m.strip()])
                elif match.strip():
                    companies.append(match.strip())
        
        # Deduplicate and clean
        seen = set()
        unique_companies = []
        for company in companies:
            # Clean up company name
            clean_name = re.sub(r'[^\w\s]', '', company.lower()).strip()
            if clean_name and clean_name not in seen:
                seen.add(clean_name)
                # Map to ticker (simplified - would use a ticker mapping service in production)
                ticker = clean_name.upper()  # Placeholder
                unique_companies.append((company, ticker))
        
        return unique_companies
    
    def _determine_partner_tier(self, companies: List[Tuple[str, str]]) -> PartnerTier:
        """Determine the highest partner tier in the list of companies"""
        for name, _ in companies:
            clean_name = name.lower()
            if any(tier1 in clean_name for tier1 in self.tier1_partners):
                return PartnerTier.TIER_1
        
        # In a real implementation, we would check market cap data here
        # For now, we'll just return a default tier
        return PartnerTier.TIER_3
    
    def _calculate_credibility(self, source: str) -> float:
        """Calculate source credibility score (0-1)"""
        # Simple implementation - would be enhanced with known source ratings
        source = source.lower()
        if any(s in source for s in ['prnewswire', 'businesswire', 'globenewswire']):
            return 0.9  # Official press releases
        elif any(s in source for s in ['reuters', 'bloomberg', 'wsj', 'marketwatch']):
            return 0.85  # Major financial news
        elif any(s in source for s in ['seekingalpha', 'benzinga']):
            return 0.7   # Financial news aggregators
        return 0.5  # Default credibility
    
    def _is_partnership_news(self, title: str, description: str) -> bool:
        """Check if the content is likely about a partnership"""
        content = f"{title} {description}".lower()
        return any(keyword in content for keyword in self.keywords)
    
    async def scan_news_article(self, source: str, title: str, description: str, 
                              published_at: str, raw_data: dict = None) -> Optional[Partnership]:
        """
        Scan a news article for partnership announcements
        
        Args:
            source: News source (e.g., 'PR Newswire', 'Seeking Alpha')
            title: Article title
            description: Article description or content
            published_at: Publication timestamp (ISO format)
            raw_data: Raw article data for reference
            
        Returns:
            Partnership object if a partnership is detected, else None
        """
        try:
            # Skip if not partnership-related
            if not self._is_partnership_news(title, description):
                return None
            
            # Extract mentioned companies
            companies = self._extract_companies(f"{title} {description}")
            if len(companies) < 1:
                return None
            
            # Determine partner tier and credibility
            partner_tier = self._determine_partner_tier(companies)
            credibility = self._calculate_credibility(source)
            
            # Parse publication time
            try:
                published_time = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
            except (ValueError, TypeError):
                published_time = datetime.utcnow()
            
            return Partnership(
                source=source,
                title=title,
                description=description,
                published_at=published_time,
                companies=companies,
                partner_tier=partner_tier,
                source_credibility=credibility,
                raw_data=raw_data
            )
            
        except Exception as e:
            self.logger.error(f"Error scanning article: {e}", exc_info=True)
            return None
    
    async def scan_sec_filings(self, symbol: str) -> List[Partnership]:
        """Scan SEC filings for partnership announcements"""
        # TODO: Implement SEC EDGAR API integration
        return []
    
    async def scan_government_contracts(self, symbol: str) -> List[Partnership]:
        """
        Scan government contract databases for relevant awards
        
        Args:
            symbol: Stock ticker symbol to search for
            
        Returns:
            List of Partnership objects found in government contracts
        """
        if not self.session:
            self.logger.warning("Session not initialized. Call initialize() first.")
            return []
            
        # Get company name from symbol (simplified - would map to company name in production)
        company_name = symbol.upper()
        partnerships = []
        
        # Process SAM.gov API if enabled
        sam_config = self.config.get('api_keys', {}).get('sam_gov', {})
        if sam_config.get('enabled', False):
            await self._process_sam_gov_contracts(company_name, symbol, partnerships)
        
        # Process USAspending API if enabled
        usaspending_config = self.config.get('api_keys', {}).get('usaspending', {})
        if usaspending_config.get('enabled', False):
            await self._process_usaspending_contracts(company_name, symbol, partnerships)
            
        return partnerships
        
    async def _process_sam_gov_contracts(self, company_name: str, symbol: str, partnerships: List[Partnership]) -> None:
        """Process contracts from SAM.gov API"""
        try:
            sam_config = self.config['api_keys']['sam_gov']
            base_url = sam_config.get('base_url', 'https://api.sam.gov')
            api_key = sam_config.get('api_key')
            
            if not api_key:
                self.logger.warning("SAM.gov API key not found in config")
                return
                
            # Search for contracts with the company
            url = f"{base_url}/opportunities/v2/search"
            params = {
                'api_key': api_key,
                'limit': 5,
                'q': company_name,
                'postedFrom': (datetime.utcnow() - timedelta(days=30)).strftime('%m/%d/%Y'),
                'postedTo': datetime.utcnow().strftime('%m/%d/%Y'),
                'status': 'active'
            }
            
            try:
                async with self.session.get(url, params=params, ssl=False) as response:
                    if response.status == 200:
                        try:
                            data = await response.json()
                            
                            # Process each contract found
                            for opp in data.get('opportunitiesData', [])[:5]:
                                try:
                                    # Extract opportunity details
                                    title = opp.get('title', 'Government Contract')
                                    description = opp.get('description', 'No description available')
                                    award_amount = float(opp.get('awardCeiling', '0').replace('$', '').replace(',', '') or '0')
                                    publish_date = opp.get('publishDate')
                                    
                                    # Only include significant opportunities
                                    if award_amount < 1000000:  # $1M threshold
                                        continue
                                        
                                    # Create a partnership object
                                    partnership = Partnership(
                                        source="SAM.gov",
                                        title=f"Government Opportunity: {title}",
                                        description=f"Potential ${award_amount:,.0f} opportunity. {description[:200]}...",
                                        published_at=datetime.strptime(publish_date, '%m/%d/%Y') if publish_date else datetime.utcnow(),
                                        companies=[(company_name, symbol)],
                                        partner_tier=PartnerTier.TIER_1,
                                        source_credibility=0.95,
                                        raw_data=opp
                                    )
                                    
                                    partnerships.append(partnership)
                                    
                                except Exception as e:
                                    self.logger.error(f"Error processing SAM.gov opportunity: {e}", exc_info=True)
                                    continue
                                    
                        except Exception as e:
                            self.logger.error(f"Error parsing SAM.gov response: {e}")
                    else:
                        self.logger.warning(f"SAM.gov API returned status {response.status}")
                        
            except aiohttp.ClientError as e:
                self.logger.error(f"Network error querying SAM.gov: {e}")
            except Exception as e:
                self.logger.error(f"Unexpected error querying SAM.gov: {e}", exc_info=True)
                
        except Exception as e:
            self.logger.error(f"Error in _process_sam_gov_contracts: {e}", exc_info=True)
    
    async def _process_usaspending_contracts(self, company_name: str, symbol: str, partnerships: List[Partnership]) -> None:
        """Process contracts from USAspending API"""
        try:
            base_url = self.config['api_keys']['usaspending'].get('base_url', 'https://api.usaspending.gov')
            
            # Calculate date range (last 30 days)
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=30)
            
            # Prepare the request payload for the spending_by_award endpoint
            payload = {
                'filters': {
                    'recipient_search_text': [company_name],
                    'time_period': [{
                        'start_date': start_date.strftime('%Y-%m-%d'),
                        'end_date': end_date.strftime('%Y-%m-%d')
                    }],
                    'award_type_codes': [
                        'A', 'B', 'C', 'D',  # Contracts
                        '02', '03', '04', '05', '06', '10'  # Grants, loans, etc.
                    ],
                    'award_amounts': [
                        {'lower_bound': 1000000}  # Only awards over $1M
                    ]
                },
                'fields': [
                    'Award ID',
                    'Recipient Name',
                    'Awarding Agency',
                    'Awarding Sub Agency',
                    'Award Amount',
                    'Start Date',
                    'End Date',
                    'Award Type',
                    'Description',
                    'Period of Performance Start Date',
                    'Period of Performance Current End Date',
                    'Awarding Office Name',
                    'Funding Agency',
                    'Funding Sub Agency'
                ],
                'limit': 5,
                'page': 1,
                'order': 'desc',
                'sort': 'Award Amount'
            }
            
            # Get the awards data
            awards_url = f"{base_url}/api/v2/search/spending_by_award/"
            awards_data = await self._make_request(
                awards_url,
                method='POST',
                json_data=payload,
                max_retries=3
            )
            
            if not awards_data or 'results' not in awards_data:
                self.logger.debug(f"No awards found for: {company_name}")
                return
            
            # Process each award
            for award in awards_data.get('results', [])[:5]:
                try:
                    # Extract award details
                    contract_id = award.get('Award ID')
                    awarding_agency = award.get('Awarding Agency', 'Unknown Agency')
                    contract_title = f"{awarding_agency} - {award.get('Award Type', 'Contract')}"
                    contract_desc = award.get('Description', 'No description available')
                    award_amount = float(award.get('Award Amount', 0) or 0)
                    award_date = award.get('Start Date') or award.get('Period of Performance Start Date')
                    
                    # Only include significant contracts
                    if award_amount < 1000000:  # $1M threshold
                        continue
                        
                    # Create a partnership object
                    partnership = Partnership(
                        source="USAspending",
                        title=f"Government Contract: {contract_title}",
                        description=f"${award_amount:,.0f} contract. {contract_desc[:200]}...",
                        published_at=datetime.strptime(award_date, '%Y-%m-%d') if award_date else datetime.utcnow(),
                        companies=[(company_name, symbol)],
                        partner_tier=PartnerTier.TIER_2,
                        source_credibility=0.9,
                        raw_data=award
                    )
                    
                    partnerships.append(partnership)
                    
                except Exception as e:
                    self.logger.error(f"Error processing USAspending contract: {e}", exc_info=True)
                    continue
                    
        except aiohttp.ClientError as e:
            self.logger.error(f"Network error querying USAspending: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error in _process_usaspending_contracts: {e}", exc_info=True)
    
    def score_opportunity(self, partnership: Partnership) -> float:
        """Score a partnership opportunity (0-10 scale)"""
        if not partnership:
            return 0.0
        
        # Base score from partner tier (higher tier = higher score)
        tier_score = (6 - partnership.partner_tier.value) * 1.5  # 1.5-7.5 points
        
        # Boost for recent news (decay over 7 days)
        days_old = (datetime.utcnow() - partnership.published_at).total_seconds() / 86400
        recency_score = max(0, 1 - (days_old / 7)) * 2.0  # 0-2 points
        
        # Source credibility
        credibility_score = partnership.source_credibility * 1.5  # 0-1.5 points
        
        # Total score (0-10)
        total_score = min(10.0, tier_score + recency_score + credibility_score)
        
        return round(total_score, 1)
    
    def generate_alert(self, partnership: Partnership, score: float) -> dict:
        """Generate an alert for a high-scoring partnership"""
        if not partnership or score < 7.0:  # Only alert on high-confidence opportunities
            return None
            
        # Format company list
        company_list = ", ".join([f"{name} ({ticker})" for name, ticker in partnership.companies])
        
        return {
            'type': 'partnership_alert',
            'symbol': partnership.companies[0][1] if partnership.companies else 'N/A',
            'title': partnership.title,
            'companies': company_list,
            'partner_tier': partnership.partner_tier.name,
            'score': score,
            'source': partnership.source,
            'published_at': partnership.published_at.isoformat(),
            'alert_time': datetime.utcnow().isoformat(),
            'details': {
                'description': partnership.description[:500] + ('...' if len(partnership.description) > 500 else ''),
                'source_credibility': partnership.source_credibility,
                'raw_data': partnership.raw_data if self.config.get('include_raw_data', False) else None
            }
        }
