#!/usr/bin/env python3
"""
Handshake Proxy - Multi-website scraper with GoLogin + NodeMaven
Anti-detection proxy server with sticky IP support (24hr sessions)
"""

import json
import os
import sys
import time
import logging
from pathlib import Path
from typing import List, Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from python.gologin_handler import GoLoginHandler
from python.nodemaven_handler import NodeMavenHandler
from python.scraper import WebScraper
from python.anti_detection import AntiDetectionEngine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/handshake_proxy.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class HandshakeProxy:
    """Main proxy orchestrator"""
    
    def __init__(self, config_path: str = 'config.json'):
        """Initialize HandshakeProxy with configuration"""
        self.config_path = config_path
        self.config = self._load_config()
        self.gologin = GoLoginHandler(self.config['gologin'])
        self.nodemaven = NodeMavenHandler(self.config['nodemaven'])
        self.scraper = WebScraper(self.config['scraper'])
        self.anti_detection = AntiDetectionEngine(self.config['anti_detection'])
        self.output_data = []
        
        logger.info("HandshakeProxy initialized successfully")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from JSON file"""
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
            logger.info(f"Configuration loaded from {self.config_path}")
            return config
        except FileNotFoundError:
            logger.error(f"Config file not found: {self.config_path}")
            raise
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON in config file: {self.config_path}")
            raise
    
    def add_target(self, website_url: str, data_selectors: Dict[str, str]):
        """Add a target website to scrape"""
        target = {
            'url': website_url,
            'selectors': data_selectors,
            'timestamp': time.time()
        }
        self.config['scraper']['targets'].append(target)
        logger.info(f"Target added: {website_url}")
    
    def setup_browser(self):
        """Setup GoLogin browser with anti-detection"""
        logger.info("Setting up GoLogin browser...")
        try:
            browser = self.gologin.start_browser()
            logger.info("GoLogin browser started successfully")
            return browser
        except Exception as e:
            logger.error(f"Failed to start GoLogin browser: {e}")
            raise
    
    def get_proxy_ip(self) -> Dict[str, Any]:
        """Get sticky proxy IP from NodeMaven (24hr session)"""
        logger.info("Requesting proxy IP from NodeMaven...")
        try:
            proxy = self.nodemaven.get_sticky_proxy()
            logger.info(f"Proxy IP obtained: {proxy['ip']}")
            return proxy
        except Exception as e:
            logger.error(f"Failed to get proxy IP: {e}")
            raise
    
    def scrape_websites(self, browser):
        """Scrape all configured target websites"""
        targets = self.config['scraper']['targets']
        
        if not targets:
            logger.warning("No target websites configured")
            return
        
        logger.info(f"Starting scrape of {len(targets)} target(s)...")
        
        # Get proxy for all targets (sticky IP for 24hrs)
        proxy = self.get_proxy_ip()
        
        for idx, target in enumerate(targets, 1):
            logger.info(f"Scraping target {idx}/{len(targets)}: {target['url']}")
            
            try:
                # Apply anti-detection measures
                headers = self.anti_detection.generate_headers()
                
                # Scrape website through proxy
                result = self.scraper.scrape(
                    browser=browser,
                    url=target['url'],
                    selectors=target['selectors'],
                    proxy=proxy,
                    headers=headers
                )
                
                # Store result
                result['target_url'] = target['url']
                result['proxy_ip'] = proxy['ip']
                result['timestamp'] = time.time()
                self.output_data.append(result)
                
                logger.info(f"Successfully scraped: {target['url']}")
                
                # Add delay between requests for anti-detection
                delay = self.anti_detection.get_request_delay()
                time.sleep(delay / 1000)
                
            except Exception as e:
                logger.error(f"Failed to scrape {target['url']}: {e}")
                # Continue with next target
                continue
        
        logger.info(f"Scraping completed. Retrieved {len(self.output_data)} results")
    
    def save_results(self):
        """Save scraped data to output file"""
        output_file = self.config['scraper']['output_file']
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        try:
            with open(output_file, 'w') as f:
                json.dump(self.output_data, f, indent=2)
            logger.info(f"Results saved to {output_file}")
        except Exception as e:
            logger.error(f"Failed to save results: {e}")
            raise
    
    def run(self):
        """Execute complete proxy scraping workflow"""
        browser = None
        try:
            logger.info("=" * 50)
            logger.info("HandshakeProxy - Starting workflow")
            logger.info("=" * 50)
            
            # Setup browser and get proxy
            browser = self.setup_browser()
            
            # Scrape all targets
            self.scrape_websites(browser)
            
            # Save results
            self.save_results()
            
            logger.info("=" * 50)
            logger.info("HandshakeProxy - Workflow completed successfully")
            logger.info("=" * 50)
            
        except Exception as e:
            logger.error(f"HandshakeProxy workflow failed: {e}")
            raise
        finally:
            # Cleanup
            if browser:
                self.gologin.close_browser(browser)
                logger.info("Browser closed")


def main():
    """Main entry point"""
    try:
        # Create logs directory
        os.makedirs('logs', exist_ok=True)
        
        # Initialize proxy
        proxy = HandshakeProxy('config.json')
        
        # Example: Add target websites (user should modify this)
        # proxy.add_target('https://example.com', {'title': 'h1', 'price': '.price'})
        # proxy.add_target('https://another-site.com', {'product': '.product-name', 'description': '.description'})
        
        # Run the proxy scraper
        proxy.run()
        
    except KeyboardInterrupt:
        logger.info("HandshakeProxy interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
