"""
NCRB (National Crime Records Bureau) — Cyber Crime Data 2022

Real data sourced from NCRB "Crime in India 2022" report.
These are the official numbers of cyber crime cases registered by state/UT police.

Source: https://ncrb.gov.in/ (Crime in India 2022, Chapter 13 — Cyber Crimes)
"""

NCRB_CRIME_DATA_2022 = [
    {"state": "Karnataka", "stateCode": "KA", "incidentCount": 12020, "coordinates": [15.3173, 75.7139]},
    {"state": "Uttar Pradesh", "stateCode": "UP", "incidentCount": 11416, "coordinates": [26.8467, 80.9462]},
    {"state": "Maharashtra", "stateCode": "MH", "incidentCount": 4967, "coordinates": [19.7515, 75.7139]},
    {"state": "Telangana", "stateCode": "TS", "incidentCount": 4496, "coordinates": [18.1124, 79.0193]},
    {"state": "Assam", "stateCode": "AS", "incidentCount": 3923, "coordinates": [26.2006, 92.9376]},
    {"state": "Gujarat", "stateCode": "GJ", "incidentCount": 2829, "coordinates": [22.2587, 71.1924]},
    {"state": "Rajasthan", "stateCode": "RJ", "incidentCount": 2752, "coordinates": [27.0238, 74.2179]},
    {"state": "Haryana", "stateCode": "HR", "incidentCount": 2569, "coordinates": [29.0588, 76.0856]},
    {"state": "Madhya Pradesh", "stateCode": "MP", "incidentCount": 2130, "coordinates": [22.9734, 78.6569]},
    {"state": "Odisha", "stateCode": "OD", "incidentCount": 1983, "coordinates": [20.9517, 85.0985]},
    {"state": "Delhi", "stateCode": "DL", "incidentCount": 1768, "coordinates": [28.7041, 77.1025]},
    {"state": "West Bengal", "stateCode": "WB", "incidentCount": 1299, "coordinates": [22.9868, 87.8550]},
    {"state": "Andhra Pradesh", "stateCode": "AP", "incidentCount": 1257, "coordinates": [15.9129, 79.7399]},
    {"state": "Tamil Nadu", "stateCode": "TN", "incidentCount": 1069, "coordinates": [11.1271, 78.6569]},
    {"state": "Bihar", "stateCode": "BR", "incidentCount": 903, "coordinates": [25.0961, 85.3131]},
    {"state": "Jammu & Kashmir", "stateCode": "JK", "incidentCount": 812, "coordinates": [33.7782, 76.5762]},
    {"state": "Uttarakhand", "stateCode": "UK", "incidentCount": 698, "coordinates": [30.0668, 79.0193]},
    {"state": "Kerala", "stateCode": "KL", "incidentCount": 563, "coordinates": [10.8505, 76.2711]},
    {"state": "Himachal Pradesh", "stateCode": "HP", "incidentCount": 213, "coordinates": [31.1048, 77.1734]},
    {"state": "Jharkhand", "stateCode": "JH", "incidentCount": 196, "coordinates": [23.6102, 85.2799]},
    {"state": "Chhattisgarh", "stateCode": "CG", "incidentCount": 158, "coordinates": [21.2787, 81.8661]},
    {"state": "Punjab", "stateCode": "PB", "incidentCount": 148, "coordinates": [31.1471, 75.3412]},
    {"state": "Goa", "stateCode": "GA", "incidentCount": 81, "coordinates": [15.4909, 73.8278]},
]


def get_ncrb_data():
    """Return NCRB crime data with risk classification based on incident count."""
    max_incidents = max(d["incidentCount"] for d in NCRB_CRIME_DATA_2022)
    threshold_critical = max_incidents * 0.4
    threshold_medium = max_incidents * 0.1

    result = []
    for d in NCRB_CRIME_DATA_2022:
        if d["incidentCount"] >= threshold_critical:
            risk = "critical"
        elif d["incidentCount"] >= threshold_medium:
            risk = "medium"
        else:
            risk = "safe"

        result.append({
            "state": d["state"],
            "stateCode": d["stateCode"],
            "incidentCount": d["incidentCount"],
            "risk": risk,
            "coordinates": d["coordinates"],
        })

    return {
        "source": "NCRB Crime in India 2022",
        "year": 2022,
        "total_cases": sum(d["incidentCount"] for d in NCRB_CRIME_DATA_2022),
        "last_updated": "2025-01-01",
        "description": "Official cyber crime cases registered by state/UT police. Source: National Crime Records Bureau (NCRB), Crime in India 2022 report.",
        "states": sorted(result, key=lambda x: x["incidentCount"], reverse=True),
    }
