import httpx
import asyncio
from config import config
import logging
from typing import Dict, Any

class URLScanner:
    def __init__(self):
        """Initialize URL scanner with urlscan.io API"""
        self.api_key = config.URLSCAN_API_KEY
        self.base_url = "https://urlscan.io/api/v1"
        self.logger = logging.getLogger(__name__)

    async def scan_url(self, url: str) -> Dict[str, Any]:
        """Scan URL using urlscan.io API"""
        try:
            async with httpx.AsyncClient() as client:
                # Submit URL for scanning
                headers = {
                    'API-Key': self.api_key,
                    'Content-Type': 'application/json'
                }
                
                data = {
                    'url': url,
                    'visibility': 'private'
                }
                
                # Submit scan
                response = await client.post(
                    f"{self.base_url}/scan/",
                    json=data,
                    headers=headers
                )
                
                if response.status_code == 200:
                    scan_result = response.json()
                    scan_uuid = scan_result['uuid']
                    
                    # Wait for scan to complete
                    await asyncio.sleep(10)  # Wait for scan processing
                    
                    # Get scan results
                    result_response = await client.get(
                        f"{self.base_url}/result/{scan_uuid}/",
                        headers={'API-Key': self.api_key}
                    )
                    
                    if result_response.status_code == 200:
                        result_data = result_response.json()
                        return self._analyze_scan_result(result_data)
                    else:
                        return {
                            'is_safe': True,
                            'risk_level': 'unknown',
                            'message': 'Scan results not available yet'
                        }
                else:
                    return {
                        'is_safe': True,
                        'risk_level': 'unknown',
                        'message': 'Failed to submit URL for scanning'
                    }
                    
        except Exception as e:
            self.logger.error(f"URL scan error: {e}")
            return {
                'is_safe': True,
                'risk_level': 'unknown',
                'message': 'Scanner temporarily unavailable'
            }

    def _analyze_scan_result(self, result_data: dict) -> Dict[str, Any]:
        """Analyze scan results and determine risk level"""
        try:
            verdicts = result_data.get('verdicts', {})
            overall = verdicts.get('overall', {})
            
            # Check various risk indicators
            malicious_score = overall.get('score', 0)
            categories = overall.get('categories', [])
            
            # Determine risk level
            if malicious_score >= 80:
                risk_level = 'high'
                is_safe = False
                message = "⚠️ High risk URL detected! This link may be dangerous."
            elif malicious_score >= 40:
                risk_level = 'medium'
                is_safe = False
                message = "⚠️ Medium risk URL. Exercise caution."
            elif malicious_score >= 20:
                risk_level = 'low'
                is_safe = True
                message = "⚠️ Low risk detected. Proceed with caution."
            else:
                risk_level = 'safe'
                is_safe = True
                message = "✅ URL appears to be safe."
            
            return {
                'is_safe': is_safe,
                'risk_level': risk_level,
                'score': malicious_score,
                'categories': categories,
                'message': message,
                'scan_url': f"https://urlscan.io/result/{result_data.get('task', {}).get('uuid', '')}"
            }
            
        except Exception as e:
            self.logger.error(f"Result analysis error: {e}")
            return {
                'is_safe': True,
                'risk_level': 'unknown',
                'message': 'Could not analyze scan results'
            }

    def extract_urls_from_text(self, text: str) -> list:
        """Extract URLs from text message"""
        import re
        url_pattern = r'https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:[\w.])*)?)?'
        return re.findall(url_pattern, text, re.IGNORECASE)