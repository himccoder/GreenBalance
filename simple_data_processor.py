import csv
import os
import time
import threading
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import statistics
import logging
from requests.auth import HTTPBasicAuth

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleCarbonDataProcessor:
    """Simplified CSV processor using only built-in Python libraries."""
    
    def __init__(self, data_dir: str = "HistoricalData"):
        self.data_dir = data_dir
        self.available_regions = {
            "US-CAL-CISO": {"name": "California", "file": "US-CAL-CISO.csv"},
            "US-NY-NYIS": {"name": "New York", "file": "US-NY-NYIS.csv"},
            "US-TEX-ERCO": {"name": "Texas", "file": "US-TEX-ERCO.csv"}
        }
        self._data_cache = {}
    
    def get_available_regions(self) -> Dict[str, str]:
        """Get list of available regions for server assignment."""
        return {code: info["name"] for code, info in self.available_regions.items()}
    
    def load_region_data(self, region_code: str, max_rows: int | None = None) -> Optional[List[Dict]]:
        """Load RECENT data for a specific region - reads from END of CSV (2022) not beginning (2020)."""
        if region_code not in self.available_regions:
            logger.error(f"Region {region_code} not available")
            return None
        
        file_path = os.path.join(self.data_dir, self.available_regions[region_code]["file"])
        
        if not os.path.exists(file_path):
            logger.error(f"Data file not found: {file_path}")
            return None
        
        try:
            logger.info(f"Loading RECENT data for {region_code} (from END of CSV - 2022 data)...")
            
            # FIXED: Read ALL rows first, then take LAST ones (most recent)
            all_rows = []
            with open(file_path, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                all_rows = list(reader)
            
            # Optionally limit to last N rows for performance
            if max_rows is not None and len(all_rows) > max_rows:
                recent_rows = all_rows[-max_rows:]
            else:
                recent_rows = all_rows
            
            data = []
            for row in recent_rows:
                try:
                    # Parse datetime
                    dt = datetime.fromisoformat(row['datetime'].replace('Z', '+00:00'))
                    
                    # Parse carbon intensity
                    carbon_intensity = float(row['carbon_intensity_avg'])
                    
                    # Store cleaned data
                    data.append({
                        'datetime': dt,
                        'carbon_intensity_avg': carbon_intensity,
                        'zone_name': region_code,
                        'power_production_percent_renewable_avg': float(row.get('power_production_percent_renewable_avg', 0) or 0),
                        'power_production_wind_avg': float(row.get('power_production_wind_avg', 0) or 0),
                        'power_production_solar_avg': float(row.get('power_production_solar_avg', 0) or 0)
                    })
                    
                except (ValueError, KeyError) as e:
                    # Skip invalid rows
                    continue
            
            # Sort by datetime (most recent first)
            data.sort(key=lambda x: x['datetime'], reverse=True)
            
            # Log the date range we're actually using
            if data:
                oldest_date = data[-1]['datetime'].strftime('%Y-%m-%d')
                newest_date = data[0]['datetime'].strftime('%Y-%m-%d')
                logger.info(f"Loaded {len(data)} valid records for {region_code} | Date range: {oldest_date} to {newest_date}")
            else:
                logger.warning(f"No valid data loaded for {region_code}")
            
            return data
            
        except Exception as e:
            logger.error(f"Error loading data for {region_code}: {e}")
            return None
    
    def get_carbon_stats(self, region_code: str) -> Optional[Dict]:
        """Get carbon intensity statistics for a region."""
        data = self.load_region_data(region_code, max_rows=500)  # Last ~500 records
        if not data:
            return None
        
        carbon_values = [row['carbon_intensity_avg'] for row in data]
        
        if not carbon_values:
            return None
        
        stats = {
            'mean': statistics.mean(carbon_values),
            'min': min(carbon_values),
            'max': max(carbon_values),
            'current': carbon_values[0] if carbon_values else None,  # Most recent
            'std': statistics.stdev(carbon_values) if len(carbon_values) > 1 else 0,
            'trend': self._calculate_trend(carbon_values),
            'data_points': len(carbon_values)
        }
        
        return stats
    
    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate if carbon intensity is trending up, down, or stable."""
        if len(values) < 10:
            return "insufficient_data"
        
        # Compare recent 10% vs previous 10%
        n = len(values)
        recent_window = max(5, n // 10)
        
        recent_avg = statistics.mean(values[:recent_window])  # Most recent data
        previous_avg = statistics.mean(values[recent_window:recent_window*2])
        
        diff_pct = ((recent_avg - previous_avg) / previous_avg) * 100
        
        if diff_pct > 5:
            return "increasing"
        elif diff_pct < -5:
            return "decreasing"
        else:
            return "stable"
    
    def predict_carbon_intensity(self, region_code: str, hours_ahead: int = 24) -> Optional[Dict]:
        """EDUCATIONAL DEMO: Shows how prediction might work using 2022 historical patterns. NOT real future predictions."""
        data = self.load_region_data(region_code, max_rows=200)
        if not data:
            return None
        
        try:
            # Calculate hourly averages for seasonal pattern
            hourly_patterns = {}
            for row in data:
                hour = row['datetime'].hour
                if hour not in hourly_patterns:
                    hourly_patterns[hour] = []
                hourly_patterns[hour].append(row['carbon_intensity_avg'])
            
            # Average for each hour
            hourly_avg = {}
            for hour, values in hourly_patterns.items():
                hourly_avg[hour] = statistics.mean(values)
            
            # Generate pattern demonstration (using 2022 data to show typical patterns)
            last_datetime = data[0]['datetime']  # Most recent from 2022
            predictions = []
            
            # Recent trend from 2022 data
            recent_values = [row['carbon_intensity_avg'] for row in data[:24]]  # Last 24 records
            recent_trend = statistics.mean(recent_values) if recent_values else 0
            overall_avg = statistics.mean([row['carbon_intensity_avg'] for row in data])
            
            for i in range(1, hours_ahead + 1):
                hour_of_day = (last_datetime.hour + i) % 24  # Cycle through hours
                
                # Base pattern on hourly average from 2022
                seasonal_avg = hourly_avg.get(hour_of_day, overall_avg)
                
                # Weighted combination
                pattern_value = (seasonal_avg * 0.7) + (recent_trend * 0.3)
                
                predictions.append({
                    'hour_of_day': f'{hour_of_day:02d}:00',
                    'typical_carbon_intensity': round(pattern_value, 2),
                    'data_source': '2022 historical patterns',
                    'note': 'Educational demo - NOT real future prediction'
                })
            
            return {
                'region': region_code,
                'predictions': predictions,
                'base_stats': self.get_carbon_stats(region_code)
            }
            
        except Exception as e:
            logger.error(f"Error predicting for {region_code}: {e}")
            return None
    
    def generate_simple_chart_data(self, region_code: str) -> Dict:
        """Generate data for simple HTML charts."""
        data = self.load_region_data(region_code, max_rows=48)  # Last 48 records
        if not data:
            return {}
        
        # Prepare chart data
        chart_data = {
            'labels': [row['datetime'].strftime('%H:%M') for row in reversed(data[-24:])],  # Last 24 hours
            'carbon_values': [row['carbon_intensity_avg'] for row in reversed(data[-24:])],
            'renewable_values': [row['power_production_percent_renewable_avg'] for row in reversed(data[-24:])],
            'region_name': self.available_regions[region_code]['name']
        }
        
        return chart_data


class HAProxyDataplaneAPI:
    """
    HAProxy Dataplane API integration for updating server weights in real-time.
    
    This class handles communication with HAProxy's dataplane API to dynamically
    adjust backend server weights based on carbon intensity data. Used by both
    real-time (WATTIME) and historical simulation modes.
    """
    
    def __init__(self, host: str = "haproxy", port: int = 5555, user: str = "admin", password: str = "password"):
        """
        Initialize HAProxy Dataplane API connection.
        
        Args:
            host: HAProxy container name or IP (default: "haproxy" for Docker)
            port: Dataplane API port (default: 5555)
            user: API username (default: "admin")
            password: API password (default: "password")
        """
        self.host = host
        self.port = port
        self.base_url = f"http://{host}:{port}"
        self.auth = HTTPBasicAuth(user, password)
        self.backend = "local_servers"  # HAProxy backend name
        
        logger.info(f"HAProxy Dataplane API initialized: {self.base_url}")
    
    def get_configuration_version(self) -> Optional[int]:
        """
        Get current HAProxy configuration version.
        Required for making configuration changes via dataplane API.
        
        Returns:
            Configuration version number, or None if error
        """
        try:
            version_url = f"{self.base_url}/v2/services/haproxy/configuration/version"
            response = requests.get(version_url, auth=self.auth, timeout=5)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to get config version: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting configuration version: {e}")
            return None
    
    def set_server_weight(self, server_name: str, weight: int) -> bool:
        """
        Update weight for a specific HAProxy backend server.
        
        Weight determines how much traffic a server receives:
        - Higher weight = more traffic routed to this server
        - Lower weight = less traffic routed to this server
        - Range: 1-256 (HAProxy standard)
        
        Args:
            server_name: Server identifier (e.g., "n1", "n2", "n3")
            weight: New weight value (1-256)
            
        Returns:
            True if weight update successful, False otherwise
        """
        try:
            # Step 1: Get current configuration version
            version = self.get_configuration_version()
            if version is None:
                return False
            
            # Step 2: Get current server configuration
            server_url = f"{self.base_url}/v2/services/haproxy/configuration/servers/{server_name}"
            params = {"backend": self.backend}
            response = requests.get(server_url, auth=self.auth, params=params, timeout=5)
            
            if response.status_code != 200:
                logger.error(f"Failed to get server config for {server_name}: {response.status_code}")
                return False
            
            current_config = response.json()["data"]
            
            # Step 3: Update weight in configuration
            updated_config = current_config.copy()
            updated_config["weight"] = int(weight)
            
            # Step 4: Send PUT request to update server weight
            put_params = {"backend": self.backend, "version": version}
            put_response = requests.put(
                server_url,
                auth=self.auth,
                params=put_params,
                json=updated_config,
                headers={"Content-Type": "application/json"},
                timeout=5
            )
            
            if put_response.status_code in [200, 202]:  # Success codes
                logger.info(f"✓ Updated {server_name} weight to {weight}")
                return True
            else:
                logger.error(f"✗ Failed to update {server_name} weight: {put_response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"✗ Error updating weight for {server_name}: {e}")
            return False
    
    def get_current_weights(self) -> Optional[Dict[str, int]]:
        """
        Get current weights for all servers in the backend.
        
        Returns:
            Dictionary mapping server names to their current weights
        """
        try:
            url = f"{self.base_url}/v2/services/haproxy/configuration/servers"
            params = {"backend": self.backend}
            response = requests.get(url, auth=self.auth, params=params, timeout=5)
            
            if response.status_code == 200:
                servers = response.json()["data"]
                weights = {}
                for server in servers:
                    weights[server["name"]] = server.get("weight", 100)
                return weights
            else:
                logger.error(f"Failed to get server weights: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting server weights: {e}")
            return None


class HistoricalSimulationEngine:
    """
    Historical Carbon Intensity Simulation Engine.
    
    This class provides time-series simulation using historical CSV data to demonstrate
    how carbon-aware load balancing would have worked during past periods. Unlike the
    real-time WATTIME API integration, this replays historical data hour-by-hour to
    show routing decisions over time.
    
    Key Features:
    - Time-based simulation (hour-by-hour replay)
    - Real HAProxy weight updates via dataplane API
    - Cumulative impact tracking (carbon/cost savings)
    - Playback controls (play/pause/speed)
    """
    
    def __init__(self, data_processor: SimpleCarbonDataProcessor):
        """
        Initialize the simulation engine.
        
        Args:
            data_processor: Instance of SimpleCarbonDataProcessor for CSV data access
        """
        self.data_processor = data_processor
        self.haproxy_api = HAProxyDataplaneAPI()
        
        # Simulation state
        self.is_running = False
        self.is_paused = False
        self.current_time = None
        self.simulation_thread = None
        self.simulation_data = {}
        self.simulation_results = {}
        
        # Server region mapping (matches production setup)
        self.server_regions = {
            'n1': 'US-CAL-CISO',  # California server
            'n2': 'US-NY-NYIS',   # New York server  
            'n3': 'US-TEX-ERCO'   # Texas server
        }
        
        logger.info("Historical Simulation Engine initialized")
    
    def calculate_carbon_weights(self, carbon_intensities: Dict[str, float]) -> Dict[str, int]:
        """
        Calculate HAProxy server weights based on carbon intensity data.
        
        Algorithm Logic:
        1. Convert carbon intensities to "green scores" (lower carbon = higher score)
        2. Normalize scores to HAProxy weight range (50-256)
        3. Ensure minimum weight of 50 to maintain basic connectivity
        
        This algorithm favors servers in regions with lower carbon intensity,
        routing more traffic to "greener" locations while maintaining service availability.
        
        Args:
            carbon_intensities: Dict mapping server names to carbon intensity values
            
        Returns:
            Dict mapping server names to HAProxy weights (50-256 range)
        """
        if not carbon_intensities:
            logger.warning("No carbon intensity data available, using equal weights")
            return {server: 100 for server in self.server_regions.keys()}
        
        # Step 1: Convert carbon intensities to green scores (inverse relationship)
        green_scores = {}
        for server, intensity in carbon_intensities.items():
            # Invert carbon intensity: lower carbon = higher green score
            # Use 1000 as base to avoid very small numbers
            green_scores[server] = 1000.0 / max(intensity, 1.0)  # Avoid division by zero
        
        # Step 2: Normalize scores to HAProxy weight range
        min_score = min(green_scores.values())
        max_score = max(green_scores.values())
        score_range = max_score - min_score
        
        weights = {}
        for server, score in green_scores.items():
            if score_range > 0:
                # Normalize to 0-1, then scale to 50-256 range
                # 50 = minimum weight to ensure basic connectivity
                # 256 = maximum HAProxy weight
                normalized = (score - min_score) / score_range
                weight = int(50 + normalized * 206)
            else:
                # All scores equal = use default weight
                weight = 100
                
            weights[server] = weight
        
        return weights
    
    def load_simulation_period(self, start_date: str, end_date: str) -> bool:
        """
        Load historical data for simulation period.
        
        Args:
            start_date: Start date in "YYYY-MM-DD" format
            end_date: End date in "YYYY-MM-DD" format
            
        Returns:
            True if data loaded successfully, False otherwise
        """
        try:
            # If 'auto', we will compute min/max later
            auto_start = start_date == 'auto'
            auto_end = end_date == 'auto'
            from datetime import timezone
            start_dt = datetime.min.replace(tzinfo=timezone.utc) if auto_start else datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = datetime.max.replace(tzinfo=timezone.utc) if auto_end else datetime.strptime(end_date, "%Y-%m-%d")
            
            logger.info(f"Loading simulation data from {start_date} to {end_date}")
            
            # Load data for each region
            simulation_data = {}
            for server, region in self.server_regions.items():
                region_data = self.data_processor.load_region_data(region)
                if not region_data:
                    logger.error(f"Failed to load data for region {region}")
                    return False
                
                # Filter data by date range
                filtered_data = []
                for row in region_data:
                    row_date = row['datetime']
                    if start_dt <= row_date <= end_dt:
                        filtered_data.append(row)
                
                simulation_data[server] = filtered_data
                logger.info(f"Loaded {len(filtered_data)} records for {server} ({region})")
            
            self.simulation_data = simulation_data
            
            # Initialize results tracking
            self.simulation_results = {
                'timeline': [],
                'cumulative_carbon_saved': 0,
                'cumulative_cost_diff': 0,
                'weight_changes': []
            }
            
            return True
            
        except Exception as e:
            logger.error(f"Error loading simulation period: {e}")
            return False
    
    def get_carbon_at_time(self, target_time: datetime) -> Dict[str, float]:
        """
        Get carbon intensity values for all servers at a specific time.
        
        Args:
            target_time: Target datetime for carbon intensity lookup
            
        Returns:
            Dict mapping server names to carbon intensity values
        """
        carbon_values = {}
        
        for server, data_points in self.simulation_data.items():
            # Find closest data point to target time
            closest_point = None
            min_time_diff = float('inf')
            
            for point in data_points:
                time_diff = abs((point['datetime'] - target_time).total_seconds())
                if time_diff < min_time_diff:
                    min_time_diff = time_diff
                    closest_point = point
            
            if closest_point:
                carbon_values[server] = closest_point['carbon_intensity_avg']
        
        return carbon_values
    
    def simulate_hour(self, current_time: datetime, requests_per_hour: int = 1000) -> Dict:
        """
        Simulate one hour of operation with current carbon intensities.
        
        Args:
            current_time: Current simulation time
            requests_per_hour: Number of requests to simulate for this hour
            
        Returns:
            Dict containing simulation results for this hour
        """
        # Get carbon intensities at current time
        carbon_intensities = self.get_carbon_at_time(current_time)
        
        if not carbon_intensities:
            logger.warning(f"No carbon data available for {current_time}")
            return {}
        
        # Calculate new weights based on carbon data
        new_weights = self.calculate_carbon_weights(carbon_intensities)
        
        # Update HAProxy weights via dataplane API
        weight_update_success = {}
        for server, weight in new_weights.items():
            success = self.haproxy_api.set_server_weight(server, weight)
            weight_update_success[server] = success
        
        # Simulate request distribution based on weights
        total_weight = sum(new_weights.values())
        request_distribution = {}
        for server, weight in new_weights.items():
            if total_weight > 0:
                requests = int(requests_per_hour * weight / total_weight)
                request_distribution[server] = requests
        
        # Calculate carbon impact
        total_carbon = sum(request_distribution[server] * carbon_intensities[server] 
                          for server in new_weights.keys())
        
        # Compare with round-robin distribution
        rr_requests_per_server = requests_per_hour // len(new_weights)
        rr_carbon = sum(rr_requests_per_server * carbon_intensities[server] 
                       for server in new_weights.keys())
        
        carbon_saved = rr_carbon - total_carbon
        
        # Create hourly result
        result = {
            'time': current_time,
            'carbon_intensities': carbon_intensities,
            'weights': new_weights,
            'weight_update_success': weight_update_success,
            'request_distribution': request_distribution,
            'total_carbon': total_carbon,
            'carbon_saved_vs_rr': carbon_saved,
            'requests_per_hour': requests_per_hour
        }
        
        # Update cumulative results
        self.simulation_results['cumulative_carbon_saved'] += carbon_saved
        self.simulation_results['timeline'].append(result)
        self.simulation_results['weight_changes'].append({
            'time': current_time,
            'weights': new_weights.copy()
        })
        
        logger.info(f"Simulated hour {current_time.strftime('%Y-%m-%d %H:00')} - "
                   f"Carbon saved: {carbon_saved:.2f}g CO2")
        
        return result
    
    def start_simulation(self, start_date: str, end_date: str, 
                        requests_per_hour: int = 1000, speed_multiplier: float = 1.0):
        """
        Start historical simulation in a separate thread.
        
        Args:
            start_date: Start date in "YYYY-MM-DD" format
            end_date: End date in "YYYY-MM-DD" format  
            requests_per_hour: Simulated request rate
            speed_multiplier: Simulation speed (1.0 = real-time, 2.0 = 2x speed)
        """
        if self.is_running:
            logger.warning("Simulation already running")
            return False
        
        # Load simulation data
        if not self.load_simulation_period(start_date, end_date):
            logger.error("Failed to load simulation data")
            return False
        
        self.is_running = True
        self.is_paused = False
        
        def simulation_loop():
            """Main simulation loop - runs in separate thread"""
            if start_date == 'auto':
                start_dt = min(
                    min(points, key=lambda x: x['datetime'])['datetime'] for points in self.simulation_data.values()
                )
            else:
                start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            if end_date == 'auto':
                end_dt = max(
                    max(points, key=lambda x: x['datetime'])['datetime'] for points in self.simulation_data.values()
                )
            else:
                end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            
            current_time = start_dt
            sleep_duration = 1.0 / speed_multiplier  # Base: 1 second per hour
            
            logger.info(f"Starting simulation: {start_date} to {end_date} "
                       f"(speed: {speed_multiplier}x)")
            
            while current_time <= end_dt and self.is_running:
                if not self.is_paused:
                    self.current_time = current_time
                    
                    # Simulate this hour
                    self.simulate_hour(current_time, requests_per_hour)
                    
                    # Advance time by 1 hour
                    current_time += timedelta(hours=1)
                
                # Sleep to control simulation speed
                time.sleep(sleep_duration)
            
            self.is_running = False
            logger.info("Simulation completed")
        
        # Start simulation in background thread
        self.simulation_thread = threading.Thread(target=simulation_loop, daemon=True)
        self.simulation_thread.start()
        
        return True
    
    def pause_simulation(self):
        """Pause the running simulation"""
        self.is_paused = True
        logger.info("Simulation paused")
    
    def resume_simulation(self):
        """Resume the paused simulation"""
        self.is_paused = False
        logger.info("Simulation resumed")
    
    def stop_simulation(self):
        """Stop the running simulation"""
        self.is_running = False
        self.is_paused = False
        if self.simulation_thread:
            self.simulation_thread.join(timeout=2)
        logger.info("Simulation stopped")
    
    def get_simulation_status(self) -> Dict:
        """
        Get current simulation status and results.
        
        Returns:
            Dict containing simulation state and current results
        """
        return {
            'is_running': self.is_running,
            'is_paused': self.is_paused,
            'current_time': self.current_time.isoformat() if self.current_time else None,
            'results': self.simulation_results,
            'current_weights': self.haproxy_api.get_current_weights()
        }


# Utility functions for experiment app integration
def get_simple_processor() -> SimpleCarbonDataProcessor:
    """Get a singleton instance of the simple data processor."""
    if not hasattr(get_simple_processor, '_instance'):
        get_simple_processor._instance = SimpleCarbonDataProcessor()
    return get_simple_processor._instance

def get_simulation_engine() -> HistoricalSimulationEngine:
    """Get a singleton instance of the historical simulation engine."""
    if not hasattr(get_simulation_engine, '_instance'):
        processor = get_simple_processor()
        get_simulation_engine._instance = HistoricalSimulationEngine(processor)
    return get_simulation_engine._instance