"""
Lawyer Recommender System
Location-based lawyer recommendations with specialization filtering
"""

import json
from pathlib import Path
from typing import List, Dict, Optional
from geolocation import calculate_distance, get_location_display_name


class LawyerRecommender:
    """Recommend lawyers based on location and specialization"""

    def __init__(self, lawyers_db_path: str = "data/lawyers.json"):
        """
        Initialize recommender

        Args:
            lawyers_db_path: Path to lawyers.json database
        """
        self.lawyers_db_path = Path(lawyers_db_path)
        self.lawyers = self._load_lawyers()

    def _load_lawyers(self) -> List[Dict]:
        """Load lawyers from JSON database"""
        if not self.lawyers_db_path.exists():
            raise FileNotFoundError(f"Lawyers database not found: {self.lawyers_db_path}")

        with open(self.lawyers_db_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        return data.get('lawyers', [])

    def recommend_lawyers(
        self,
        user_location: Dict,
        legal_category: str,
        max_distance_km: float = 50.0,
        top_n: int = 5
    ) -> List[Dict]:
        """
        Recommend lawyers based on location and legal category

        Args:
            user_location: Dict with latitude, longitude
            legal_category: Legal category (munkajog, fogyasztóvédelem, etc.)
            max_distance_km: Maximum distance in km
            top_n: Number of recommendations to return

        Returns:
            List of recommended lawyers with distance and relevance score
        """
        user_lat = user_location.get('latitude')
        user_lon = user_location.get('longitude')

        if not user_lat or not user_lon:
            raise ValueError("User location must have latitude and longitude")

        # Calculate distance and filter
        candidates = []

        for lawyer in self.lawyers:
            lawyer_coords = lawyer['location']['coordinates']
            lawyer_lat, lawyer_lon = lawyer_coords

            # Calculate distance
            distance = calculate_distance(user_lat, user_lon, lawyer_lat, lawyer_lon)

            # Filter by max distance
            if distance > max_distance_km:
                continue

            # Check specialization match
            specializations = [s.lower() for s in lawyer['specialization']]
            category_match = any(legal_category.lower() in spec for spec in specializations)

            # Calculate relevance score
            # - Distance: closer is better (inverse weighting)
            # - Rating: higher is better
            # - Specialization match: strong bonus
            # - Partnership tier: premium gets bonus

            distance_score = max(0, 1 - (distance / max_distance_km))  # 0-1, closer = higher
            rating_score = lawyer['rating'] / 5.0  # 0-1
            specialization_bonus = 0.5 if category_match else 0.0
            premium_bonus = 0.2 if lawyer['partnership_tier'] == 'premium' else 0.0

            relevance_score = (
                distance_score * 0.3 +
                rating_score * 0.4 +
                specialization_bonus +
                premium_bonus
            )

            candidates.append({
                "lawyer": lawyer,
                "distance_km": distance,
                "relevance_score": relevance_score,
                "specialization_match": category_match
            })

        # Sort by relevance score (descending)
        candidates.sort(key=lambda x: x['relevance_score'], reverse=True)

        # Return top N
        return candidates[:top_n]

    def format_recommendation(self, recommendation: Dict) -> str:
        """
        Format a single lawyer recommendation for display

        Args:
            recommendation: Dict from recommend_lawyers()

        Returns:
            Formatted string
        """
        lawyer = recommendation['lawyer']
        distance = recommendation['distance_km']

        lines = []
        lines.append(f"**{lawyer['name']}**")
        lines.append(f"📍 {lawyer['location']['address']}, {lawyer['location']['district']} ({distance} km)")
        lines.append(f"⭐ {lawyer['rating']}/5.0 ({lawyer['reviews_count']} értékelés)")
        lines.append(f"💼 Szakosodás: {', '.join(lawyer['specialization'][:3])}")
        lines.append(f"📞 {lawyer['contact']['phone']}")
        lines.append(f"✉️ {lawyer['contact']['email']}")
        lines.append(f"🗺️ [Google Maps link]({lawyer['contact']['google_maps_url']})")
        lines.append(f"💰 Első konzultáció: {lawyer['consultation_fee']}")
        lines.append(f"🕐 Válaszidő: {lawyer['response_time']}")

        if lawyer['partnership_tier'] == 'premium':
            lines.append("⭐ **Prémium Partner**")

        return "\n".join(lines)

    def get_no_results_message(self, legal_category: str, location: Dict) -> str:
        """
        Generate message when no lawyers found

        Args:
            legal_category: Legal category
            location: User location

        Returns:
            Helpful message
        """
        city = location.get('city', 'az Ön területén')

        message = f"""
Sajnáljuk, nem találtunk {legal_category} szakértő ügyvédet {city} területén (50 km-en belül).

**Ajánlásaink:**

1. **Bővítse a keresési területet**: Szeretne országos szinten keresni?

2. **Online tanácsadás**: Sok ügyvéd nyújt online konzultációt videóhívás útján.

3. **Alternatív szakosodás**: Keressünk általános jogi tanácsadót, aki segíthet?

4. **Magyar Ügyvédi Kamara**: Látogassa meg a hivatalos ügyvédkeresőt: https://magyarugyvedikamara.hu/
"""
        return message

    def get_category_display_name(self, category: str) -> str:
        """Get human-readable category name"""
        category_names = {
            "munkajog": "Munkajog",
            "fogyasztóvédelem": "Fogyasztóvédelem",
            "családjog": "Családjog",
            "ingatlan": "Ingatlan és Adásvétel",
            "büntetőjog": "Büntetőjog",
            "általános": "Általános jogi tanácsadás"
        }
        return category_names.get(category.lower(), category.capitalize())


# Example usage
if __name__ == "__main__":
    from geolocation import get_default_location

    # Initialize recommender
    recommender = LawyerRecommender("data/lawyers.json")

    # User location (Budapest center)
    user_loc = get_default_location()

    # Get recommendations for munkajog
    recommendations = recommender.recommend_lawyers(
        user_location=user_loc,
        legal_category="munkajog",
        max_distance_km=10.0,
        top_n=3
    )

    print(f"Found {len(recommendations)} lawyers:\n")

    for i, rec in enumerate(recommendations, 1):
        print(f"--- Ajánlás {i} ---")
        print(recommender.format_recommendation(rec))
        print(f"Relevancia pontszám: {rec['relevance_score']:.2f}\n")
