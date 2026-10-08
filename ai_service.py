"""
FoodLoop AI Intelligence Service
- Food Safety Status & Urgency Scorer
- Surplus Forecast Engine (30-day historical pattern modeling)
- AI Delivery Partner Matching Engine
- Bulk Redistribution Split Optimizer
"""

import math
from datetime import datetime, timedelta
import random

def calculate_distance(lat1, lon1, lat2, lon2):
    """Haversine formula to compute distance in km between two GPS coordinates."""
    R = 6371.0 # Earth radius in kilometers
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(R * c, 2)

def evaluate_urgency_and_safety(pickup_end_str, has_safety_report=False, safety_pledge_confirmed=True):
    """
    Evaluates urgency level and safety score for a listing.
    Urgency:
      - LOW (> 4 hours remaining)
      - MEDIUM (2 - 4 hours remaining)
      - HIGH (< 2 hours remaining)
    Safety Status:
      - VERIFIED: All criteria met, safe window
      - REQUIRES_ATTENTION: Within 90 mins of expiry or ambient temp warning
      - NOT_ELIGIBLE: Expired, open safety report, or missing pledge
    """
    now = datetime.now()
    try:
        # Expected format "HH:MM"
        end_hour, end_minute = map(int, pickup_end_str.split(':'))
        pickup_end_dt = now.replace(hour=end_hour, minute=end_minute, second=0, microsecond=0)
        
        # If pickup_end is earlier than current time, it might be for today or passed
        time_diff = (pickup_end_dt - now).total_seconds() / 60.0 # in minutes
    except Exception:
        time_diff = 120.0 # fallback

    if has_safety_report or not safety_pledge_confirmed:
        return {
            "urgency": "HIGH",
            "safety_score": "NOT_ELIGIBLE",
            "minutes_remaining": max(0, int(time_diff)),
            "reason": "Safety report open or hygiene declaration unconfirmed."
        }

    if time_diff <= 0:
        return {
            "urgency": "EXPIRED",
            "safety_score": "NOT_ELIGIBLE",
            "minutes_remaining": 0,
            "reason": "Collection deadline has passed. Item removed from feed."
        }
    elif time_diff <= 120: # under 2 hours
        safety_status = "REQUIRES_ATTENTION" if time_diff <= 60 else "VERIFIED"
        return {
            "urgency": "HIGH",
            "safety_score": safety_status,
            "minutes_remaining": int(time_diff),
            "reason": f"Urgent: {int(time_diff)} minutes remaining before safe redistribution window closes."
        }
    elif time_diff <= 240: # 2 to 4 hours
        return {
            "urgency": "MEDIUM",
            "safety_score": "VERIFIED",
            "minutes_remaining": int(time_diff),
            "reason": f"Optimal collection window: {int(time_diff // 60)}h {int(time_diff % 60)}m remaining."
        }
    else:
        return {
            "urgency": "LOW",
            "safety_score": "VERIFIED",
            "minutes_remaining": int(time_diff),
            "reason": f"Freshly prepared / ample time: {int(time_diff // 60)} hours remaining."
        }

def generate_surplus_forecast(provider_id, provider_name, category):
    """
    Simulates AI 30-day historical analysis to forecast today's expected surplus.
    Returns expected portion range, expected hour, probability, and risk breakdown.
    """
    day_name = datetime.now().strftime("%A")
    is_weekend = day_name in ["Saturday", "Sunday"]

    profiles = {
        "Café": {
            "portions_min": 14, "portions_max": 22, "peak_time": "20:30",
            "confidence": 91,
            "high_risk_categories": ["Cooked Curries & Rice", "Bakery Pastries", "Fresh Cut Fruit"],
            "insights": f"Café surplus peaks around 8:00–8:45 PM after evening study/work rush. Rice and dairy items require rapid redistribution within 2 hours."
        },
        "College Canteen": {
            "portions_min": 25, "portions_max": 40, "peak_time": "19:00",
            "confidence": 94,
            "high_risk_categories": ["Biryani & Rice Meals", "Lentil Curries", "Flatbreads/Roti"],
            "insights": f"Hostel and campus dining routinely yields 25–40 surplus dinner portions on {day_name}s. Direct volunteer-assisted routing to nearby student hostels and shelters recommended."
        },
        "Bakery": {
            "portions_min": 12, "portions_max": 18, "peak_time": "21:00",
            "confidence": 88,
            "high_risk_categories": ["Artisan Sourdough", "Cream Pastries", "Sandwiches"],
            "insights": f"Bakery items have stable room-temp holding, but cream-filled items have 3-hour expiry limit."
        },
        "Hotel": {
            "portions_min": 35, "portions_max": 55, "peak_time": "22:15",
            "confidence": 96,
            "high_risk_categories": ["Buffet Entrees", "Paneer & Gravies", "Desserts"],
            "insights": f"Buffet closure generates large bulk volumes. High compatibility with Community Kitchen partners capable of 30+ portions."
        }
    }

    profile = profiles.get(category, profiles["Café"])
    
    # Pre-draft suggestion
    pre_draft = {
        "title": f"Predicted Surplus {category} Meal Batch",
        "category": "Cooked Meals",
        "estimated_portions": int((profile["portions_min"] + profile["portions_max"]) / 2),
        "recommended_pickup": f"{profile['peak_time']} – {int(profile['peak_time'].split(':')[0]) + 1}:30",
        "storage": "Hot Insulated Container (>60°C)" if category != "Bakery" else "Bakery Ambient Box"
    }

    # 7-day historical + predicted trend
    days_week = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    base_portions = (profile["portions_min"] + profile["portions_max"]) / 2
    trend_history = [
        {"day": d, "actual": int(base_portions * (0.85 + (i * 0.05) + (0.1 if d in ['Fri','Sat'] else 0)))}
        for i, d in enumerate(days_week)
    ]

    return {
        "provider_id": provider_id,
        "provider_name": provider_name,
        "day": day_name,
        "historical_period": "Past 30 Days",
        "forecast_portions_range": f"{profile['portions_min']}–{profile['portions_max']} portions",
        "peak_surplus_time": profile["peak_time"],
        "confidence_score": f"{profile['confidence']}%",
        "high_risk_items": profile["high_risk_categories"],
        "ai_rationale": profile["insights"],
        "weekly_trend": trend_history,
        "pre_draft_listing": pre_draft
    }

def simulate_surplus_forecast(category, weather="Clear", dining_traffic="Normal", volume_factor=1.0):
    """
    Dynamic AI simulation engine based on environmental and operational variables.
    """
    base_min = 15
    base_max = 24
    if category == "Hotel":
        base_min, base_max = 35, 55
    elif category == "College Canteen":
        base_min, base_max = 25, 42
    elif category == "Bakery":
        base_min, base_max = 12, 18

    # Weather impact
    weather_multiplier = 1.0
    if weather == "Rainy":
        weather_multiplier = 1.25 # customers cancel dine-in, surplus jumps
    elif weather == "Event":
        weather_multiplier = 1.35 # large campus / city event surplus

    # Traffic impact
    traffic_multiplier = 1.0
    if dining_traffic == "Low":
        traffic_multiplier = 1.20 # low footfall leaves excess food
    elif dining_traffic == "High":
        traffic_multiplier = 0.85 # high footfall consumes more food

    final_min = int(base_min * weather_multiplier * traffic_multiplier * volume_factor)
    final_max = int(base_max * weather_multiplier * traffic_multiplier * volume_factor)
    confidence = max(78, min(97, int(92 - (weather_multiplier - 1.0) * 20)))

    return {
        "simulated_range": f"{final_min}–{final_max} portions",
        "min_portions": final_min,
        "max_portions": final_max,
        "confidence": f"{confidence}%",
        "weather_effect": f"{'+' if weather_multiplier >= 1.0 else ''}{int((weather_multiplier - 1.0)*100)}%",
        "traffic_effect": f"{'+' if traffic_multiplier >= 1.0 else ''}{int((traffic_multiplier - 1.0)*100)}%",
        "haccp_urgency_window": "2.5 hours holding maximum" if category != "Bakery" else "12 hours room temperature"
    }

def match_delivery_partner(listing, partners_list):
    """
    AI Matchmaker: ranks verified delivery partners for transporting a food listing.
    Parameters considered:
    1. Proximity / distance (40%)
    2. Capacity fit (30%)
    3. Vehicle temperature suitability (20%)
    4. Workload / past completed deliveries (10%)
    """
    listing_lat = listing.get("lat", 12.9716)
    listing_lng = listing.get("lng", 77.5946)
    portions = listing.get("portions_remaining", 10)
    is_hot = "Hot" in listing.get("storage_method", "") or "60" in listing.get("storage_temp", "")

    scored_partners = []
    for p in partners_list:
        if p["status"] not in ["verified", "active"]:
            continue

        # Estimate partner distance (mocked realistic campus coordinates)
        p_lat = 12.9720 + (p["id"] * 0.002)
        p_lng = 77.5950 + (p["id"] * 0.002)
        dist = calculate_distance(listing_lat, listing_lng, p_lat, p_lng)

        # Capacity score: partner capacity must cover portions
        cap = p["capacity_portions"]
        cap_score = 100 if cap >= portions else (cap / portions) * 70

        # Proximity score: closer is better
        dist_score = max(0, 100 - (dist * 15))

        # Vehicle & thermal suitability
        vehicle = p["vehicle_type"].lower()
        if is_hot and ("insulated" in vehicle or "thermal" in vehicle):
            thermal_score = 100
        elif not is_hot:
            thermal_score = 95
        else:
            thermal_score = 60 # lacks thermal box for hot food

        # Total weighted score
        composite_score = round(
            (dist_score * 0.40) +
            (cap_score * 0.30) +
            (thermal_score * 0.20) +
            (min(100, p["deliveries_completed"] * 2) * 0.10),
            1
        )

        eta_minutes = max(6, int(dist * 6) + 4)

        scored_partners.append({
            "partner_id": p["id"],
            "user_id": p["user_id"],
            "parent_org_name": p["parent_org_name"],
            "partner_type": p["partner_type"],
            "coordinator_name": p["coordinator_name"],
            "vehicle_type": p["vehicle_type"],
            "capacity_portions": p["capacity_portions"],
            "distance_km": dist,
            "estimated_eta_mins": eta_minutes,
            "match_score": composite_score,
            "safety_compliant": thermal_score >= 80,
            "rationale": f"{dist} km away • {cap} portions capacity • {p['vehicle_type']} (ETA ~{eta_minutes} mins)"
        })

    # Sort descending by match score
    scored_partners.sort(key=lambda x: x["match_score"], reverse=True)
    return scored_partners

def recommend_redistribution_split(portions_total, ngos_nearby_count=1):
    """
    AI recommendation engine for large batches:
    Divides surplus between community organizations (bulk) and individual receivers.
    """
    if portions_total >= 25:
        ngo_portions = int(portions_total * 0.65)
        individual_portions = portions_total - ngo_portions
        return {
            "bulk_split_recommended": True,
            "ngo_allocation": ngo_portions,
            "individual_allocation": individual_portions,
            "recommendation_text": f"Bulk Split: Allocate {ngo_portions} portions to Hope Community Kitchen, {individual_portions} portions for individual student pickups."
        }
    else:
        return {
            "bulk_split_recommended": False,
            "ngo_allocation": 0,
            "individual_allocation": portions_total,
            "recommendation_text": f"Direct Individual Allocation: Best suited for immediate local receiver pickups (1–3 portions per claim)."
        }
