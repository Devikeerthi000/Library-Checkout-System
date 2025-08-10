# test_db_connection.py
import mysql.connector
from mysql.connector import Error

def connect_to_database():
    try:
        # Replace with your actual MySQL credentials
        connection = mysql.connector.connect(
            host='localhost',      # MySQL server host
            database='librarydb',  # Your database name
            user='root',  # Your MySQL username
            password='Lally@034'  # Your MySQL password
        )

        if connection.is_connected():
            print("Successfully connected to the database")
            return connection
        else:
            print("Connection failed")
            return None

    except Error as e:
        print(f"Error: {e}")
        return None

def close_connection(connection):
    if connection and connection.is_connected():
        connection.close()
        print("Connection closed")

# Test the connection
connection = connect_to_database()

# Close the connection after testing
if connection:
    close_connection(connection)
