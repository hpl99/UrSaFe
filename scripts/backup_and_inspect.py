import sqlite3
import shutil
import os
import time

db_src = r"data/ursafe_production.db"
ts = time.strftime("%Y%m%d_%H%M%S")
backup_dir = r"C:\Users\edgeo\.gemini\antigravity-ide\brain\691d3538-2344-4d04-9ce8-eb5a165268c7\backups"
os.makedirs(backup_dir, exist_ok=True)
backup_dst = os.path.join(backup_dir, f"ursafe_production_backup_{ts}.db")
shutil.copy2(db_src, backup_dst)
print(f"Backed up to: {backup_dst}")

local_backup = f"data/backup_ursafe_production_{ts}.db"
shutil.copy2(db_src, local_backup)
print(f"Local backup created: {local_backup}")

con = sqlite3.connect(db_src)
tables = [r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'").fetchall()]
print("\nTABLE ROW COUNTS:")
for t in sorted(tables):
    c = con.execute(f"SELECT count(*) FROM {t}").fetchone()[0]
    print(f"  {t}: {c}")

print("\nUNIQUE REPORTERS IN INCIDENTS:")
for r in con.execute("SELECT reporter_user_id, count(*), min(created_at), max(created_at) FROM incidents GROUP BY reporter_user_id").fetchall():
    print(r)

print("\nSAMPLE INCIDENTS (id, reporter, lat, lon, desc):")
for r in con.execute("SELECT id, reporter_user_id, latitude, longitude, description FROM incidents ORDER BY created_at DESC LIMIT 15").fetchall():
    print(r)

print("\nCOORDINATE DIVERSITY IN INCIDENTS:")
for r in con.execute("SELECT latitude, longitude, count(*) FROM incidents GROUP BY latitude, longitude").fetchall():
    print(r)

print("\nUSERS TABLE:")
for r in con.execute("SELECT id, username, role, full_name, email FROM users").fetchall():
    print(r)
