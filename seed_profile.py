import sqlite3
from datetime import datetime, timezone

DB_NAME = "truebuild_advanced.db"

company_payload = {
    "legal_name": "Sumthin3lse Global Solutions LLC",
    "dba": "Sumthin3lse Global",
    "entity_type": "LLC",
    "state_of_inc": "Florida",
    "date_established": "2025-12-01",
    "ein": "XX-XXXXXXX",  # Insert your 9-digit EIN
    "duns_number": "Pending D&B Generation",
    "industry_naics": "541611",  # Management Consulting Services
    "primary_phone": "321-555-0199",
    "primary_email": "admin@sumthin3lse.com",
    "website": "https://sumthin3lse.com",
    "physical_address": "2055 Warrior Ave SE",
    "city": "Palm Bay",
    "state": "FL",
    "zip_code": "32909",
    "officer_name": "Darwin Nicholas Hayle",
    "officer_title": "Managing Member",
    "officer_ownership_pct": 100.0,
    "bank_name": "Chase Commercial Banking",
    "bank_account_type": "Business Checking",
    "compliance_score": 100,
    "current_unlocked_tier": 1,
    "created_at": datetime.now(timezone.utc).isoformat(),
}

with sqlite3.connect(DB_NAME) as conn:
    cursor = conn.cursor()
    # Check if profile 1 exists
    cursor.execute("SELECT id FROM company_dossier WHERE id = 1;")
    existing = cursor.fetchone()

    if existing:
        cursor.execute(
            """
            UPDATE company_dossier SET 
                physical_address = ?, 
                city = ?, 
                state = ?, 
                zip_code = ? 
            WHERE id = 1;
            """,
            (
                company_payload["physical_address"],
                company_payload["city"],
                company_payload["state"],
                company_payload["zip_code"],
            ),
        )
        print("Updated company #1 address to 2055 Warrior Ave SE, Palm Bay, FL 32909.")
    else:
        cursor.execute(
            """
            INSERT INTO company_dossier (
                legal_name, dba, entity_type, state_of_inc, date_established, ein, duns_number, 
                industry_naics, primary_phone, primary_email, website, physical_address, city, state, 
                zip_code, officer_name, officer_title, officer_ownership_pct, bank_name, bank_account_type, 
                compliance_score, current_unlocked_tier, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            (
                company_payload["legal_name"],
                company_payload["dba"],
                company_payload["entity_type"],
                company_payload["state_of_inc"],
                company_payload["date_established"],
                company_payload["ein"],
                company_payload["duns_number"],
                company_payload["industry_naics"],
                company_payload["primary_phone"],
                company_payload["primary_email"],
                company_payload["website"],
                company_payload["physical_address"],
                company_payload["city"],
                company_payload["state"],
                company_payload["zip_code"],
                company_payload["officer_name"],
                company_payload["officer_title"],
                company_payload["officer_ownership_pct"],
                company_payload["bank_name"],
                company_payload["bank_account_type"],
                company_payload["compliance_score"],
                company_payload["current_unlocked_tier"],
                company_payload["created_at"],
            ),
        )
        print("Inserted new profile for Sumthin3lse Global Solutions LLC at 2055 Warrior Ave SE.")
    conn.commit()
