# Fertilizer Predictor
A Python application that fetches soil properties for locations in Africa using the iSDAsoil API and provides fertilizer recommendations using Google Gemini AI.

## Overview

This project implements two main tasks:

**Task A**: Fetch soil properties (Nitrogen, Phosphorus, Potassium, pH) from the iSDAsoil API for any location in Africa.

**Task B**: Use Google Gemini to generate fertilizer recommendations based on soil classifications and available fertilizer options.

## Features

- Fetch soil data for any African coordinates using iSDAsoil API
- Classify soil properties according to agricultural thresholds  
- AI-powered fertilizer recommendations using Google Gemini
- Secure credential management with environment variables
- Comprehensive error handling and logging

## Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/MurungaOwen/fertilizer_predictor.git
   cd fertilizer_predictor
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` and add your credentials:
   - `ISDA_USERNAME`: Your iSDAsoil API username (register at https://isda-africa.com/api/registration)
   - `ISDA_PASSWORD`: Your iSDAsoil API password
   - `GEMINI_API_KEY`: Your Google Gemini API key (get from https://ai.google.dev/)

## Usage

Run the main script:
```bash
python fertilizer_predictor.py
```

The script will:
1. Authenticate with the iSDAsoil API
2. Fetch soil properties for the default location (Nairobi, Kenya)
3. Classify soil properties according to agricultural thresholds
4. Generate fertilizer recommendations using Gemini AI

## Soil Classification Thresholds

| Property | Low | Moderate | High |
|----------|-----|----------|------|
| Nitrogen (g/kg) | ≤ 1.5 | 1.5 - 5.0 | > 5.0 |
| Phosphorus (mg/kg) | ≤ 10 | 10 - 50 | > 50 |
| Potassium (mg/kg) | ≤ 39 | 39 - 195 | > 195 |
| pH | ≤ 5.3 | 5.3 - 7.3 | > 7.3 |

## Available Fertilizers

- Urea (46-0-0) - High N, Low P, Low K
- Ammonium Sulfate (21-0-0) - High N, Low P, Low K  
- Single Super Phosphate - Low N, Moderate P, Low K
- Triple Super Phosphate - Low N, High P, Low K
- Muriate of Potash - Low N, Low P, High K
- Sulphate of Potash - Low N, Low P, High K
- Lime - For raising soil pH

## API Documentation

- **iSDAsoil API**: https://api.isda-africa.com/isdasoil/v2/docs
- **Google Gemini AI**: https://ai.google.dev/

## License

This project is for educational purposes as part of the iSDA take-home assignment.
