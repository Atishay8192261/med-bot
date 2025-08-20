#!/usr/bin/env python3
import os, re, psycopg, time
from dotenv import load_dotenv
from app.rxnorm_client import rxnorm_lookup
from app.normalization import norm_term

load_dotenv()

def db():
    return psycopg.connect(
        host=os.getenv("DB_HOST"), port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"), user=os.getenv("DB_USER"), password=os.getenv("DB_PASS")
    )

def split_salts(generic_name: str):
    """Split generic name into normalized salts"""
    if not generic_name:
        return []
    parts = re.split(r"[+,\|]", generic_name)
    out = [norm_term(x) for x in parts if x and norm_term(x)]
    return [re.sub(r"\s+", " ", x).title() for x in out]

def signature_for(generic_name: str):
    """Generate salt signature for a generic name with timeout"""
    try:
        salts = split_salts(generic_name)
        rxcui_set = set()
        
        for s in salts:
            try:
                rxcuis, _ = rxnorm_lookup(s)
                if rxcuis:
                    rxcui_set.add(rxcuis[0])
                time.sleep(0.1)  # Rate limiting for RxNorm API
            except Exception as e:
                print(f"  RxNorm lookup failed for '{s}': {e}")
                continue
                
        if not rxcui_set:
            return None
        return "-".join(sorted(rxcui_set))
        
    except Exception as e:
        print(f"  Signature generation failed for '{generic_name}': {e}")
        return None

def update_janaushadhi_batch():
    """Update Jan Aushadhi signatures in batches with progress"""
    print("Processing Jan Aushadhi signatures...")
    
    conn = db()
    cur = conn.cursor()
    
    # Get total count
    cur.execute("SELECT COUNT(*) FROM janaushadhi_products WHERE salt_signature IS NULL")
    total_count = cur.fetchone()[0]
    
    if total_count == 0:
        print("✅ All Jan Aushadhi products already have signatures!")
        conn.close()
        return
    
    print(f"Found {total_count} Jan Aushadhi products needing signatures")
    
    # Process in batches
    batch_size = 50
    processed = 0
    successful = 0
    
    while processed < total_count:
        # Get batch
        cur.execute("""
            SELECT id, generic_name 
            FROM janaushadhi_products 
            WHERE salt_signature IS NULL 
            ORDER BY id 
            LIMIT %s
        """, (batch_size,))
        
        batch = cur.fetchall()
        if not batch:
            break
            
        print(f"\nProcessing batch {processed//batch_size + 1}: {len(batch)} products")
        
        for i, (product_id, generic_name) in enumerate(batch):
            print(f"  [{i+1}/{len(batch)}] Processing: {generic_name[:50]}...")
            
            sig = signature_for(generic_name)
            
            if sig:
                cur.execute("""
                    UPDATE janaushadhi_products 
                    SET salt_signature=%s, updated_at=NOW() 
                    WHERE id=%s
                """, (sig, product_id))
                successful += 1
                print(f"    ✅ Signature: {sig}")
            else:
                print(f"    ❌ No signature found")
            
            processed += 1
            
            # Progress update every 10 products
            if processed % 10 == 0:
                print(f"  Progress: {processed}/{total_count} ({processed/total_count*100:.1f}%) - Success: {successful}")
        
        # Commit batch
        conn.commit()
        print(f"  Batch completed. Total: {processed}/{total_count}, Success: {successful}")
        
        # Small delay between batches
        time.sleep(1)
    
    conn.close()
    print(f"\n✅ Jan Aushadhi completed: {successful}/{total_count} signatures mapped")

def update_nppa_batch():
    """Update NPPA signatures in batches with progress"""
    print("\nProcessing NPPA signatures...")
    
    conn = db()
    cur = conn.cursor()
    
    # Get total count
    cur.execute("SELECT COUNT(*) FROM nppa_ceiling_prices WHERE salt_signature IS NULL")
    total_count = cur.fetchone()[0]
    
    if total_count == 0:
        print("✅ All NPPA products already have signatures!")
        conn.close()
        return
    
    print(f"Found {total_count} NPPA products needing signatures")
    
    # Process in batches
    batch_size = 50
    processed = 0
    successful = 0
    
    while processed < total_count:
        # Get batch
        cur.execute("""
            SELECT id, generic_name 
            FROM nppa_ceiling_prices 
            WHERE salt_signature IS NULL 
            ORDER BY id 
            LIMIT %s
        """, (batch_size,))
        
        batch = cur.fetchall()
        if not batch:
            break
            
        print(f"\nProcessing batch {processed//batch_size + 1}: {len(batch)} products")
        
        for i, (product_id, generic_name) in enumerate(batch):
            print(f"  [{i+1}/{len(batch)}] Processing: {generic_name[:50]}...")
            
            sig = signature_for(generic_name)
            
            if sig:
                cur.execute("""
                    UPDATE nppa_ceiling_prices 
                    SET salt_signature=%s, updated_at=NOW() 
                    WHERE id=%s
                """, (sig, product_id))
                successful += 1
                print(f"    ✅ Signature: {sig}")
            else:
                print(f"    ❌ No signature found")
            
            processed += 1
            
            # Progress update every 10 products
            if processed % 10 == 0:
                print(f"  Progress: {processed}/{total_count} ({processed/total_count*100:.1f}%) - Success: {successful}")
        
        # Commit batch
        conn.commit()
        print(f"  Batch completed. Total: {processed}/{total_count}, Success: {successful}")
        
        # Small delay between batches
        time.sleep(1)
    
    conn.close()
    print(f"\n✅ NPPA completed: {successful}/{total_count} signatures mapped")

def main():
    print("🚀 Starting optimized signature mapping for Chunk 4.9 completion...")
    print("=" * 60)
    
    try:
        # Process Jan Aushadhi first
        update_janaushadhi_batch()
        
        # Process NPPA second
        update_nppa_batch()
        
        print("\n" + "=" * 60)
        print("🎉 Chunk 4.9 signature mapping completed!")
        
        # Final status check
        conn = db()
        cur = conn.cursor()
        
        cur.execute("SELECT COUNT(*) FILTER (WHERE salt_signature IS NOT NULL) FROM janaushadhi_products")
        jana_count = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FILTER (WHERE salt_signature IS NOT NULL) FROM nppa_ceiling_prices")
        nppa_count = cur.fetchone()[0]
        
        print(f"📊 Final Status:")
        print(f"   Jan Aushadhi: {jana_count} signatures mapped")
        print(f"   NPPA: {nppa_count} signatures mapped")
        
        conn.close()
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Process interrupted by user")
        print("Partial progress has been saved. You can run the script again to continue.")
    except Exception as e:
        print(f"\n\n❌ Error occurred: {e}")
        print("Check the logs and try again.")

if __name__ == "__main__":
    main()
