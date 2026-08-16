#!/usr/bin/env python3
"""
NodeMaven Handler - Sticky IP proxy management
Handles proxy IP allocation with 24hr sticky sessions
"""

import logging
import time
from typing import Dict, Any, Optional
import requests

logger = logging.getLogger(__name__)


class NodeMavenHandler:
    """Manage NodeMaven proxy IP allocation"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize NodeMaven handler
        
        Args:
            config: NodeMaven configuration with api_key, countries, ip_type
        """
        self.config = config
        self.api_key = config.get('api_key')
        self.sticky_duration = config.get('sticky_duration', 86400)  # 24 hours
        self.countries = config.get('countries', ['US'])
        self.ip_type = config.get('ip_type', 'residential')
        self.base_url = "https://api.nodemaven.com/api/v1"
        self.current_proxy = None
        self.proxy_session_id = None
        
        if not self.api_key:
            logger.warning("NodeMaven API key not configured")
    
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict:
        """Make API request to NodeMaven"""
        try:
            url = f"{self.base_url}{endpoint}"
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            if method.upper() == 'GET':
                response = requests.get(url, headers=headers, timeout=10)
            elif method.upper() == 'POST':
                response = requests.post(url, headers=headers, json=data, timeout=10)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"NodeMaven API request failed: {e}")
            raise
    
    def get_sticky_proxy(self, country: Optional[str] = None, duration: Optional[int] = None) -> Dict[str, Any]:
        """
        Get sticky proxy IP that lasts for 24 hours
        
        Args:
            country: Country code (US, UK, DE, etc.)
            duration: Session duration in seconds (default: 24hr)
        
        Returns:
            Proxy details with IP, port, username, password
        """
        try:
            country = country or self.countries[0]
            duration = duration or self.sticky_duration
            
            logger.info(f"Requesting sticky proxy: {country} (duration: {duration}s)")
            
            # Request sticky session proxy
            data = {
                'type': self.ip_type,
                'country': country,
                'sticky': True,
                'sticky_duration': duration,
                'format': 'json'
            }
            
            response = self._make_request('POST', '/proxies/sticky', data)
            
            proxy = {
                'ip': response.get('ip'),
                'port': response.get('port'),
                'username': response.get('username'),
                'password': response.get('password'),
                'protocol': 'http',
                'country': country,
                'type': self.ip_type,
                'session_id': response.get('session_id'),
                'expires_at': time.time() + duration,
                'created_at': time.time()
            }
            
            self.current_proxy = proxy
            self.proxy_session_id = proxy.get('session_id')
            
            logger.info(f"Sticky proxy obtained: {proxy['ip']}:{proxy['port']} (expires in {duration}s)")
            return proxy
            
        except Exception as e:
            logger.error(f"Failed to get sticky proxy: {e}")
            raise
    
    def format_proxy_url(self, proxy: Dict[str, Any]) -> str:
        """Format proxy as URL string"""
        username = proxy.get('username')
        password = proxy.get('password')
        ip = proxy.get('ip')
        port = proxy.get('port')
        
        if username and password:
            return f"{proxy.get('protocol', 'http')}://{username}:{password}@{ip}:{port}"
        else:
            return f"{proxy.get('protocol', 'http')}://{ip}:{port}"
    
    def format_proxy_dict(self, proxy: Dict[str, Any]) -> Dict[str, str]:
        """Format proxy as dictionary for requests library"""
        proxy_url = self.format_proxy_url(proxy)
        return {
            'http': proxy_url,
            'https': proxy_url
        }
