#!/usr/bin/env python3
import csv
import psycopg
import re
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

def db():
    return psycopg.connect(
        host=os.getenv("DB_HOST"), port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"), user=os.getenv("DB_USER"), password=os.getenv("DB_PASS")
    )

def split_composition(composition_str):
    """Split composition by common separators and clean up"""
    if not composition_str:
        return []
    
    # Split by common separators: comma, semicolon, plus sign
    parts = re.split(r'[,;+]', composition_str)
    
    # Clean each part
    cleaned = []
    for part in parts:
        part = part.strip()
        if part:
            # Remove strength info in parentheses, keep just the salt name
            salt_name = re.sub(r'\s*\([^)]*\)', '', part).strip()
            if salt_name:
                cleaned.append(salt_name.title())
    
    return cleaned

def main():
    csv_path = Path("data/raw/india_catalog/indian_medicine_data.csv")
    
    if not csv_path.exists():
        print(f"Error: CSV file not found at {csv_path}")
        return
    
    # First, count total rows for progress tracking
    print("Counting total rows...")
    with csv_path.open(encoding='utf-8') as f:
        total_rows = sum(1 for _ in csv.reader(f)) - 1  # Subtract header
    
    print(f"Total rows to process: {total_rows}")
    
    conn = db()
    cur = conn.cursor()
    
    inserted = 0
    skipped = 0
    processed = 0
    
    # Process in batches for better performance
    batch_size = 1000
    batch_data = []
    
    with csv_path.open(encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            try:
                # Extract fields based on actual CSV structure
                brand_name = row.get('name', '').strip()
                composition = row.get('short_composition1', '') + ' ' + (row.get('short_composition2', '') or '')
                price = row.get('price(₹)', '').strip()
                manufacturer = row.get('manufacturer_name', '').strip()
                pack_size = row.get('pack_size_label', '').strip()
                is_discontinued = row.get('Is_discontinued', 'FALSE').upper() == 'TRUE'
                
                if not brand_name or not composition.strip():
                    skipped += 1
                    processed += 1
                    continue
                
                # Parse composition into salts
                salts = split_composition(composition)
                
                # Convert price to float
                try:
                    mrp_inr = float(price) if price else None
                except (ValueError, TypeError):
                    mrp_inr = None
                
                # Add to batch
                batch_data.append({
                    'brand_name': brand_name,
                    'pack_size': pack_size,
                    'mrp_inr': mrp_inr,
                    'manufacturer': manufacturer,
                    'is_discontinued': is_discontinued,
                    'salts': salts
                })
                
                processed += 1
                
                # Process batch when it reaches batch_size
                if len(batch_data) >= batch_size:
                    inserted += process_batch(cur, batch_data)
                    batch_data = []
                    
                    # Progress update
                    print(f"Progress: {processed}/{total_rows} ({processed/total_rows*100:.1f}%) - Inserted: {inserted}, Skipped: {skipped}")
                
            except Exception as e:
                print(f"Error processing row {brand_name}: {e}")
                skipped += 1
                processed += 1
                continue
    
    # Process remaining batch
    if batch_data:
        inserted += process_batch(cur, batch_data)
    
    conn.commit()
    conn.close()
    
    print(f"[DONE] India Catalog: inserted={inserted}, skipped={skipped}, total_processed={processed}")

def process_batch(cur, batch_data):
    """Process a batch of data for better performance"""
    inserted_count = 0
    
    for item in batch_data:
        try:
            # Insert into products_in
            cur.execute("""
                INSERT INTO products_in (brand_name, strength, dosage_form, pack, mrp_inr, manufacturer, discontinued)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT DO NOTHING
                RETURNING id
            """, (item['brand_name'], None, None, item['pack_size'], item['mrp_inr'], 
                  item['manufacturer'], item['is_discontinued']))
            
            product_id = cur.fetchone()
            if product_id:
                product_id = product_id[0]
                
                # Insert salts into product_salts
                for pos, salt_name in enumerate(item['salts'], 1):
                    cur.execute("""
                        INSERT INTO product_salts (product_id, salt_name, salt_pos)
                        VALUES (%s, %s, %s)
                        ON CONFLICT DO NOTHING
                    """, (product_id, salt_name, pos))
                
                inserted_count += 1
                
        except Exception as e:
            print(f"Error processing batch item {item['brand_name']}: {e}")
            continue
    
    return inserted_count

if __name__ == "__main__":
    import os
    main()
