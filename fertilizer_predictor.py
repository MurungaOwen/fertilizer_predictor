#!/usr/bin/env python3
"""
Fertilizer Predictor

This script fetches soil properties for any location in Africa using the iSDAsoil API
and uses Google Gemini to provide fertilizer recommendations based on soil data.

Tasks:
- Task A: Fetch soil properties (N, P, K, pH) from iSDAsoil API
- Task B: Generate fertilizer recommendations using LLM based on soil classifications
"""

import os
import requests
import time
from typing import Dict, Optional, Tuple
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()

# Network defaults
TIMEOUT_S = 15  # seconds

class SoilDataFetcher:
    """Handles interaction with the iSDAsoil API"""
    
    def __init__(self, username: str, password: str):
        """
        Initialize the SoilDataFetcher with credentials
        
        Args:
            username: iSDAsoil API username
            password: iSDAsoil API password
        """
        self.username = username
        self.password = password
        self.base_url = "https://api.isda-africa.com"
        self.access_token = None
        self.token_expiry = None
    
    def authenticate(self) -> bool:
        """
        Authenticate with the iSDAsoil API and obtain access token
        
        Returns:
            bool: True if authentication successful, False otherwise
        """
        try:
            login_url = f"{self.base_url}/login"
            headers = {
                "accept": "application/json",
                "Content-Type": "application/x-www-form-urlencoded"
            }
            login_data = {
                "grant_type": "password",
                "username": self.username,
                "password": self.password,
                "scope": "",
                "client_id": "string",
                "client_secret": "string"
            }
            
            response = requests.post(login_url, headers=headers, data=login_data)
            response.raise_for_status()
            
            token_data = response.json()
            self.access_token = token_data.get("access_token")
            # Token expires in 1 hour according to API docs
            self.token_expiry = time.time() + 3600
            
            print("Successfully authenticated with iSDAsoil API")
            return True
            
        except requests.exceptions.RequestException as e:
            print(f"Authentication failed: {e}")
            return False
    
    def _is_token_valid(self) -> bool:
        """Check if current token is valid and not expired"""
        return (self.access_token is not None and 
                self.token_expiry is not None and 
                time.time() < self.token_expiry - 300)  # Refresh 5 min before expiry
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers with authorization token"""
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
    
    def fetch_soil_properties(self, latitude: float, longitude: float) -> Optional[Dict]:
        """
        Fetch soil properties for a given location
        
        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
        """    
        try:
            # Query the soilproperty endpoint for top soil data (0-20cm depth)
            soil_url = f"{self.base_url}/isdasoil/v2/soilproperty"
            params = {
                "lon": longitude,
                "lat": latitude,
                "depth": "0-20"  # Top soil only as required
                # Don't specify property - get all properties then filter what we need
            }

            response = requests.get(
                soil_url,
                params=params,
                headers=self._get_headers(),
                timeout=TIMEOUT_S,
            )
            if response.status_code == 401:
                # Refresh token once and retry
                if self.authenticate():
                    response = requests.get(
                        soil_url,
                        params=params,
                        headers=self._get_headers(),
                        timeout=TIMEOUT_S,
                    )
                else:
                    return None
            response.raise_for_status()

            soil_data = response.json()
            print(f"Successfully fetched soil data for coordinates ({latitude}, {longitude})")

            return soil_data

        except requests.exceptions.RequestException as e:
            print(f"Failed to fetch soil properties: {e}")
            return None


class SoilClassifier:
    """Classifies soil properties according to the provided thresholds"""
    
    # Classification thresholds from Table 1
    THRESHOLDS = {
        "nitrogen": {"low": 1.5, "high": 5.0},
        "phosphorus": {"low": 10, "high": 50},
        "potassium": {"low": 39, "high": 195},
        "ph": {"low": 5.3, "high": 7.3}
    }
    @staticmethod
    def classify_property(value: float, property_name: str) -> str:
        """
        Classify a soil property value as Low, Moderate, or High
        
        Args:
            value: The property value to classify
            property_name: Name of the property (nitrogen, phosphorus, potassium, ph)
            
        Returns:
            str: Classification result ('Low', 'Moderate', 'High')
        """
        thresholds = SoilClassifier.THRESHOLDS.get(property_name.lower())
        if not thresholds:
            return "Unknown"

        try:
            v = float(value)
        except (TypeError, ValueError):
            return "Unknown"

        if v <= thresholds["low"]:
            return "Low"
        elif v <= thresholds["high"]:
            return "Moderate"
        else:
            return "High"
    
    @staticmethod
    def classify_soil_data(soil_data: Dict) -> Dict[str, Dict]:
        """
        Classify all soil properties in the dataset
        
        Args:
            soil_data: Raw soil data from API
            
        Returns:
            Dict containing classified soil properties
        """
        classified = {}
        
        # Map API response fields to our classification system
        property_mapping = {
            "nitrogen_total": "nitrogen",
            "phosphorous_extractable": "phosphorus", 
            "potassium_extractable": "potassium",
            "ph": "ph"
        }
        
        for api_field, class_name in property_mapping.items():
            if api_field in soil_data.get("property", {}):
                # API returns array of data objects, we want the first one for 0-20cm depth
                property_data = soil_data["property"][api_field]
                if property_data and len(property_data) > 0:
                    # Extract the actual value from the nested structure
                    value = property_data[0]["value"]["value"]
                    classification = SoilClassifier.classify_property(value, class_name)
                    classified[class_name] = {
                        "value": value,
                        "classification": classification
                    }
        
        return classified


class FertilizerRecommender:
    """Generates fertilizer recommendations using Google Gemini"""
    
    def __init__(self, api_key: str):
        """
        Initialize the FertilizerRecommender with Gemini API key
        
        Args:
            api_key: Google Gemini API key
        """
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash')
    
    def generate_recommendation(self, classified_soil: Dict[str, Dict]) -> str:
        """
        Generate fertilizer recommendation based on classified soil data
        
        Args:
            classified_soil: Dictionary containing classified soil properties
            
        Returns:
            str: Fertilizer recommendation from Gemini
        """
        # Create a detailed prompt with soil data and fertilizer options
        prompt = f"""
Based on the following soil analysis results, provide a specific fertilizer recommendation:

Soil Analysis:
- Nitrogen (N): {classified_soil.get('nitrogen', {}).get('value', 'N/A')} g/kg - Classification: {classified_soil.get('nitrogen', {}).get('classification', 'N/A')}
- Phosphorus (P): {classified_soil.get('phosphorus', {}).get('value', 'N/A')} mg/kg - Classification: {classified_soil.get('phosphorus', {}).get('classification', 'N/A')}
- Potassium (K): {classified_soil.get('potassium', {}).get('value', 'N/A')} mg/kg - Classification: {classified_soil.get('potassium', {}).get('classification', 'N/A')}
- pH: {classified_soil.get('ph', {}).get('value', 'N/A')} - Classification: {classified_soil.get('ph', {}).get('classification', 'N/A')}

Classification Guidelines:
- Nitrogen (N): Low ≤ 1.5, Moderate > 1.5 – ≤ 5.0, High > 5.0 g/kg
- Phosphorus (P): Low ≤ 10, Moderate > 10 – ≤ 50, High > 50 mg/kg
- Potassium (K): Low ≤ 39, Moderate > 39 – ≤ 195, High > 195 mg/kg
- pH: Low ≤ 5.3, Moderate > 5.3 – ≤ 7.3, High > 7.3

Available Fertilizer Options:
1. Urea (46-0-0) - High N, Low P, Low K
2. Ammonium Sulfate (21-0-0) - High N, Low P, Low K
3. Single Super Phosphate - Low N, Moderate P, Low K
4. Triple Super Phosphate - Low N, High P, Low K
5. Muriate of Potash - Low N, Low P, High K
6. Sulphate of Potash - Low N, Low P, High K
7. Lime - For raising soil pH

Please provide:
1. Primary fertilizer recommendation based on the soil deficiencies
2. Secondary recommendations if multiple nutrients are needed
3. pH adjustment recommendations if necessary
4. Brief explanation of why these fertilizers are recommended for this soil profile
"""

        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Error generating recommendation: {e}"


def main():
    """Main function to execute the complete workflow"""
    
    print("Fertilizer Predictor")
    print("=" * 50)
    
    # Load credentials from environment variables
    isda_username = os.getenv("ISDA_USERNAME")
    isda_password = os.getenv("ISDA_PASSWORD")
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    
    if not all([isda_username, isda_password, gemini_api_key]):
        print("Missing required environment variables. Please check your .env file.")
        print("Required: ISDA_USERNAME, ISDA_PASSWORD, GEMINI_API_KEY")
        return
    
    # Example coordinates in Kenya
    latitude = 0.0917 # Kisumu, Kenya
    longitude = 34.7680
    
    print(f"Fetching soil data for coordinates: {latitude}, {longitude}")
    
    # Task A: Fetch soil properties
    print("\nTask A: Fetching soil properties from iSDAsoil API...")
    soil_fetcher = SoilDataFetcher(isda_username, isda_password)
    
    soil_data = soil_fetcher.fetch_soil_properties(latitude, longitude)
    if not soil_data:
        print("Failed to fetch soil data. Exiting.")
        return
    
    #print("Raw soil data:", soil_data)
    
    # Classify soil properties
    print("\nClassifying soil properties...")
    classified_soil = SoilClassifier.classify_soil_data(soil_data)
    
    print("\nClassified Soil Properties:")
    for nutrient, data in classified_soil.items():
        print(f"  {nutrient.capitalize()}: {data['value']} - {data['classification']}")
    
    # Task B: Generate fertilizer recommendation
    print("\nTask B: Generating fertilizer recommendation using Gemini...")
    recommender = FertilizerRecommender(gemini_api_key)
    
    recommendation = recommender.generate_recommendation(classified_soil)
    
    print("\nFertilizer Recommendation:")
    print("-" * 30)
    print(recommendation)


if __name__ == "__main__":
    main()