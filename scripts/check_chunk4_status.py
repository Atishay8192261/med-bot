#!/usr/bin/env python3
import psycopg
from dotenv import load_dotenv

load_dotenv()

def db():
    return psycopg.connect(
        host=os.getenv("DB_HOST"), port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"), user=os.getenv("DB_USER"), password=os.getenv("DB_PASS")
    )

def main():
    print("🔍 Chunk 4.9 Completion Status Check")
    print("=" * 50)
    
    conn = db()
    cur = conn.cursor()
    
    # Check products_in
    cur.execute("SELECT COUNT(*) FROM products_in")
    total_products = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM products_in WHERE salt_signature IS NOT NULL")
    products_with_sig = cur.fetchone()[0]
    
    print(f"📦 India Catalog Products:")
    print(f"   Total: {total_products:,}")
    print(f"   With Signatures: {products_with_sig:,}")
    print(f"   Signature Rate: {products_with_sig/total_products*100:.1f}%")
    
    # Check Jan Aushadhi
    cur.execute("SELECT COUNT(*) FROM janaushadhi_products")
    total_jana = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM janaushadhi_products WHERE salt_signature IS NOT NULL")
    jana_with_sig = cur.fetchone()[0]
    
    print(f"\n💊 Jan Aushadhi Generics:")
    print(f"   Total: {total_jana:,}")
    print(f"   With Signatures: {jana_with_sig:,}")
    print(f"   Signature Rate: {jana_with_sig/total_jana*100:.1f}%")
    
    # Check NPPA
    cur.execute("SELECT COUNT(*) FROM nppa_ceiling_prices")
    total_nppa = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM nppa_ceiling_prices WHERE salt_signature IS NOT NULL")
    nppa_with_sig = cur.fetchone()[0]
    
    print(f"\n💰 NPPA Ceiling Prices:")
    print(f"   Total: {total_nppa:,}")
    print(f"   With Signatures: {nppa_with_sig:,}")
    print(f"   Signature Rate: {nppa_with_sig/total_nppa*100:.1f}%")
    
    # Overall status
    total_items = total_products + total_jana + total_nppa
    total_with_sig = products_with_sig + jana_with_sig + nppa_with_sig
    
    print(f"\n📊 OVERALL STATUS:")
    print(f"   Total Items: {total_items:,}")
    print(f"   With Signatures: {total_with_sig:,}")
    print(f"   Overall Signature Rate: {total_with_sig/total_items*100:.1f}%")
    
    # What needs completion
    jana_needed = total_jana - jana_with_sig
    nppa_needed = total_nppa - nppa_with_sig
    
    if jana_needed > 0 or nppa_needed > 0:
        print(f"\n⚠️  REMAINING WORK FOR CHUNK 4.9:")
        if jana_needed > 0:
            print(f"   Jan Aushadhi: {jana_needed:,} signatures needed")
        if nppa_needed > 0:
            print(f"   NPPA: {nppa_needed:,} signatures needed")
        print(f"   Total: {jana_needed + nppa_needed:,} signatures to complete")
    else:
        print(f"\n✅ CHUNK 4.9 IS COMPLETE!")
    
    conn.close()

if __name__ == "__main__":
    import os
    main()
