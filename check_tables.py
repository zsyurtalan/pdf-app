import sqlite3

# Veritabanına bağlan
conn = sqlite3.connect('pdf_learning.db')
cursor = conn.cursor()

# Tabloları listele
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()

print("Oluşturulan tablolar:")
for table in tables:
    print(f"- {table[0]}")

# Her tablonun yapısını göster
for table in tables:
    table_name = table[0]
    print(f"\n{table_name} tablosu:")
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    for column in columns:
        print(f"  - {column[1]} ({column[2]})")

conn.close()
