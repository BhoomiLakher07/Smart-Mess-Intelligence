from database import get_connection

try:
    connection = get_connection()

    if connection.is_connected():
        print("MySQL connection successful!")

    connection.close()

except Exception as error:
    print("Database connection failed!")
    print(error)