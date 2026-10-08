"""
FoodLoop Database Module
SQLite Database with tables for Users, Providers, Delivery Partners,
Listings, Claims, Chain of Custody, Safety Reports, Audit Logs, and Emergency Incidents.
Includes rich realistic seed data.
"""

import sqlite3
import hashlib
import os
import json
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(__file__), "foodloop.db")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def hash_password(password: str, salt: str = "foodloop_secure_salt_2026") -> str:
    return hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        100000
    ).hex()

def init_db(force_reseed=False):
    db_exists = os.path.exists(DB_PATH)
    if force_reseed and db_exists:
        try:
            os.remove(DB_PATH)
            db_exists = False
        except Exception:
            pass

    conn = get_connection()
    cur = conn.cursor()

    # Users Table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL, -- 'receiver', 'provider', 'delivery', 'ngo', 'admin'
        name TEXT NOT NULL,
        phone TEXT NOT NULL, -- kept private
        status TEXT NOT NULL DEFAULT 'active', -- 'pending', 'under_review', 'verified', 'active', 'suspended'
        no_show_count INTEGER DEFAULT 0,
        claim_cooldown_until TEXT DEFAULT NULL,
        created_at TEXT NOT NULL
    )
    """)

    # Providers Table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS providers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        org_name TEXT NOT NULL,
        category TEXT NOT NULL, -- 'Restaurant', 'Bakery', 'Café', 'Hotel', 'Canteen', 'Supermarket'
        address TEXT NOT NULL,
        lat REAL NOT NULL,
        lng REAL NOT NULL,
        verification_status TEXT NOT NULL DEFAULT 'verified', -- 'pending', 'under_review', 'verified', 'suspended'
        rescues_count INTEGER DEFAULT 0,
        safety_reports_count INTEGER DEFAULT 0,
        fssai_license TEXT DEFAULT 'FSSAI-2026-REG-XXXX',
        registered_date TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    """)

    # Delivery Partners Table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS delivery_partners (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        partner_type TEXT NOT NULL, -- 'ngo_volunteer', 'ncc_camp', 'college_group', 'community_kitchen', 'municipal_program'
        parent_org_name TEXT NOT NULL,
        coordinator_name TEXT NOT NULL,
        coordinator_contact TEXT NOT NULL,
        vehicle_type TEXT NOT NULL, -- 'Bicycle with Insulated Bag', 'E-Scooter with Thermal Box', 'Community Van', 'Walking / On-foot'
        capacity_portions INTEGER NOT NULL DEFAULT 20,
        status TEXT NOT NULL DEFAULT 'verified', -- 'pending', 'under_review', 'verified', 'active', 'suspended'
        deliveries_completed INTEGER DEFAULT 0,
        safety_agreement_signed INTEGER DEFAULT 1,
        registered_date TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    """)

    # Food Listings Table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS listings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        provider_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        category TEXT NOT NULL, -- 'Cooked Meals', 'Bakery', 'Fresh Produce', 'Dairy & Packaged', 'Prepared Snacks'
        portions_total INTEGER NOT NULL,
        portions_remaining INTEGER NOT NULL,
        prep_time TEXT NOT NULL,
        expiry_time TEXT NOT NULL,
        pickup_start TEXT NOT NULL,
        pickup_end TEXT NOT NULL,
        is_veg INTEGER NOT NULL DEFAULT 1, -- 1: Veg, 0: Non-Veg
        allergens TEXT NOT NULL, -- JSON array e.g. ["Gluten", "Dairy"]
        ingredients TEXT DEFAULT '',
        storage_method TEXT NOT NULL, -- 'Hot Insulated Box (>60°C)', 'Refrigerated (<4°C)', 'Cool Ambient', 'Bakery Display'
        storage_temp TEXT DEFAULT 'Ambient',
        safety_score TEXT NOT NULL DEFAULT 'VERIFIED', -- 'VERIFIED', 'REQUIRES_ATTENTION', 'NOT_ELIGIBLE'
        safety_pledge_confirmed INTEGER NOT NULL DEFAULT 1,
        status TEXT NOT NULL DEFAULT 'AVAILABLE', -- 'AVAILABLE', 'PAUSED', 'COLLECTED', 'EXPIRED', 'FLAGGED_UNSAFE'
        photo_url TEXT DEFAULT '',
        max_claims_per_user INTEGER DEFAULT 2,
        created_at TEXT NOT NULL,
        FOREIGN KEY (provider_id) REFERENCES providers(id)
    )
    """)

    # Claims Table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS claims (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        claim_code TEXT UNIQUE NOT NULL, -- e.g. 'LOOP-8492-X'
        listing_id INTEGER NOT NULL,
        receiver_id INTEGER NOT NULL,
        portion_count INTEGER NOT NULL,
        status TEXT NOT NULL DEFAULT 'RESERVED', -- 'RESERVED', 'IN_TRANSIT', 'COLLECTED', 'EXPIRED', 'CANCELLED'
        allergen_acknowledged INTEGER NOT NULL DEFAULT 1,
        qr_hash TEXT NOT NULL,
        delivery_required INTEGER NOT NULL DEFAULT 0,
        delivery_partner_id INTEGER DEFAULT NULL,
        created_at TEXT NOT NULL,
        pickup_deadline TEXT NOT NULL,
        completed_at TEXT DEFAULT NULL,
        FOREIGN KEY (listing_id) REFERENCES listings(id),
        FOREIGN KEY (receiver_id) REFERENCES users(id),
        FOREIGN KEY (delivery_partner_id) REFERENCES delivery_partners(id)
    )
    """)

    # Digital Chain of Custody Table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS chain_of_custody (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        batch_id TEXT NOT NULL,
        listing_id INTEGER NOT NULL,
        claim_id INTEGER DEFAULT NULL,
        stage TEXT NOT NULL, -- 'PREPARED', 'LISTED', 'VOLUNTEER_ASSIGNED', 'PICKED_UP', 'IN_TRANSIT', 'RECEIVED', 'DISTRIBUTED'
        actor_role TEXT NOT NULL, -- 'PROVIDER', 'VOLUNTEER', 'RECIPIENT', 'NGO'
        actor_name TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        temp_checked TEXT DEFAULT 'Compliant',
        qr_verified INTEGER NOT NULL DEFAULT 1,
        notes TEXT DEFAULT '',
        FOREIGN KEY (listing_id) REFERENCES listings(id)
    )
    """)

    # Food Safety Reports Table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS safety_reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        listing_id INTEGER NOT NULL,
        provider_id INTEGER NOT NULL,
        reporter_id INTEGER NOT NULL,
        issue_type TEXT NOT NULL, -- 'SPOILED', 'BAD_SMELL', 'INCORRECT_DESC', 'INCORRECT_PREP_TIME', 'UNSAFE_PACKAGING', 'IMPROPER_STORAGE', 'ALLERGEN_ISSUE', 'OTHER'
        details TEXT NOT NULL,
        immediate_action_taken TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'OPEN', -- 'OPEN', 'INVESTIGATING', 'RESOLVED', 'PROVIDER_WARNED', 'SUSPENDED'
        created_at TEXT NOT NULL,
        FOREIGN KEY (listing_id) REFERENCES listings(id),
        FOREIGN KEY (provider_id) REFERENCES providers(id),
        FOREIGN KEY (reporter_id) REFERENCES users(id)
    )
    """)

    # Audit Logs Table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        actor_id INTEGER DEFAULT NULL,
        actor_role TEXT NOT NULL,
        action TEXT NOT NULL,
        target_type TEXT NOT NULL,
        target_id TEXT NOT NULL,
        details TEXT NOT NULL,
        timestamp TEXT NOT NULL
    )
    """)

    # Emergency Incidents Table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS emergency_incidents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        delivery_partner_id INTEGER NOT NULL,
        claim_id INTEGER DEFAULT NULL,
        emergency_type TEXT NOT NULL, -- 'ACCIDENT', 'FOOD_SPOILED', 'MEDICAL', 'UNABLE_TO_DELIVER', 'VEHICLE_BREAKDOWN', 'UNSAFE_LOCATION'
        coordinator_notified INTEGER DEFAULT 1,
        status TEXT NOT NULL DEFAULT 'DISPATCHED_HELP',
        details TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        FOREIGN KEY (delivery_partner_id) REFERENCES delivery_partners(id)
    )
    """)

    # NGO Profiles Table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS ngo_profiles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        org_name TEXT NOT NULL,
        registration_num TEXT NOT NULL,
        coordinator_name TEXT NOT NULL,
        target_beneficiaries INTEGER NOT NULL DEFAULT 50,
        preferred_categories TEXT NOT NULL, -- JSON array
        radius_km REAL NOT NULL DEFAULT 5.0,
        status TEXT NOT NULL DEFAULT 'verified',
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    """)

    conn.commit()

    # Seed if table is freshly created
    cur.execute("SELECT COUNT(*) FROM users")
    count = cur.fetchone()[0]
    if count == 0:
        seed_data(conn)

    conn.close()

def seed_data(conn):
    cur = conn.cursor()
    now = datetime.now()

    # 1. Seed Users (with hashed passwords)
    users = [
        # Admin
        ("admin@foodloop.org", hash_password("admin123"), "admin", "FoodLoop Central Trust & Safety Admin", "+91 98765 00001", "verified", "2026-01-10 10:00:00"),
        # Receiver
        ("ananya.student@univ.edu", hash_password("user123"), "receiver", "Ananya Sharma (Student)", "+91 98765 11111", "verified", "2026-02-01 12:00:00"),
        # Provider 1
        ("manager@greenleaf.cafe", hash_password("provider123"), "provider", "Chef Vikram Rao (Green Leaf Café)", "+91 98765 22221", "verified", "2026-01-15 09:00:00"),
        # Provider 2
        ("director@campuskitchen.edu", hash_password("provider123"), "provider", "Campus Dining Services", "+91 98765 22222", "verified", "2026-01-18 10:00:00"),
        # Provider 3
        ("headchef@sunrisebakery.com", hash_password("provider123"), "provider", "Master Baker Sarah", "+91 98765 22223", "verified", "2026-02-05 08:00:00"),
        # Provider 4
        ("executivechef@royalpalms.com", hash_password("provider123"), "provider", "Chef Antoine (Royal Palms Buffet)", "+91 98765 22224", "verified", "2026-01-20 14:00:00"),
        # Delivery Partner 1 (NCC / Student Volunteer)
        ("ncc.cadet.lead@univ.edu", hash_password("volunteer123"), "delivery", "Senior Under Officer Rohan (NCC 3rd Battalion)", "+91 98765 33331", "verified", "2026-02-10 11:00:00"),
        # Delivery Partner 2 (NGO Volunteer Team)
        ("logistics@cityfoodrelief.ngo", hash_password("volunteer123"), "delivery", "City Food Relief Express Van (Authorized Coordinator: Deepa M)", "+91 98765 33332", "verified", "2026-01-25 15:00:00"),
        # NGO Partner
        ("relief@hopekids.ngo", hash_password("ngo123"), "ngo", "Hope Children's Shelter & Community Kitchen", "+91 98765 44441", "verified", "2026-01-12 11:30:00"),
    ]

    for u in users:
        cur.execute("""
        INSERT INTO users (email, password_hash, role, name, phone, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, u)

    # 2. Seed Providers
    providers = [
        (3, "Green Leaf Café & Bistro", "Café", "14 College Road, North Campus", 12.9716, 77.5946, "verified", 248, 0, "FSSAI-112233445566", "2026-01-15"),
        (4, "Campus Central Dining Kitchen", "College Canteen", "Hostel Block C, University Campus", 12.9750, 77.5980, "verified", 412, 0, "FSSAI-223344556677", "2026-01-18"),
        (5, "Sunrise Artisanal Organic Bakery", "Bakery", "88 Heritage Boulevard", 12.9680, 77.6010, "verified", 189, 0, "FSSAI-334455667788", "2026-02-05"),
        (6, "Royal Palms Grand Hotel Buffet", "Hotel", "5 Star Plaza, Residency Road", 12.9650, 77.5890, "verified", 330, 0, "FSSAI-445566778899", "2026-01-20"),
    ]

    for p in providers:
        cur.execute("""
        INSERT INTO providers (user_id, org_name, category, address, lat, lng, verification_status, rescues_count, safety_reports_count, fssai_license, registered_date)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, p)

    # 3. Seed Delivery Partners
    partners = [
        (7, "ncc_camp", "NCC 3rd Battalion University Wing", "Capt. S. Sengupta (Associate Officer)", "+91 98765 88881", "Bicycle with Insulated Bag", 25, "active", 42, 1, "2026-02-10"),
        (8, "ngo_volunteer", "City Food Relief Community Network", "Deepa Mehra (Logistics Officer)", "+91 98765 88882", "E-Scooter with Thermal Box", 40, "active", 115, 1, "2026-01-25"),
    ]

    for dp in partners:
        cur.execute("""
        INSERT INTO delivery_partners (user_id, partner_type, parent_org_name, coordinator_name, coordinator_contact, vehicle_type, capacity_portions, status, deliveries_completed, safety_agreement_signed, registered_date)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, dp)

    # 4. Seed NGO Profile
    cur.execute("""
    INSERT INTO ngo_profiles (user_id, org_name, registration_num, coordinator_name, target_beneficiaries, preferred_categories, radius_km, status)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (9, "Hope Children's Shelter & Community Kitchen", "NGO-REG-2024-KA-8891", "Sister Teresa D'Souza", 85, json.dumps(["Cooked Meals", "Bakery", "Fresh Produce"]), 6.0, "verified"))

    # 5. Seed Food Listings with safety details and relative times
    # Note: Using dynamic times relative to now for realism
    t_minus_1h = (now - timedelta(hours=1)).strftime("%H:%M")
    t_plus_1h = (now + timedelta(hours=1, minutes=15)).strftime("%H:%M")
    t_plus_2h = (now + timedelta(hours=2)).strftime("%H:%M")
    t_plus_3h = (now + timedelta(hours=3, minutes=30)).strftime("%H:%M")
    t_plus_5h = (now + timedelta(hours=5)).strftime("%H:%M")

    listings = [
        (
            1, # Green Leaf Café
            "Surplus Vegetable Pulao & Slow-Cooked Dal Tadka",
            "Cooked Meals",
            18, 18,
            f"Today at {t_minus_1h}",
            f"Within 2.5 hours",
            t_minus_1h,
            t_plus_2h,
            1, # Veg
            json.dumps(["Gluten", "Dairy"]),
            "Basmati rice, carrots, green peas, ghee, yellow lentils, turmeric, cumin, ginger.",
            "Hot Insulated Box (>60°C)",
            "63°C",
            "VERIFIED",
            1,
            "AVAILABLE",
            "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?auto=format&fit=crop&w=600&q=80",
            3,
            now.strftime("%Y-%m-%d %H:%M:%S")
        ),
        (
            2, # Campus Central Dining
            "Fresh Chicken Biryani + Cucumber Mint Raita [Urgent Rescue]",
            "Cooked Meals",
            32, 28,
            f"Today at {t_minus_1h}",
            f"Within 1.5 hours",
            t_minus_1h,
            t_plus_1h,
            0, # Non-Veg
            json.dumps(["Dairy", "Spicy"]),
            "Chicken, basmati rice, saffron, onions, curd, whole spices, mint, coriander.",
            "Hot Insulated Box (>60°C)",
            "65°C",
            "REQUIRES_ATTENTION", # Approaching deadline
            1,
            "AVAILABLE",
            "https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?auto=format&fit=crop&w=600&q=80",
            4,
            now.strftime("%Y-%m-%d %H:%M:%S")
        ),
        (
            3, # Sunrise Artisanal Bakery
            "Artisan Sourdough Loaves & Croissant Assortment",
            "Bakery",
            14, 14,
            "Baked this afternoon",
            "Best within 24 hours",
            "18:00",
            t_plus_5h,
            1, # Veg
            json.dumps(["Gluten", "Dairy", "Eggs"]),
            "Organic whole wheat flour, natural sourdough levain, butter, sea salt, yeast.",
            "Bakery Display (Room Temp)",
            "22°C (Dry)",
            "VERIFIED",
            1,
            "AVAILABLE",
            "https://images.unsplash.com/photo-1509440159596-0249088772ff?auto=format&fit=crop&w=600&q=80",
            2,
            now.strftime("%Y-%m-%d %H:%M:%S")
        ),
        (
            4, # Royal Palms Grand Hotel Buffet
            "Paneer Butter Masala, Roti & Steamed Rice Batch",
            "Cooked Meals",
            45, 45,
            f"Freshly packed at {t_minus_1h}",
            f"Within 3 hours",
            "19:00",
            t_plus_3h,
            1, # Veg
            json.dumps(["Dairy", "Gluten"]),
            "Fresh cottage cheese, tomatoes, cashews, cream, whole wheat flatbreads.",
            "Hot Insulated Container (>60°C)",
            "64°C",
            "VERIFIED",
            1,
            "AVAILABLE",
            "https://images.unsplash.com/photo-1631452180519-c014fe946bc7?auto=format&fit=crop&w=600&q=80",
            4,
            now.strftime("%Y-%m-%d %H:%M:%S")
        ),
        (
            1, # Green Leaf Café (2nd listing)
            "Fresh Fruit Salad with Honey & Mint Leaves",
            "Fresh Produce",
            12, 12,
            "Prepared 45 mins ago",
            "Best within 4 hours",
            "17:30",
            t_plus_3h,
            1, # Veg
            json.dumps([]), # Allergen-free declaration
            "Watermelon, pineapple, grapes, papaya, raw organic honey, fresh mint.",
            "Refrigerated (<4°C)",
            "3.8°C",
            "VERIFIED",
            1,
            "AVAILABLE",
            "https://images.unsplash.com/photo-1519996529931-28324d5a630e?auto=format&fit=crop&w=600&q=80",
            2,
            now.strftime("%Y-%m-%d %H:%M:%S")
        )
    ]

    for l in listings:
        cur.execute("""
        INSERT INTO listings (
            provider_id, title, category, portions_total, portions_remaining,
            prep_time, expiry_time, pickup_start, pickup_end, is_veg,
            allergens, ingredients, storage_method, storage_temp, safety_score,
            safety_pledge_confirmed, status, photo_url, max_claims_per_user, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, l)

    # 6. Seed an Initial Claim & Digital Chain of Custody record
    claim_code = "LOOP-8492-X"
    cur.execute("""
    INSERT INTO claims (
        claim_code, listing_id, receiver_id, portion_count, status,
        allergen_acknowledged, qr_hash, delivery_required, delivery_partner_id,
        created_at, pickup_deadline
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        claim_code, 2, 2, 4, "RESERVED",
        1, "FL-BATCH-L2-C8492-SECURE-SHA256", 1, 1,
        now.strftime("%Y-%m-%d %H:%M:%S"), (now + timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
    ))
    claim_id = cur.lastrowid

    # 7. Seed Digital Chain of Custody for Listing #2
    batch_id = "BATCH-2026-CAMPUS-02"
    custody_entries = [
        (batch_id, 2, claim_id, "PREPARED", "PROVIDER", "Campus Dining Services", (now - timedelta(minutes=50)).strftime("%Y-%m-%d %H:%M:%S"), "65°C - Compliant", 1, "Kitchen quality verified by Head Chef"),
        (batch_id, 2, claim_id, "LISTED", "PROVIDER", "Campus Dining Services", (now - timedelta(minutes=45)).strftime("%Y-%m-%d %H:%M:%S"), "65°C - Insulated", 1, "Food listed for ₹0 redistribution with 5-point safety pledge confirmed"),
        (batch_id, 2, claim_id, "VOLUNTEER_ASSIGNED", "VOLUNTEER", "SUO Rohan (NCC 3rd Battalion)", (now - timedelta(minutes=20)).strftime("%Y-%m-%d %H:%M:%S"), "Compliant Thermal Bag Ready", 1, "Transport conditions accepted. Target delivery: Student Hostels Block C")
    ]
    for c in custody_entries:
        cur.execute("""
        INSERT INTO chain_of_custody (batch_id, listing_id, claim_id, stage, actor_role, actor_name, timestamp, temp_checked, qr_verified, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, c)

    # 8. Seed Audit Log entries
    audit_entries = [
        (1, "ADMIN", "SYSTEM_INITIALIZATION", "SYSTEM", "0", "FoodLoop Trust & Safety Infrastructure Activated", now.strftime("%Y-%m-%d %H:%M:%S")),
        (3, "PROVIDER", "CREATE_LISTING", "LISTING", "1", "Created listing with 5-point safety confirmation: Surplus Vegetable Pulao", now.strftime("%Y-%m-%d %H:%M:%S")),
        (4, "PROVIDER", "CREATE_LISTING", "LISTING", "2", "Created listing with 5-point safety confirmation: Fresh Chicken Biryani", now.strftime("%Y-%m-%d %H:%M:%S")),
        (2, "RECEIVER", "CLAIM_RESERVATION", "CLAIM", claim_code, "Receiver Ananya Sharma reserved 4 portions with allergen acknowledgment", now.strftime("%Y-%m-%d %H:%M:%S")),
        (7, "VOLUNTEER", "ASSIGNMENT_ACCEPTED", "DELIVERY", "1", "NCC Cadet Volunteer assigned to transport Batch #2", now.strftime("%Y-%m-%d %H:%M:%S"))
    ]
    for a in audit_entries:
        cur.execute("""
        INSERT INTO audit_logs (actor_id, actor_role, action, target_type, target_id, details, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, a)

    conn.commit()
    print("FoodLoop Database initialized & seeded successfully.")

if __name__ == "__main__":
    init_db(force_reseed=True)
