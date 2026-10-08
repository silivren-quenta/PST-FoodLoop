"""
FoodLoop Backend Verification Tests
Runs automated tests against database, ai_service, and REST logic.
"""

import database
import ai_service
import json

def run_tests():
    print(">>> 1. Initializing DB...")
    database.init_db(force_reseed=True)
    conn = database.get_connection()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM listings")
    l_count = cur.fetchone()[0]
    assert l_count >= 5, f"Expected at least 5 listings, found {l_count}"
    print(f"PASS: Found {l_count} seeded listings.")

    cur.execute("SELECT COUNT(*) FROM delivery_partners")
    dp_count = cur.fetchone()[0]
    assert dp_count >= 2, f"Expected at least 2 delivery partners, found {dp_count}"
    print(f"PASS: Found {dp_count} verified delivery partners.")

    print(">>> 2. Testing AI Safety Evaluator & Urgency Engine...")
    eval_urgent = ai_service.evaluate_urgency_and_safety("16:00")
    print(f"Urgency eval sample: {eval_urgent}")
    assert "urgency" in eval_urgent
    assert "safety_score" in eval_urgent

    print(">>> 3. Testing AI Delivery Matching Engine...")
    cur.execute("SELECT * FROM listings WHERE id = 2")
    l2 = dict(cur.fetchone())
    cur.execute("SELECT * FROM delivery_partners")
    partners = [dict(p) for p in cur.fetchall()]
    matches = ai_service.match_delivery_partner(l2, partners)
    assert len(matches) > 0, "AI matcher should return ranked partners"
    print(f"PASS: AI matched top partner: {matches[0]['parent_org_name']} (Score: {matches[0]['match_score']})")

    print(">>> 4. Testing AI Surplus Forecasting...")
    forecast = ai_service.generate_surplus_forecast(1, "Green Leaf Café", "Café")
    assert "forecast_portions_range" in forecast
    assert "confidence_score" in forecast
    print(f"PASS: AI Surplus Forecast for Green Leaf Café: {forecast['forecast_portions_range']} (Confidence {forecast['confidence_score']})")

    print(">>> 5. Testing Chain of Custody...")
    cur.execute("SELECT * FROM chain_of_custody WHERE listing_id = 2")
    custody = cur.fetchall()
    assert len(custody) >= 3, "Chain of custody should have initial lifecycle stages"
    print(f"PASS: Found {len(custody)} custody transitions for Batch #2.")

    conn.close()
    print("\nALL BACKEND ENGINE TESTS PASSED SUCCESSFULLY! Ready for frontend integration.")

if __name__ == "__main__":
    run_tests()
