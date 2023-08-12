#Be sure to have the wa.db in the script folder.
#The script allows users to search for contacts based on phone numbers or specific words within 
#the 'Display Name' or 'WhatsApp Name' columns. 
#The script is case-insensitive, meaning it ignores the letter case when searching for terms, 
#and it also normalizes phone numbers by removing any spaces to ensure accurate matching.

import sqlite3

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
        number AS 'Phone Number',
        display_name AS 'Display Name',
        wa_name AS 'WhatsApp Name'
    FROM 
        wa_contacts
    WHERE 
        lower(wa_name) LIKE '%{normalized_term}%'
        OR lower(display_name) LIKE '%{normalized_term}%'
        OR replace(number, ' ', '') LIKE '%{normalized_term}%'
    """
    cursor.execute(query)

    # Show the results on the screen
    results = cursor.fetchall()
    if results:
        for row in results:
            print("Phone Number:", row[0])
            print("Display Name:", row[1])
            print("WhatsApp Name:", row[2])
            print("----------------------")
    else:
        print("No results found for the entered term.")

    # Close the connection to the database
    conn.close()

if __name__ == "__main__":
    while True:
        search_term = input("Enter a number or one or more words to search (press 'q' to exit): ")
        if search_term.lower() == 'q':
            break
        search_contacts(search_term)
