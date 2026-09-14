import sqlite3
import os

dbs = [
    r"clinical.db",
    r"backend\clinical.db"
]

for db_rel in dbs:
    abs_path = os.path.abspath(db_rel)
    print(f"=== DATABASE: {abs_path} ===")
    if not os.path.exists(abs_path):
        print("  File does not exist.")
        continue
    conn = sqlite3.connect(abs_path)
    cur = conn.cursor()
    try:
        cur.execute("SELECT COUNT(*) FROM patients")
        cnt = cur.fetchone()[0]
        print(f"  Patient count: {cnt}")
        cur.execute("SELECT id, name, age FROM patients")
        all_pts = cur.fetchall()
        pt_ids = [p[0] for p in all_pts]
        print(f"  All patient rows: {all_pts}")
        print(f"  First 10 IDs: {pt_ids[:10]}")
        print(f"  Last 10 IDs: {pt_ids[-10:]}")
        print(f"  P001 exists: {'P001' in pt_ids}")
        print(f"  P007 exists: {'P007' in pt_ids}")
        print(f"  P056 exists: {'P056' in pt_ids}")
        
        # Check counts of all other tables
        for table in ["notes", "medications", "allergies", "labs", "consultations"]:
            cur.execute(f"SELECT COUNT(*) FROM {table}")
            t_cnt = cur.fetchone()[0]
            print(f"  Table '{table}' count: {t_cnt}")
    except Exception as e:
        print("  Error querying table:", e)
    conn.close()
    print()
