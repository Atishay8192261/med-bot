#!/usr/bin/env python3
import pandas as pd
import psycopg
import json
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

def db():
    return psycopg.connect(
        host=os.getenv("DB_HOST"), port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"), user=os.getenv("DB_USER"), password=os.getenv("DB_PASS")
    )

def main():
    csv_path = Path("data/raw/janaushadhi/Product List_18_8_2025 @ 22_57_28.csv")
    
    if not csv_path.exists():
        print(f"Error: CSV file not found at {csv_path}")
        return
    
    conn = db()
    cur = conn.cursor()
    
    # Read CSV with pandas
    df = pd.read_csv(csv_path)
    print(f"Found {len(df)} rows in Jan Aushadhi CSV")
    print(f"Columns: {list(df.columns)}")
    
    inserted = 0
    skipped = 0
    
    for _, row in df.iterrows():
        try:
            # Extract fields based on actual CSV structure
            generic_name = str(row.get("Generic Name", "")).strip()
            unit_size = str(row.get("Unit Size", "")).strip()
            mrp = row.get("MRP", "")
            drug_code = str(row.get("Drug Code", "")).strip()
            group_name = str(row.get("Group Name", "")).strip()
            
            if not generic_name:
                skipped += 1
                continue
            
            # Parse unit size to extract pack and dosage form
            pack = unit_size
            dosage_form = None
            
            # Try to extract dosage form from unit size
            if "tablet" in unit_size.lower():
                dosage_form = "Tablet"
            elif "capsule" in unit_size.lower():
                dosage_form = "Capsule"
            elif "syrup" in unit_size.lower():
                dosage_form = "Syrup"
            elif "injection" in unit_size.lower():
                dosage_form = "Injection"
            elif "cream" in unit_size.lower():
                dosage_form = "Cream"
            elif "ointment" in unit_size.lower():
                dosage_form = "Ointment"
            
            # Convert MRP to float
            try:
                mrp_inr = float(mrp) if pd.notna(mrp) else None
            except (ValueError, TypeError):
                mrp_inr = None
            
            # Create source_row for tracking
            source_row = {
                "drug_code": drug_code,
                "generic_name": generic_name,
                "unit_size": unit_size,
                "mrp": mrp,
                "group_name": group_name
            }
            
            # Insert into janaushadhi_products
            cur.execute("""
                INSERT INTO janaushadhi_products (generic_name, strength, dosage_form, pack, mrp_inr, source_row)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT DO NOTHING
            """, (generic_name, None, dosage_form, pack, mrp_inr, json.dumps(source_row)))
            
            if cur.rowcount > 0:
                inserted += 1
            else:
                skipped += 1
                
        except Exception as e:
            print(f"Error processing row {generic_name}: {e}")
            skipped += 1
            continue
    
    conn.commit()
    conn.close()
    
    print(f"[DONE] Jan Aushadhi: inserted={inserted}, skipped={skipped}")

if __name__ == "__main__":
    import os
    main()
