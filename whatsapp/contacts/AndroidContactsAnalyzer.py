import os
import zipfile
import sqlite3

# Get the current directory where the script is executed
current_directory = os.getcwd()

# Initialize zip_filename as None
zip_filename = None

# Introductory messages
print("Android Contacts Analyzer v. 1.1")
print("\n")
print("Developed by: Luca Cadonici")
print("This script searches for 'contacts2.db' and 'wa.db' databases within ZIP or TAR files in the script's folder.")
print("It allows you to search for contacts based on WhatsApp name, display name, or phone number and returns the result in basic or extended form, including additional information such as the contact's last modification date.")
print("To exit the script, press 'q' when prompted.")
print("\n")
# Print ZIP file information at the beginning
for filename in os.listdir(current_directory):
    if filename.endswith(".zip"):
        print(f"ZIP file found: {filename}")
        print("\n")
        zip_filename = filename  # Store the ZIP filename for later use
        break

# Initialize a dictionary to store associations between phone numbers and contact information
phone_number_to_contact_info = {}

# Function to print basic contact information
def print_basic_contact_info(contact_info):
    print("Display Name:", contact_info['display_name'])
    print("Phone Number:", contact_info['phone_number'])
    print("WhatsApp Name:", contact_info['whatsapp_name'])
    print("----------------------")

# Function to print complete contact information
def print_complete_contact_info(contact_info, last_updated_timestamp):
    print("Display Name:", contact_info['display_name'])
    print("Phone Number:", contact_info['phone_number'])
    print("WhatsApp Name:", contact_info['whatsapp_name'])
    print("WhatsApp Status:", contact_info['status'])
    print("Contact Update timestamp (from contacts2.db):", last_updated_timestamp)
    print("WhatsApp Status Timestamp:", contact_info['status_timestamp'])
    print("----------------------")

# Function to search for "contacts2.db" files in a ZIP archive and update the phone_number_to_contact_info dictionary
def search_for_contacts2_db_in_zip(zip_filename, normalized_term):
    with zipfile.ZipFile(zip_filename, 'r') as zip_ref:
        for file_info in zip_ref.infolist():
            if 'data/data/com.Android.providers.contacts/databases/' in file_info.filename or 'data/data/com.samsung.android.providers.contacts/databases/' in file_info.filename:
                if file_info.filename.endswith("contacts2.db"):
                    # Extract the 'contacts2.db' file to the current directory
                    zip_ref.extract(file_info, current_directory)
                    db_filename = os.path.join(current_directory, file_info.filename)
                    # Update the phone_number_to_contact_info dictionary with contact information from 'contacts2.db'
                    update_phone_number_to_contact_info(db_filename, normalized_term)

# Function to update the phone_number_to_contact_info dictionary with contact information from 'contacts2.db'
def update_phone_number_to_contact_info(db_filename, normalized_term):
    try:
        conn = sqlite3.connect(db_filename)
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT DISTINCT
                raw_contacts.display_name AS 'Display Name',
                phone_lookup.normalized_number AS 'Phone Number',
                strftime('%Y-%m-%d %H:%M:%S.', "contact_last_updated_timestamp" / 1000, 'unixepoch') || ("contact_last_updated_timestamp" % 1000) AS "Last updated timestamp"
            FROM raw_contacts
            INNER JOIN phone_lookup ON raw_contacts._id = phone_lookup.raw_contact_id
            INNER JOIN contacts ON raw_contacts._id = contacts.name_raw_contact_id
            WHERE
                raw_contacts.display_name LIKE '%{normalized_term}%'
                OR phone_lookup.normalized_number LIKE '%{normalized_term}%'
        """)
        rows = cursor.fetchall()
        if rows:
            for row in rows:
                contact_info = {
                    'display_name': row[0],
                    'phone_number': row[1],
                    'last_updated_timestamp': row[2],  # Assuming it's in the third column of the query
                    'whatsapp_name': None,  # Placeholder for WhatsApp Name
                    'status': None,  # Placeholder for WhatsApp Status
                    'status_timestamp': None,  # Placeholder for WhatsApp Status Timestamp
                    'jid': None  # Placeholder for WhatsApp JID
                }
                phone_number_to_contact_info[row[1]] = contact_info
        else:
            print("No results found for the entered term in 'contacts2.db'.")
    except sqlite3.Error as e:
        print(f"Error opening the database '{db_filename}': {e}")
    finally:
        conn.close()

# Function to search for "wa.db" files in a ZIP archive and update the phone_number_to_contact_info dictionary
def search_for_wa_db_in_zip(zip_filename, normalized_term):
    with zipfile.ZipFile(zip_filename, 'r') as zip_ref:
        for file_info in zip_ref.infolist():
            if 'data/data/com.whatsapp/databases/' in file_info.filename and file_info.filename.endswith("wa.db"):
                # Extract the 'wa.db' file to the current directory
                zip_ref.extract(file_info, current_directory)
                db_filename = os.path.join(current_directory, file_info.filename)
                # Update the phone_number_to_contact_info dictionary with WhatsApp information from 'wa.db'
                update_phone_number_to_contact_info_from_wa_db(db_filename, normalized_term)

# Function to update the phone_number_to_contact_info dictionary with WhatsApp information from 'wa.db'
def update_phone_number_to_contact_info_from_wa_db(db_filename, normalized_term):
    try:
        conn = sqlite3.connect(db_filename)
        cursor = conn.cursor()
        cursor.execute(f"""
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
                END AS "Status Timestamp",
                jid
            FROM wa_contacts
            WHERE 
                lower(wa_name) LIKE '%{normalized_term}%'
                OR lower(display_name) LIKE '%{normalized_term}%'
                OR replace(number, ' ', '') LIKE '%{normalized_term}%'
        """)
        rows = cursor.fetchall()
        if rows:
            for row in rows:
                phone_number = row[0]
                if phone_number in phone_number_to_contact_info:
                    # Update the existing contact_info with WhatsApp information
                    contact_info = phone_number_to_contact_info[phone_number]
                    contact_info['whatsapp_name'] = row[2]
                    contact_info['status'] = row[3]
                    contact_info['status_timestamp'] = row[4]
                    contact_info['jid'] = row[5]
        else:
            print("No results found for the entered term in 'wa.db'.")
    except sqlite3.Error as e:
        print(f"Error opening the database '{db_filename}': {e}")
    finally:
        conn.close()


# Continuous search loop
while True:
    normalized_term = input("Enter a number or one or more words to search (press 'q' to exit): ")
    if normalized_term.lower() == 'q':
        break

    # Search for contact information in 'contacts2.db'
    search_for_contacts2_db_in_zip(zip_filename, normalized_term)

    # Search for contact information in 'wa.db'
    search_for_wa_db_in_zip(zip_filename, normalized_term)

    # Print basic contact information
    for phone_number, contact_info in phone_number_to_contact_info.items():
        print_basic_contact_info(contact_info)

    # Ask the user if they want to see complete information
    show_complete_info = input("Do you want to see complete information? (yes/no): ").strip().lower()
    if show_complete_info == 'yes':
        for phone_number, contact_info in phone_number_to_contact_info.items():
            # Include the last_updated_timestamp argument here
            print_complete_contact_info(contact_info, contact_info['last_updated_timestamp'])

    phone_number_to_contact_info.clear()  # Clear the dictionary for the next search

