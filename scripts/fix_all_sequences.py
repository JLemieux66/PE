import psycopg2
import os

DATABASE_URL = os.getenv("DATABASE_URL")
conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

# Fix companies sequence
cur.execute("SELECT setval('companies_id_seq', (SELECT MAX(id) FROM companies))")
result1 = cur.fetchone()
print(f'✅ Companies sequence reset to: {result1[0]}')

# Fix company_pe_investments sequence  
cur.execute("SELECT setval('company_pe_investments_id_seq', (SELECT MAX(id) FROM company_pe_investments))")
result2 = cur.fetchone()
print(f'✅ Investments sequence reset to: {result2[0]}')

conn.commit()
cur.close()
conn.close()

print("\n✅ All sequences fixed!")
