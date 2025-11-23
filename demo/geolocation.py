"""
Geolocation utilities for lawyer recommendation
Handles IP-based location detection and distance calculation
"""

import json
import requests
from typing import Dict, Tuple, Optional
from math import radians, sin, cos, sqrt, atan2


def get_user_location_from_ip(ip_address: str = None) -> Dict:
    """
    Get user location from IP address using ipapi.co (free tier)

    Args:
        ip_address: Optional IP address. If None, detects automatically

    Returns:
        Dict with city, latitude, longitude, country
    """
    try:
        if ip_address:
            url = f"https://ipapi.co/{ip_address}/json/"
        else:
            # Automatic detection
            url = "https://ipapi.co/json/"

        response = requests.get(url, timeout=5)

        if response.status_code == 200:
            data = response.json()
            return {
                "city": data.get("city", "Budapest"),  # Default Budapest
                "latitude": data.get("latitude", 47.4979),
                "longitude": data.get("longitude", 19.0402),
                "country": data.get("country_name", "Hungary"),
                "region": data.get("region", "Budapest"),
                "postal": data.get("postal", "1000")
            }
        else:
            # Fallback to Budapest center
            return get_default_location()

    except Exception as e:
        print(f"Geolocation error: {e}")
        return get_default_location()


def get_default_location() -> Dict:
    """Return default location (Budapest center)"""
    return {
        "city": "Budapest",
        "latitude": 47.4979,
        "longitude": 19.0402,
        "country": "Hungary",
        "region": "Budapest",
        "postal": "1000"
    }


def parse_location_input(location_string: str) -> Dict:
    """
    Parse user-provided location string

    Args:
        location_string: City name or postal code

    Returns:
        Dict with approximate coordinates
    """
    location_lower = location_string.lower().strip()

    # Budapest district mapping
    budapest_districts = {
        "i. kerület": (47.4983, 19.0343),
        "ii. kerület": (47.5167, 19.0315),
        "iii. kerület": (47.5421, 19.0428),
        "iv. kerület": (47.5633, 19.0791),
        "v. kerület": (47.5034, 19.0458),
        "vi. kerület": (47.5048, 19.0632),
        "vii. kerület": (47.4969, 19.0632),
        "viii. kerület": (47.4963, 19.0684),
        "ix. kerület": (47.4717, 19.0824),
        "x. kerület": (47.4817, 19.1004),
        "xi. kerület": (47.4692, 19.0507),
        "xii. kerület": (47.4934, 19.0207),
        "xiii. kerület": (47.5174, 19.0501),
        "xiv. kerület": (47.5102, 19.1157),
    }

    # Check for Budapest district
    for district, coords in budapest_districts.items():
        if district in location_lower:
            return {
                "city": f"Budapest, {district.upper()}",
                "latitude": coords[0],
                "longitude": coords[1],
                "country": "Hungary",
                "region": "Budapest"
            }

    # Check for Budapest (general)
    if "budapest" in location_lower:
        return get_default_location()

    # Major Hungarian cities
    cities = {
        "debrecen": (47.5316, 21.6273),
        "szeged": (46.2530, 20.1414),
        "miskolc": (48.1035, 20.7784),
        "pécs": (46.0727, 18.2324),
        "győr": (47.6875, 17.6504),
        "nyíregyháza": (47.9559, 21.7177),
        "kecskemét": (46.9061, 19.6892),
        "székesfehérvár": (47.1898, 18.4306),
    }

    for city, coords in cities.items():
        if city in location_lower:
            return {
                "city": city.capitalize(),
                "latitude": coords[0],
                "longitude": coords[1],
                "country": "Hungary",
                "region": city.capitalize()
            }

    # Fallback: Budapest
    return get_default_location()


def calculate_distance(
    lat1: float, lon1: float,
    lat2: float, lon2: float
) -> float:
    """
    Calculate distance between two GPS coordinates using Haversine formula

    Args:
        lat1, lon1: First coordinate (latitude, longitude)
        lat2, lon2: Second coordinate (latitude, longitude)

    Returns:
        Distance in kilometers
    """
    # Earth radius in kilometers
    R = 6371.0

    # Convert degrees to radians
    lat1_rad = radians(lat1)
    lon1_rad = radians(lon1)
    lat2_rad = radians(lat2)
    lon2_rad = radians(lon2)

    # Differences
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad

    # Haversine formula
    a = sin(dlat / 2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    distance = R * c
    return round(distance, 1)


def get_location_display_name(location: Dict) -> str:
    """
    Format location for display

    Args:
        location: Location dict with city, region, etc.

    Returns:
        Formatted string
    """
    city = location.get("city", "Ismeretlen")
    region = location.get("region", "")

    if region and region != city:
        return f"{city}, {region}"
    return city


# Example usage
if __name__ == "__main__":
    # Test IP-based location
    location = get_user_location_from_ip()
    print(f"Detected location: {location}")

    # Test manual input
    manual_loc = parse_location_input("Budapest V. kerület")
    print(f"Parsed location: {manual_loc}")

    # Test distance calculation
    budapest = (47.4979, 19.0402)
    v_kerulet = (47.5034, 19.0458)
    distance = calculate_distance(budapest[0], budapest[1], v_kerulet[0], v_kerulet[1])
    print(f"Distance Budapest center to V. kerület: {distance} km")
