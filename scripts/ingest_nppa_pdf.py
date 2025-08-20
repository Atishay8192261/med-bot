#!/usr/bin/env python3
import psycopg
import json
import re
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

def db():
    return psycopg.connect(
        host=os.getenv("DB_HOST"), port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"), user=os.getenv("DB_USER"), password=os.getenv("DB_PASS")
    )

def main():
    pdf_path = Path("data/raw/nppa/NPPA_UPDATED_PRICE-LIST_AS_ON_07022025.pdf")
    
    if not pdf_path.exists():
        print(f"Error: PDF file not found at {pdf_path}")
        return
    
    try:
        import pdfplumber
    except ImportError:
        print("Error: pdfplumber not installed. Install with: pip install pdfplumber")
        return
    
    conn = db()
    cur = conn.cursor()
    
    inserted = 0
    skipped = 0
    
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages):
            print(f"Processing page {page_num + 1}")
            
            # Extract tables from the page
            tables = page.extract_tables()
            
            for table in tables:
                for row in table:
                    if not row or len(row) < 3:
                        continue
                    
                    # Skip header rows and empty rows
                    if any(header in str(cell).lower() for cell in row[:3] 
                           for header in ['medicines', 'dosage', 'strength', 'unit', 'ceiling', 'price']):
                        continue
                    
                    # Try to parse the row
                    try:
                        # Clean and extract fields
                        medicines = str(row[0]).strip() if len(row) > 0 else ""
                        dosage_strength = str(row[1]).strip() if len(row) > 1 else ""
                        unit = str(row[2]).strip() if len(row) > 2 else ""
                        ceiling_price = str(row[3]).strip() if len(row) > 3 else ""
                        so_no_date = str(row[4]).strip() if len(row) > 4 else ""
                        
                        # Skip if no medicine name
                        if not medicines or medicines.lower() in ['nan', 'none', '']:
                            continue
                        
                        # Try to extract price
                        try:
                            # Look for numeric values in the price field
                            price_match = re.search(r'(\d+(?:\.\d{2})?)', ceiling_price)
                            if price_match:
                                price = float(price_match.group(1))
                            else:
                                price = None
                        except (ValueError, TypeError):
                            price = None
                        
                        # Create generic_name by combining medicines and dosage_strength
                        generic_name = f"{medicines} {dosage_strength}".strip()
                        
                        # Create source_row for tracking
                        source_row = {
                            "medicines": medicines,
                            "dosage_strength": dosage_strength,
                            "unit": unit,
                            "ceiling_price": ceiling_price,
                            "so_no_date": so_no_date,
                            "page": page_num + 1
                        }
                        
                        # Insert into nppa_ceiling_prices
                        cur.execute("""
                            INSERT INTO nppa_ceiling_prices (generic_name, strength, pack, ceiling_price, source_row)
                            VALUES (%s, %s, %s, %s, %s)
                            ON CONFLICT DO NOTHING
                        """, (generic_name, dosage_strength, unit, price, json.dumps(source_row)))
                        
                        if cur.rowcount > 0:
                            inserted += 1
                        else:
                            skipped += 1
                            
                    except Exception as e:
                        print(f"Error processing row {medicines}: {e}")
                        skipped += 1
                        continue
    
    conn.commit()
    conn.close()
    
    print(f"[DONE] NPPA PDF: inserted={inserted}, skipped={skipped}")

if __name__ == "__main__":
    import os
    main()
