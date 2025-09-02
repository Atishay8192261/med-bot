import os, psycopg, json, re
from dotenv import load_dotenv
load_dotenv()

def db():
    return psycopg.connect(host=os.getenv('DB_HOST'), port=os.getenv('DB_PORT'), dbname=os.getenv('DB_NAME'), user=os.getenv('DB_USER'), password=os.getenv('DB_PASS'))

def fetch_unresolved_products():
    sql='''select p.id, p.brand_name, array_agg(ps.salt_name order by ps.salt_pos) salts
            from products_in p join product_salts ps on ps.product_id=p.id
            where p.salt_signature is null group by p.id order by p.id'''
    with db() as conn, conn.cursor() as cur:
        cur.execute(sql)
        return cur.fetchall()

def main():
    rows=fetch_unresolved_products()
    print(f"Unresolved products_in count={len(rows)}")
    for pid, brand, salts in rows:
        norm_salts=[re.sub(r"\s+"," ", s.strip()) for s in salts]
        print(f"PID={pid} brand={brand} salts={norm_salts}")

if __name__=='__main__':
    main()
