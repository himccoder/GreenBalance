#!/usr/bin/env python3
"""
Green CDN Carbon Controller for Test Environment

This script fetches real-time carbon intensity data from WattTime API
and dynamically adjusts HAProxy server weights to favor servers in regions
with lower carbon intensity (greener energy).

Adapted for Test environment with dockerized services.
"""

import os
import time
import requests
import logging
from typing import Dict, List, Optional
from datetime import datetime
import math
import random

from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class WattTimeAPI:
    """Handles all interactions with the WattTime API"""
    
    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password
        self.token = None
        self.base_url = "https://api.watttime.org"
    
    def login(self) -> bool:
        """Authenticate with WattTime API and get access token"""
        try:
            login_url = f"{self.base_url}/login"
            response = requests.get(
                login_url, 
                auth=HTTPBasicAuth(self.username, self.password),
                timeout=10
            )
            response.raise_for_status()
            
            self.token = response.json().get('token')
            if self.token:
                logger.info("Successfully authenticated with WattTime API")
                return True
            else:
                logger.error("No token received from WattTime API")
                return False
                
        except Exception as e:
            logger.error(f"Failed to authenticate with WattTime API: {e}")
            return False
    
    def get_carbon_intensity(self, region: str, base_intensity: Optional[float] = None) -> Optional[float]:
        """Get carbon intensity for a region"""
        if not self.token:
            if not self.login():
                return None
        
        try:
            # For CAISO_NORTH, use real WattTime data
            if region == "CAISO_NORTH":
                return self._get_real_intensity(region)
            else:
                # For other regions, use simulated data
                if base_intensity is None:
                    base_intensity = 600.0  # Default baseline
                return self._get_simulated_intensity(base_intensity)
                
        except Exception as e:
            logger.error(f"Error getting carbon intensity for {region}: {e}")
            return None
    
    def _get_real_intensity(self, region: str) -> Optional[float]:
        """Get real carbon intensity data from WattTime"""
        try:
            headers = {'Authorization': f'Bearer {self.token}'}
            url = f"{self.base_url}/v3/signal-index"
            params = {
                'region': region,
                'signal_type': 'co2_moer'
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            logger.info(f"WattTime API response status: {response.status_code}")
            
            response.raise_for_status()
            data = response.json()
            
            if 'data' in data and len(data['data']) > 0:
                intensity = data['data'][0]['value']
                logger.info(f"🌱 REAL carbon intensity for {region}: {intensity:.2f} lbs CO2/MWh")
                return intensity
            else:
                logger.warning(f"No carbon intensity data available for {region}")
                return 600.0  # Fallback value
                
        except Exception as e:
            logger.error(f"Failed to get real carbon intensity for {region}: {e}")
            return 600.0  # Fallback value
    
    def _get_simulated_intensity(self, base_intensity: float) -> float:
        """Generate realistic simulated carbon intensity data"""
        # Add time-based variation (lower at night, higher during peak hours)
        hour = datetime.now().hour
        time_factor = 0.8 + 0.4 * math.sin((hour - 6) * math.pi / 12)
        
        # Add random variation (±20%)
        random_factor = 1 + (random.random() - 0.5) * 0.4
        
        # Calculate final intensity
        intensity = base_intensity * time_factor * random_factor
        
        # Ensure reasonable bounds (200-1000 lbs CO2/MWh)
        intensity = max(200, min(1000, intensity))
        
        logger.info(f"🤖 SIMULATED carbon intensity: {intensity:.2f} lbs CO2/MWh")
        return intensity


class DataplaneController:
    """Manages HAProxy server weights via Dataplane API"""
    
    def __init__(self, host: str = "haproxy", port: int = 5555):
        self.host = host
        self.port = port
        self.base_url = f"http://{host}:{port}"
        self.auth = HTTPBasicAuth("admin", "password")
        self.backend = "local_servers"
    
    def set_server_weight(self, server_name: str, weight: int) -> bool:
        """Set weight for a specific server using Dataplane API"""
        try:
            # Get current config version
            version_url = f"{self.base_url}/v2/services/haproxy/configuration/version"
            version_response = requests.get(version_url, auth=self.auth, timeout=5)
            
            if version_response.status_code != 200:
                logger.error(f"Could not get configuration version: {version_response.status_code}")
                return False
            
            version = version_response.json()
            
            # Get current server config
            server_url = f"{self.base_url}/v2/services/haproxy/configuration/servers/{server_name}"
            params = {"backend": self.backend}
            response = requests.get(server_url, auth=self.auth, params=params, timeout=5)
            
            if response.status_code != 200:
                logger.error(f"Could not get current server config: {response.status_code}")
                return False
            
            current_config = response.json()["data"]
            
            # Update weight
            updated_config = current_config.copy()
            updated_config["weight"] = int(weight)
            
            # Send PUT request
            put_params = {"backend": self.backend, "version": version}
            put_response = requests.put(
                server_url, 
                auth=self.auth, 
                params=put_params,
                json=updated_config,
                headers={"Content-Type": "application/json"},
                timeout=5
            )
            
            if put_response.status_code in [200, 202]:  # 200 OK or 202 Accepted
                logger.info(f"✓ Set {server_name} weight to {weight}")
                return True
            else:
                logger.error(f"✗ Failed to set weight: {put_response.status_code} - {put_response.text}")
                return False
                
        except Exception as e:
            logger.error(f"✗ Error setting weight for {server_name}: {e}")
            return False
    
    def get_servers(self) -> Optional[List[Dict]]:
        """Get current server configurations"""
        try:
            url = f"{self.base_url}/v2/services/haproxy/configuration/servers"
            params = {"backend": self.backend}
            response = requests.get(url, auth=self.auth, params=params, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                return data.get("data", [])
            return None
        except Exception as e:
            logger.error(f"Error getting servers: {e}")
            return None


class GreenCDNController:
    """Main controller that coordinates carbon data and load balancing"""
    
    def __init__(self):
        # Initialize WattTime API
        username = os.getenv('WATTTIME_USERNAME')
        password = os.getenv('WATTTIME_PASSWORD')
        
        if not username or not password:
            logger.error("WattTime credentials not found in .env file")
            raise ValueError("Missing WattTime credentials")
        
        self.watttime = WattTimeAPI(username, password)
        self.dataplane = DataplaneController()
        
        # Server to region mapping
        self.server_regions = {
            'n1': {'region': 'CAISO_NORTH', 'name': 'US West (California)', 'type': 'real'},
            'n2': {'region': 'ERCOT', 'name': 'US Central (Texas)', 'base_intensity': 500, 'type': 'simulated'},
            'n3': {'region': 'PJM', 'name': 'US East (Mid-Atlantic)', 'base_intensity': 700, 'type': 'simulated'}
        }
        
        logger.info("Green CDN Controller initialized")
    
    def calculate_green_weights(self, carbon_intensities: Dict[str, float]) -> Dict[str, int]:
        """Calculate server weights based on carbon intensity (lower carbon = higher weight)"""
        
        # Convert carbon intensities to "green scores" (inverted)
        green_scores = {}
        for server, intensity in carbon_intensities.items():
            # Invert: lower carbon intensity = higher green score
            green_scores[server] = 1000.0 / intensity
        
        # Find min and max scores for normalization
        min_score = min(green_scores.values())
        max_score = max(green_scores.values())
        score_range = max_score - min_score
        
        # Convert to HAProxy weights (1-256)
        weights = {}
        for server, score in green_scores.items():
            if score_range > 0:
                # Normalize to 0-1, then scale to 50-256 (ensuring minimum traffic)
                normalized = (score - min_score) / score_range
                weight = int(50 + normalized * 206)  # 50-256 range
            else:
                weight = 150  # Equal weights if all scores are the same
            
            weights[server] = weight
        
        return weights
    
    def update_weights(self):
        """Fetch carbon data and update HAProxy weights accordingly"""
        logger.info("🌱 Starting carbon intensity check and weight update...")
        
        # Get carbon intensity for each region
        carbon_intensities = {}
        for server_id, config in self.server_regions.items():
            region = config['region']
            base_intensity = config.get('base_intensity')
            
            intensity = self.watttime.get_carbon_intensity(region, base_intensity)
            if intensity is not None:
                carbon_intensities[server_id] = intensity
                marker = "🌱 REAL" if config['type'] == 'real' else "🤖 SIM"
                logger.info(f"{marker} {config['name']}: {intensity:.2f} lbs CO2/MWh")
        
        if not carbon_intensities:
            logger.error("No carbon intensity data available")
            return
        
        # Calculate new weights based on carbon data
        new_weights = self.calculate_green_weights(carbon_intensities)
        
        # Update HAProxy weights
        logger.info("⚖️ Updating HAProxy server weights...")
        success_count = 0
        for server_name, weight in new_weights.items():
            success = self.dataplane.set_server_weight(server_name, weight)
            if success:
                intensity = carbon_intensities[server_name]
                region_name = self.server_regions[server_name]['name']
                logger.info(f"✓ {region_name}: weight={weight} (carbon: {intensity:.1f})")
                success_count += 1
            else:
                logger.error(f"✗ Failed to update weight for {server_name}")
        
        logger.info(f"Weight update completed: {success_count}/{len(new_weights)} servers updated\n")
    
    def run_continuous(self, interval_minutes: int = 5):
        """Run the controller continuously with specified interval"""
        logger.info("🌱 Green CDN Carbon Controller - Starting Up")
        logger.info("=" * 60)
        logger.info(f"⏰ Update interval: {interval_minutes} minutes")
        logger.info(f"🌍 Monitoring regions: {len(self.server_regions)} servers")
        logger.info("=" * 60)
        
        # Initial authentication
        if not self.watttime.login():
            logger.error("Failed to authenticate with WattTime API on startup")
            return
        
        logger.info("🌱 Ready for carbon-aware weight management!")
        
        while True:
            try:
                self.update_weights()
                logger.info(f"😴 Next update in {interval_minutes} minutes...")
                time.sleep(interval_minutes * 60)
                
            except KeyboardInterrupt:
                logger.info("🛑 Shutting down Green CDN Controller...")
                break
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                logger.info("Continuing after error...")
                time.sleep(60)  # Wait 1 minute before retrying


def main():
    """Main entry point"""
    try:
        controller = GreenCDNController()
        
        # Check if running in container or locally
        import sys
        if len(sys.argv) > 1 and sys.argv[1] == "--once":
            # Run once for testing
            print("Running single update cycle...")
            controller.update_weights()
        else:
            # Run continuously
            controller.run_continuous(interval_minutes=5)
        
    except Exception as e:
        logger.error(f"Failed to start Green CDN Controller: {e}")


if __name__ == "__main__":
    main() 