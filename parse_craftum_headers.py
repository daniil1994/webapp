#!/usr/bin/env python3
"""
Simple script for parsing HTTP headers from craftum.com
"""

import requests
import json
from datetime import datetime


def parse_craftum_headers(url="https://craftum.com"):
    """
    Parse and display HTTP headers from craftum.com
    
    Args:
        url: The URL to fetch headers from (default: https://craftum.com)
    
    Returns:
        dict: Dictionary containing headers and metadata
    """
    try:
        print(f"Fetching headers from: {url}")
        print("-" * 60)
        
        # Send GET request
        response = requests.get(url, timeout=10)
        
        # Extract headers
        headers = dict(response.headers)
        
        # Display basic info
        print(f"\nStatus Code: {response.status_code}")
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"URL: {response.url}")
        print("\n" + "=" * 60)
        print("HTTP HEADERS:")
        print("=" * 60)
        
        # Display headers in a formatted way
        for key, value in headers.items():
            print(f"{key}: {value}")
        
        print("\n" + "=" * 60)
        
        # Extract and display important security headers
        print("\nSECURITY HEADERS:")
        print("-" * 60)
        security_headers = [
            'Content-Security-Policy',
            'Strict-Transport-Security',
            'X-Content-Type-Options',
            'X-Frame-Options',
            'X-XSS-Protection',
            'Referrer-Policy',
            'Permissions-Policy'
        ]
        
        for header in security_headers:
            value = headers.get(header, 'Not set')
            print(f"{header}: {value}")
        
        # Save to JSON file
        output_data = {
            'timestamp': datetime.now().isoformat(),
            'url': url,
            'status_code': response.status_code,
            'headers': headers
        }
        
        output_file = 'craftum_headers.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n✓ Headers saved to: {output_file}")
        
        return output_data
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching headers: {e}")
        return None


if __name__ == "__main__":
    import sys
    
    # Allow custom URL as command line argument
    url = sys.argv[1] if len(sys.argv) > 1 else "https://craftum.com"
    
    parse_craftum_headers(url)
