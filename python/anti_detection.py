#!/usr/bin/env python3
"""
Anti-Detection Engine - Prevent website identification
Randomizes headers, fingerprints, and request patterns
"""

import logging
import random
import time
from typing import Dict, Any, Tuple

logger = logging.getLogger(__name__)


class AntiDetectionEngine:
    """Anti-detection measures for avoiding website blocking"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Anti-Detection Engine
        
        Args:
            config: Configuration for anti-detection features
        """
        self.config = config
        self.randomize_headers = config.get('randomize_headers', True)
        self.spoof_webrtc = config.get('spoof_webrtc', True)
        self.disable_dns_leaks = config.get('disable_dns_leaks', True)
        self.randomize_request_order = config.get('randomize_request_order', True)
        self.request_delay_min = config.get('request_delay_min', 1000)
        self.request_delay_max = config.get('request_delay_max', 5000)
        
        logger.info("Anti-Detection Engine initialized")
    
    def generate_headers(self) -> Dict[str, str]:
        """Generate randomized HTTP headers to avoid detection"""
        
        user_agent = self._random_user_agent()
        accept_language = self._random_accept_language()
        
        headers = {
            'User-Agent': user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': accept_language,
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': str(random.choice([1, None]) or 1),
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
        }
        
        # Randomly add additional headers
        if random.choice([True, False]):
            headers['Sec-CH-UA'] = f'"Google Chrome";v="{random.randint(100, 120)}", "Not A Brand";v="24"'
            headers['Sec-CH-UA-Mobile'] = '?0'
            headers['Sec-CH-UA-Platform'] = random.choice(['"Windows"', '"macOS"', '"Linux"'])
        
        if random.choice([True, False]):
            headers['Referer'] = self._random_referer()
        
        return headers
    
    def get_request_delay(self) -> int:
        """Get random delay between requests in milliseconds"""
        delay = random.randint(self.request_delay_min, self.request_delay_max)
        logger.debug(f"Request delay: {delay}ms")
        return delay
    
    def _random_user_agent(self) -> str:
        """Generate random user agent"""
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
        ]
        
        return random.choice(user_agents)
    
    def _random_accept_language(self) -> str:
        """Generate random Accept-Language header"""
        languages = [
            'en-US,en;q=0.9',
            'en-US,en;q=0.8,es;q=0.6',
            'en-GB,en;q=0.9',
            'en-US,en;q=0.9,fr;q=0.8',
        ]
        
        return random.choice(languages)
    
    def _random_referer(self) -> str:
        """Generate random referer"""
        referers = [
            'https://www.google.com/',
            'https://www.bing.com/',
            'https://www.yahoo.com/',
            'https://www.duckduckgo.com/',
        ]
        
        return random.choice(referers)
