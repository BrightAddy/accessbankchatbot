"""
Access Bank CRM Database Utility Module
======================================
Provides helper functions to query the Access Bank CRM SQL database safely.
"""

import os
from dotenv import load_dotenv

load_dotenv()

CRM_HOST = os.getenv("CRM_DB_HOST")
CRM_PORT = os.getenv("CRM_DB_PORT", "1433")
CRM_NAME = os.getenv("CRM_DB_NAME")
CRM_USER = os.getenv("CRM_DB_USER")
CRM_PASSWORD = os.getenv("CRM_DB_PASSWORD")

def get_crm_connection():
    """
    Attempts to establish a connection to the CRM SQL Server database.
    Tries pymssql first, then falls back to pyodbc.
    """
    if not (CRM_HOST and CRM_NAME and CRM_USER and CRM_PASSWORD):
        raise ValueError("CRM Database credentials not configured in .env")

    # Try pymssql first
    try:
        import pymssql
        return pymssql.connect(
            server=CRM_HOST,
            port=int(CRM_PORT),
            user=CRM_USER,
            password=CRM_PASSWORD,
            database=CRM_NAME,
            timeout=10,
            login_timeout=10
        )
    except Exception:
        pass

    # Fallback to pyodbc
    try:
        import pyodbc
        available_drivers = pyodbc.drivers()
        chosen_driver = "SQL Server"
        for d in ["ODBC Driver 18 for SQL Server", "ODBC Driver 17 for SQL Server", "SQL Server"]:
            if d in available_drivers:
                chosen_driver = d
                break

        conn_str = (
            f"DRIVER={{{chosen_driver}}};"
            f"SERVER={CRM_HOST},{CRM_PORT};"
            f"DATABASE={CRM_NAME};"
            f"UID={CRM_USER};"
            f"PWD={CRM_PASSWORD};"
            f"TrustServerCertificate=yes;"
        )
        return pyodbc.connect(conn_str, timeout=10)
    except Exception as e:
        raise ConnectionError(f"Could not connect to CRM SQL Database: {e}")

def query_crm(sql: str, params: tuple = None):
    """
    Executes a read-only query and returns a list of dictionaries representing the rows.
    Example:
        results = query_crm("SELECT TOP 5 AccountNumber, FullName FROM Customers WHERE Phone = %s", ('0241234567',))
    """
    conn = get_crm_connection()
    try:
        cursor = conn.cursor()
        if params:
            cursor.execute(sql, params)
        else:
            cursor.execute(sql)
        
        columns = [col[0] for col in cursor.description]
        rows = cursor.fetchall()
        return [dict(zip(columns, row)) for row in rows]
    finally:
        conn.close()
