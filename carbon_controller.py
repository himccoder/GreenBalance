#!/usr/bin/env python3
"""
Green CDN Carbon Controller

This script fetches real-time carbon intensity data from WattTime API
and dynamically adjusts HAProxy server weights to favor servers in regions
with lower carbon intensity (greener energy).
"""

import os
import time
import socket
import logging
from typing import Dict, List, Optional
from datetime import datetime

import requests
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
            
            self.token = response.json()['token']
            logger.info("Successfully authenticated with WattTime API")
            return True
            
        except Exception as e:
            logger.error(f"Failed to authenticate with WattTime API: {e}")
            return False
    
    def get_carbon_intensity(self, region: str, base_intensity: Optional[float] = None) -> Optional[float]:
        """
        Get carbon intensity - real data for CAISO_NORTH, simulated for others
        
        Args:
            region: WattTime region code or 'simulated_*'
            base_intensity: Base intensity for simulated regions
        
        Returns:
            Carbon intensity value (lbs CO2/MWh) or None if failed
        """
        # Handle simulated regions (for free account limitations)
        if region.startswith('simulated_'):
            return self._get_simulated_intensity(base_intensity or 400)
        
        # Real API call for CAISO_NORTH (your free account access)
        if not self.token:
            if not self.login():
                return None
        
        try:
            headers = {'Authorization': f'Bearer {self.token}'}
            params = {
                'region': region,
                'signal_type': 'co2_moer'  # Marginal Operating Emissions Rate
            }
            
            # Use v3 API forecast endpoint for real-time data
            # Try with horizon_hours=0 for current data only
            params['horizon_hours'] = 0
            
            response = requests.get(
                f"{self.base_url}/v3/forecast",
                headers=headers,
                params=params,
                timeout=10
            )
            
            logger.info(f"WattTime API response status: {response.status_code}")
            if response.status_code != 200:
                logger.error(f"WattTime API error: {response.text}")
                return None
                
            data = response.json()
            logger.info(f"WattTime API response: {str(data)[:200]}...")
            
            # Get the first (current) forecast point
            if 'forecast' in data and len(data['forecast']) > 0:
                current_data = data['forecast'][0]
                intensity = current_data.get('value', 0)  # lbs CO2/MWh
                
                logger.info(f"🌱 REAL carbon intensity for {region}: {intensity:.2f} lbs CO2/MWh")
                return intensity
            elif 'data' in data and len(data['data']) > 0:
                # Alternative response format
                current_data = data['data'][0]
                intensity = current_data.get('value', 0)
                
                logger.info(f"🌱 REAL carbon intensity for {region}: {intensity:.2f} lbs CO2/MWh")
                return intensity
            else:
                logger.warning(f"No forecast data available for {region}. Response keys: {list(data.keys())}")
                return None
            
        except Exception as e:
            logger.error(f"Failed to get carbon intensity for {region}: {e}")
            return None
    
    def _get_simulated_intensity(self, base_intensity: float) -> float:
        """
        Generate realistic simulated carbon intensity based on time of day
        """
        import random
        from datetime import datetime
        
        # Get current hour
        current_hour = datetime.now().hour
        
        # Simulate daily carbon intensity patterns
        # Higher during day (more fossil), lower at night (more renewable)
        if 6 <= current_hour <= 18:  # Daytime
            variation = random.uniform(0.9, 1.3)  # 10-30% higher
        else:  # Nighttime  
            variation = random.uniform(0.7, 1.1)  # 30% lower to 10% higher
        
        simulated_value = base_intensity * variation
        logger.info(f"🤖 SIMULATED carbon intensity: {simulated_value:.2f} lbs CO2/MWh")
        return simulated_value


class HAProxyController:
    """Manages HAProxy server weights via admin socket"""
    
    def __init__(self, socket_path: str = "/var/run/admin.sock"):
        self.socket_path = socket_path
    
    def send_command(self, command: str) -> Optional[str]:
        """Send a command to HAProxy admin socket"""
        try:
            # Create Unix socket connection
            sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            sock.connect(self.socket_path)
            
            # Send command
            sock.send((command + '\n').encode())
            
            # Read response
            response = sock.recv(1024).decode().strip()
            sock.close()
            
            logger.debug(f"HAProxy command '{command}' -> '{response}'")
            return response
            
        except Exception as e:
            logger.error(f"Failed to send HAProxy command '{command}': {e}")
            return None
    
    def set_server_weight(self, backend: str, server: str, weight: int) -> bool:
        """Set weight for a specific server"""
        command = f"set weight {backend}/{server} {weight}"
        response = self.send_command(command)
        
        if response:
            logger.info(f"Set {backend}/{server} weight to {weight}")
            return True
        return False
    
    def get_server_stats(self) -> Optional[str]:
        """Get current server statistics"""
        return self.send_command("show stat")


class GreenCDNController:
    """Main controller that coordinates carbon data and load balancing"""
    
    def __init__(self):
        # Initialize WattTime API
        username = os.getenv('WATTTIME_USERNAME')
        password = os.getenv('WATTTIME_PASSWORD')
        
        if not username or not password:
            raise ValueError("WATTTIME_USERNAME and WATTTIME_PASSWORD must be set in .env file")
        
        self.watttime = WattTimeAPI(username, password)
        self.haproxy = HAProxyController()
        
        # Server configurations - adapted for FREE WattTime account
        # s1 gets real data, s2/s3 get simulated values based on typical patterns
        self.servers = {
            's1': {
                'backend': 'webservers',
                'region': 'CAISO_NORTH',   # Your FREE account has full access to this!
                'location': 'US West (California)',
                'access_type': 'full'
            },
            's2': {
                'backend': 'webservers', 
                'region': 'simulated_central',  # We'll simulate Texas data
                'location': 'US Central (Simulated)',
                'access_type': 'simulated',
                'base_intensity': 450  # Typical Texas intensity (lbs CO2/MWh)
            },
            's3': {
                'backend': 'webservers',
                'region': 'simulated_east',     # We'll simulate PJM data  
                'location': 'US East (Simulated)',
                'access_type': 'simulated',
                'base_intensity': 550  # Typical PJM intensity (higher)
            }
        }
        
        # Weight calculation settings
        self.max_weight = 256  # Maximum HAProxy weight
        self.min_weight = 1    # Minimum HAProxy weight
    
    def calculate_green_weights(self, carbon_intensities: Dict[str, float]) -> Dict[str, int]:
        """
        Calculate server weights based on carbon intensity
        Lower carbon intensity = higher weight (more traffic)
        """
        if not carbon_intensities:
            # If no data available, use equal weights
            return {server: self.max_weight for server in self.servers.keys()}
        
        # Invert carbon intensities (lower intensity = higher score)
        max_intensity = max(carbon_intensities.values())
        green_scores = {}
        
        for server, intensity in carbon_intensities.items():
            # Invert: 100% intensity becomes 0 score, 0% intensity becomes max score
            green_scores[server] = max_intensity - intensity + 1
        
        # Normalize scores to weights between min_weight and max_weight
        total_score = sum(green_scores.values())
        weights = {}
        
        for server, score in green_scores.items():
            # Proportional weight based on green score
            weight_ratio = score / total_score
            weight = int(self.min_weight + (self.max_weight - self.min_weight) * weight_ratio)
            weights[server] = max(weight, self.min_weight)  # Ensure minimum weight
        
        return weights
    
    def update_weights(self):
        """Fetch carbon data and update HAProxy weights accordingly"""
        logger.info("Starting carbon intensity check and weight update...")
        
        # Get carbon intensity for each region
        carbon_intensities = {}
        for server_name, config in self.servers.items():
            if config['access_type'] == 'full':
                # Real API call for CAISO_NORTH
                intensity = self.watttime.get_carbon_intensity(config['region'])
            else:
                # Simulated data for other regions (free account limitation)
                intensity = self.watttime.get_carbon_intensity(
                    config['region'], 
                    config['base_intensity']
                )
            
            if intensity is not None:
                carbon_intensities[server_name] = intensity
                access_marker = "🌱 REAL" if config['access_type'] == 'full' else "🤖 SIM"
                logger.info(f"{access_marker} {config['location']}: {intensity:.2f} lbs CO2/MWh")
        
        # Calculate new weights based on carbon data
        new_weights = self.calculate_green_weights(carbon_intensities)
        
        # Update HAProxy weights
        logger.info("Updating HAProxy server weights...")
        for server_name, weight in new_weights.items():
            server_config = self.servers[server_name]
            success = self.haproxy.set_server_weight(
                server_config['backend'], 
                server_name, 
                weight
            )
            
            if success:
                intensity = carbon_intensities.get(server_name, 'N/A')
                logger.info(f"✓ {server_config['location']}: weight={weight} (carbon: {intensity}%)")
            else:
                logger.error(f"✗ Failed to update weight for {server_name}")
        
        logger.info("Weight update completed\n")
    
    def run_continuous(self, interval_minutes: int = 5):
        """Run the controller continuously with specified interval"""
        logger.info(f"Starting Green CDN Controller (update interval: {interval_minutes} minutes)")
        
        # Initial authentication
        if not self.watttime.login():
            logger.error("Failed to authenticate with WattTime API on startup")
            return
        
        while True:
            try:
                self.update_weights()
                logger.info(f"Sleeping for {interval_minutes} minutes...")
                time.sleep(interval_minutes * 60)
                
            except KeyboardInterrupt:
                logger.info("Shutting down Green CDN Controller...")
                break
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                logger.info("Continuing after error...")
                time.sleep(60)  # Wait 1 minute before retrying


def main():
    """Main entry point"""
    try:
        controller = GreenCDNController()
        
        # Run once for testing
        print("Running single update cycle...")
        controller.update_weights()
        
        # Uncomment the line below to run continuously
        # controller.run_continuous(interval_minutes=5)
        
    except Exception as e:
        logger.error(f"Failed to start Green CDN Controller: {e}")


if __name__ == "__main__":
    main() 