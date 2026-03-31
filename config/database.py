import os
import urllib
from sqlalchemy import create_engine
from dotenv import load_dotenv

load_dotenv()

username = os.getenv("DB_USER")
password = os.getenv("DB_PASS")
server = os.getenv("DB_SERVER")
database = os.getenv("DB_NAME")

params = urllib.parse.quote_plus(
    f"DRIVER=ODBC Driver 18 for SQL Server;"
    f"SERVER={server};"
    f"DATABASE={database};"
    f"UID={username};"
    f"PWD={password};"
    f"Encrypt=yes;"
    f"TrustServerCertificate=no;"
)

connection_string = f"mssql+pyodbc:///?odbc_connect={params}"
print("Connection String:", connection_string)
engine = create_engine(connection_string)