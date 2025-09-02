import os, psycopg, argparse
from dotenv import load_dotenv
from app.normalization import norm_term, alias_if_needed
from app.rxnorm_client import rxnorm_lookup

load_dotenv()

def db():
    return psycopg.connect(host=os.getenv('DB_HOST'), port=os.getenv('DB_PORT'), dbname=os.getenv('DB_NAME'), user=os.getenv('DB_USER'), password=os.getenv('DB_PASS'))

def gather_unresolved(limit=None):
    sql='''select distinct ps.salt_name from products_in p join product_salts ps on ps.product_id=p.id where p.salt_signature is null'''
    with db() as conn, conn.cursor() as cur:
        cur.execute(sql)
        salts=[r[0] for r in cur.fetchall()]
    return salts[:limit] if limit else salts

def warm(salts):
    done=0; hits=0; new=0
    for s in salts:
        t=norm_term(s)
        alias=alias_if_needed(t) or t
        rxcuis,_=rxnorm_lookup(alias)
        if rxcuis:
            hits+=1
        done+=1
        if done % 20 == 0:
            print(f"[WARM] {done}/{len(salts)} hits={hits}")
    print(f"Completed warm-up: salts={len(salts)} hits={hits}")

if __name__=='__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('--limit', type=int, default=None)
    args=ap.parse_args()
    salts=gather_unresolved(args.limit)
    print(f"Warming cache for {len(salts)} unresolved salts")
    warm(salts)
