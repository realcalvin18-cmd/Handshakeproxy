#!/usr/bin/env python3
"""
Web Scraper - Extract data from websites through proxy
Uses BeautifulSoup and requests with anti-detection measures
"""

import logging
import time
from typing import Dict, Any, Optional, List
import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


class WebScraper:
    """Web scraper with proxy support and anti-detection"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Web Scraper
        
        Args:
            config: Scraper configuration with timeout, retry_attempts, etc.
        """
        self.config = config
        self.timeout = config.get('timeout', 30)
        self.retry_attempts = config.get('retry_attempts', 3)
        self.output_file = config.get('output_file', 'output/data.json')
        self.session = self._create_session()
    
    def _create_session(self) -> requests.Session:
        """Create requests session with retry strategy"""
        session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=self.retry_attempts,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=['GET', 'POST']
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        
        return session
    
    def scrape(self, browser: Any, url: str, selectors: Dict[str, str], 
               proxy: Optional[Dict[str, Any]] = None, 
               headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Scrape website and extract data
        
        Args:
            browser: GoLogin browser instance
            url: Target URL to scrape
            selectors: CSS selectors for data extraction {field: selector}
            proxy: Proxy configuration
            headers: Custom headers for request
        
        Returns:
            Dictionary with extracted data
        """
        try:
            logger.info(f"Scraping: {url}")
            
            # Prepare headers
            if headers is None:
                headers = self._default_headers()
            
            # Prepare proxy
            proxy_dict = None
            if proxy:
                proxy_dict = self._format_proxy(proxy)
            
            # Make request
            response = self.session.get(
                url,
                headers=headers,
                proxies=proxy_dict,
                timeout=self.timeout,
                verify=False  # For testing; enable verification in production
            )
            
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract data using selectors
            extracted_data = self._extract_data(soup, selectors)
            
            result = {
                'status': 'success',
                'url': url,
                'status_code': response.status_code,
                'data': extracted_data,
                'headers_sent': dict(headers),
                'timestamp': time.time()
            }
            
            logger.info(f"Successfully scraped {url}: {len(extracted_data)} fields extracted")
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to scrape {url}: {e}")
            return {
                'status': 'error',
                'url': url,
                'error': str(e),
                'timestamp': time.time()
            }
        except Exception as e:
            logger.error(f"Unexpected error scraping {url}: {e}")
            return {
                'status': 'error',
                'url': url,
                'error': str(e),
                'timestamp': time.time()
            }
    
    def _extract_data(self, soup: BeautifulSoup, selectors: Dict[str, str]) -> Dict[str, Any]:
        """Extract data from parsed HTML using CSS selectors"""
        extracted = {}
        
        for field, selector in selectors.items():
            try:
                elements = soup.select(selector)
                
                if not elements:
                    extracted[field] = None
                elif len(elements) == 1:
                    extracted[field] = elements[0].get_text(strip=True)
                else:
                    extracted[field] = [elem.get_text(strip=True) for elem in elements]
                
                logger.debug(f"Extracted '{field}': {type(extracted[field])}")
                
            except Exception as e:
                logger.error(f"Failed to extract field '{field}' with selector '{selector}': {e}")
                extracted[field] = None
        
        return extracted
    
    def _format_proxy(self, proxy: Dict[str, Any]) -> Dict[str, str]:
        """Format proxy for requests library"""
        username = proxy.get('username')
        password = proxy.get('password')
        ip = proxy.get('ip')
        port = proxy.get('port')
        protocol = proxy.get('protocol', 'http')
        
        if username and password:
            proxy_url = f"{protocol}://{username}:{password}@{ip}:{port}"
        else:
            proxy_url = f"{protocol}://{ip}:{port}"
        
        return {
            'http': proxy_url,
            'https': proxy_url
        }
    
    def _default_headers(self) -> Dict[str, str]:
        """Get default HTTP headers"""
        return {
            'User-Agent': self.config.get('user_agent', 
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
    
    def scrape_multiple(self, browser: Any, urls: List[str], 
                       selectors: Dict[str, str],
                       proxy: Optional[Dict[str, Any]] = None,
                       headers: Optional[Dict[str, str]] = None) -> List[Dict[str, Any]]:
        """Scrape multiple URLs"""
        results = []
        
        for url in urls:
            try:
                result = self.scrape(browser, url, selectors, proxy, headers)
                results.append(result)
                
                # Delay between requests
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Error scraping {url}: {e}")
                results.append({
                    'status': 'error',
                    'url': url,
                    'error': str(e)
                })
        
        return results
    
    def validate_selectors(self, url: str, selectors: Dict[str, str], 
                          proxy: Optional[Dict[str, Any]] = None) -> Dict[str, bool]:
        """Validate that selectors work on target website"""
        try:
            response = self.session.get(
                url,
                timeout=self.timeout,
                proxies=self._format_proxy(proxy) if proxy else None
            )
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            validation = {}
            
            for field, selector in selectors.items():
                elements = soup.select(selector)
                validation[field] = len(elements) > 0
                logger.info(f"Selector '{selector}' for '{field}': {'✓' if validation[field] else '✗'}")
            
            return validation
            
        except Exception as e:
            logger.error(f"Failed to validate selectors: {e}")
            return {field: False for field in selectors.keys()}
