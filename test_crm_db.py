"""
Access Bank CRM SQL Database Connection Test Script
===================================================
Tests connectivity from your local machine to the CRM SQL Server database.
Reads credentials safely from your .env file.
"""

import os
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

from dotenv import load_dotenv

# Load variables from .env
load_dotenv()

CRM_HOST = os.getenv("CRM_DB_HOST")
CRM_PORT = os.getenv("CRM_DB_PORT", "1433")
CRM_NAME = os.getenv("CRM_DB_NAME")
CRM_USER = os.getenv("CRM_DB_USER")
CRM_PASSWORD = os.getenv("CRM_DB_PASSWORD")

def check_credentials():
    missing = []
    if not CRM_HOST: missing.append("CRM_DB_HOST")
    if not CRM_NAME: missing.append("CRM_DB_NAME")
    if not CRM_USER: missing.append("CRM_DB_USER")
    if not CRM_PASSWORD: missing.append("CRM_DB_PASSWORD")
    
    if missing:
        print("[!] Missing required database settings in your .env file:")
        for key in missing:
            print(f"    - {key}")
        print("\nPlease add them to your .env file:")
        print("CRM_DB_HOST=your-crm-server-ip-or-hostname")
        print("CRM_DB_PORT=1433")
        print("CRM_DB_NAME=CRM_DATABASE_NAME")
        print("CRM_DB_USER=your_crm_username")
        print("CRM_DB_PASSWORD=your_crm_password")
        return False
    return True

def test_via_pymssql():
    print("\n[+] Attempt 1: Connecting via pymssql (Direct TDS Protocol)...")
    try:
        import pymssql
        conn = pymssql.connect(
            server=CRM_HOST,
            port=int(CRM_PORT),
            user=CRM_USER,
            password=CRM_PASSWORD,
            database=CRM_NAME,
            timeout=10,
            login_timeout=10
        )
        cursor = conn.cursor()
        cursor.execute("SELECT @@VERSION, GETDATE()")
        row = cursor.fetchone()
        version_line = row[0].split('\n')[0] if row else "Unknown"
        server_time = row[1] if row else "Unknown"
        
        print("[SUCCESS] Connected via pymssql!")
        print(f"    Server Version: {version_line}")
        print(f"    Server Time:    {server_time}")
        
        # Test query tables
        cursor.execute("SELECT TOP 5 TABLE_SCHEMA, TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE'")
        tables = cursor.fetchall()
        if tables:
            print("\n    Sample CRM Tables accessible:")
            for schema, tbl in tables:
                print(f"    - {schema}.{tbl}")
        conn.close()
        return True
    except Exception as e:
        print(f"    [-] pymssql connection failed: {e}")
        return False

def test_via_pyodbc():
    print("\n[+] Attempt 2: Connecting via pyodbc (Windows ODBC Driver)...")
    try:
        import pyodbc
        available_drivers = pyodbc.drivers()
        print(f"    Installed ODBC Drivers: {available_drivers}")
        
        # Choose best driver
        chosen_driver = None
        for d in ["ODBC Driver 18 for SQL Server", "ODBC Driver 17 for SQL Server", "SQL Server"]:
            if d in available_drivers:
                chosen_driver = d
                break
        
        if not chosen_driver:
            print("    [-] No SQL Server ODBC driver found in pyodbc.")
            return False
            
        print(f"    Using driver: '{chosen_driver}'")
        
        # Connection string
        conn_str = (
            f"DRIVER={{{chosen_driver}}};"
            f"SERVER={CRM_HOST},{CRM_PORT};"
            f"DATABASE={CRM_NAME};"
            f"UID={CRM_USER};"
            f"PWD={CRM_PASSWORD};"
            f"TrustServerCertificate=yes;"
        )
        conn = pyodbc.connect(conn_str, timeout=10)
        cursor = conn.cursor()
        cursor.execute("SELECT @@VERSION, GETDATE()")
        row = cursor.fetchone()
        version_line = row[0].split('\n')[0] if row else "Unknown"
        server_time = row[1] if row else "Unknown"
        
        print("[SUCCESS] Connected via pyodbc!")
        print(f"    Server Version: {version_line}")
        print(f"    Server Time:    {server_time}")
        conn.close()
        return True
    except Exception as e:
        print(f"    [-] pyodbc connection failed: {e}")
        return False

def main():
    print("=" * 60)
    print("Access Bank CRM Database Connectivity Diagnostic")
    print("=" * 60)
    
    if not check_credentials():
        sys.exit(1)
        
    print(f"Target Server: {CRM_HOST}:{CRM_PORT}")
    print(f"Target DB:     {CRM_NAME}")
    print(f"Target User:   {CRM_USER}")
    
    success = test_via_pymssql()
    if not success:
        success = test_via_pyodbc()
        
    print("\n" + "=" * 60)
    if success:
        print("[SUCCESS] DB CONNECTION VERIFIED! Your local machine can query the CRM DB.")
        print("You can now safely integrate CRM queries into your chatbot.")
    else:
        print("[!] CONNECTION TROUBLESHOOTING:")
        print("1. Network / Firewall: Are you connected to Access Bank's VPN or Office LAN?")
        print("2. IP Whitelist: Bank firewalls block unrecognized IPs. Ask the DBA to whitelist your IP.")
        print("3. Port 1433: Confirm if CRM SQL uses port 1433 or a custom port / named instance (e.g. HOST\\INSTANCE).")
        print("4. Credentials: Verify the username and password have SELECT rights to the database.")
    print("=" * 60)

if __name__ == "__main__":
    main()
