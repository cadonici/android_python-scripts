print("Android Contacts Parser")
print("Developed by: Luca Cadonici")
print("This script connects to a 'wa.db' database containing Android's Phonebook and WahtsApp contacts.")
print("It allows you to search for contacts based on WhatsApp name, display name, or phone number.")
print("The script displays the results, including contact details and status information.")
print("To exit the script, press 'q' when prompted.")
print("\n")

import os
import sqlite3

# Check if the 'wa.db' database file exists in the script's folder
script_folder = os.path.dirname(os.path.abspath(__file__))
db_file = os.path.join(script_folder, 'wa.db')

if not os.path.exists(db_file):
    print("Please place the 'wa.db' database file in the same folder as this script.")
    exit(1)

def normalize_phone_number(number):
    # Remove spaces and return the normalized phone number
    return number.replace(" ", "")

def search_contacts(term):
    # Connect to the 'wa.db' database
    conn = sqlite3.connect('wa.db')
    cursor = conn.cursor()

    # Normalize the search term and make it case-insensitive
    normalized_term = term.strip().lower()

    # Execute the query to search for the term in the specified columns
    query = f"""
    SELECT 
        CASE
            WHEN number IS NULL THEN
                SUBSTR(jid, 1, INSTR(jid, '@s.whatsapp.net') - 1)
            ELSE
                number
        END AS 'Phone Number',
        display_name AS 'Display Name',
        wa_name AS 'WhatsApp Name',
        status AS 'Status',
        CASE
            WHEN status_timestamp = 0 THEN NULL
            ELSE strftime('%Y-%m-%d %H:%M:%S.', status_timestamp / 1000, 'unixepoch') || (status_timestamp % 1000)
        END AS "Status timestamp",
            jid
    FROM wa_contacts
    WHERE 
        lower(wa_name) LIKE '%{normalized_term}%'
        OR lower(display_name) LIKE '%{normalized_term}%'
        OR replace(number, ' ', '') LIKE '%{normalized_term}%'
    """
    cursor.execute(query)

    # Show the results on the screen
    results = cursor.fetchall()

    # Close the connection to the database
    conn.close()

    if results:
        # Print all the phone numbers found
        for row in results:
            print("Phone Number:", row[0])
            print("Display Name:", row[1])
            print("WhatsApp Name:", row[2])
            print("WhatsApp Status:", row[3])
            print("WhatsApp Status Timestamp:", row[4])
            print("----------------------")
    else:
        print("No results found for the entered term.")

if __name__ == "__main__":
    while True:
        search_term = input("Enter a number or one or more words to search (press 'q' to exit): ")
        if search_term.lower() == 'q':
            break
        search_contacts(search_term)
