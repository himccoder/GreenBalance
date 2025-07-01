#!/usr/bin/env python3
"""
Test script for Green CDN

This script tests the carbon controller and HAProxy integration
by sending requests and monitoring weight changes.
"""

import time
import requests
from collections import Counter

def test_load_balancing():
    """Test current load balancing distribution"""
    print("Testing load balancing distribution...")
    
    responses = []
    total_requests = 20
    
    for i in range(total_requests):
        try:
            response = requests.get('http://localhost', timeout=5)
            server_text = response.text
            responses.append(server_text)
            print(f"Request {i+1}: {server_text}")
            time.sleep(0.5)  # Small delay between requests
            
        except Exception as e:
            print(f"Request {i+1} failed: {e}")
    
    # Count distribution
    print("\n=== Distribution Summary ===")
    counter = Counter(responses)
    for response, count in counter.items():
        percentage = (count / total_requests) * 100
        print(f"{response}: {count}/{total_requests} ({percentage:.1f}%)")

def test_haproxy_stats():
    """Check HAProxy statistics dashboard"""
    try:
        response = requests.get('http://localhost:8404', timeout=5)
        if response.status_code == 200:
            print("✓ HAProxy stats dashboard is accessible at http://localhost:8404")
        else:
            print(f"✗ HAProxy stats returned status {response.status_code}")
    except Exception as e:
        print(f"✗ HAProxy stats dashboard error: {e}")

def main():
    print("🌱 Green CDN Test Suite")
    print("=" * 50)
    
    # Test HAProxy dashboard
    test_haproxy_stats()
    print()
    
    # Test load balancing
    test_load_balancing()
    
    print("\n💡 Tips:")
    print("- Check HAProxy stats at http://localhost:8404")
    print("- Watch carbon controller logs: docker logs carbon-controller")
    print("- View HAProxy logs: docker logs haproxy")

if __name__ == "__main__":
    main() 