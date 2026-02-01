import os
import init_db

# Set environment variables for the Cloud Database (Clever Cloud)
os.environ['DB_HOST'] = 'brbxtuytyv3xikrvvtcl-mysql.services.clever-cloud.com'
os.environ['DB_NAME'] = 'brbxtuytyv3xikrvvtcl'
os.environ['DB_USER'] = 'um3mvliujobafqck'
os.environ['DB_PASSWORD'] = 'lDLCEsMLHpfgn7qizFw0'
os.environ['DB_PORT'] = '3306'

print("Initializing Cloud Database...")
try:
    init_db.init_db()
    print("Cloud Database initialized successfully!")
except Exception as e:
    print(f"Error initializing database: {e}")
