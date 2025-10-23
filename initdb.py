import pg8000

params = {
    'host': '172.29.176.1',
    'user': 'postgres',
    'password': 'Benedicta@22',
    'database': 'huncho_clothing'
}

try:
    conn = pg8000.connect(**params)
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM pg_database WHERE datname = 'huncho_clothing'")
    exists = cursor.fetchone()

    if not exists:
        cursor.execute('CREATE DATABASE huncho_clothing')
        print("Database created successfully!")
    else:
        print("Database already exists.")
    
    conn.commit()
    cursor.close()
    conn.close()

except Exception as e:
    print(f"Error connecting to PostgreSQL: {e}")