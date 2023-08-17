import sqlite3
import os

# Function to process the database
def process_database(database_path, results_wa):
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()

    query_msgstore = '''
        SELECT
            jid.raw_string,
            jid.user AS "Phone Number",
            CASE
                WHEN message_ephemeral_setting.setting_duration = 0 THEN '(deactivated)'
                WHEN message_ephemeral_setting.setting_duration > 86400 THEN
                    CAST(message_ephemeral_setting.setting_duration / 86400 AS VARCHAR) || ' days'
                WHEN message_ephemeral_setting.setting_duration >= 3600 THEN
                    CAST(message_ephemeral_setting.setting_duration / 3600 AS VARCHAR) || ' hours'
                WHEN message_ephemeral_setting.setting_duration >= 60 THEN
                    CAST(message_ephemeral_setting.setting_duration / 60 AS VARCHAR) || ' minutes'
                ELSE
                    CAST(message_ephemeral_setting.setting_duration AS VARCHAR) || ' seconds'
            END AS "Expiration Setting"
        FROM
            message
        INNER JOIN
            chat ON message.chat_row_id = chat._id
        INNER JOIN
            message_ephemeral_setting ON message._id = message_ephemeral_setting.message_row_id
        INNER JOIN
            jid ON chat.jid_row_id = jid._id
    '''

    cursor.execute(query_msgstore)
    results_msgstore = cursor.fetchall()
    conn.close()

    sorted_results = {}
    for msgstore_result in results_msgstore:
        jid_raw_string = msgstore_result[0]
        phone_number = msgstore_result[1]
        expiration_setting = msgstore_result[2]

        for wa_result in results_wa:
            wa_jid, display_name, wa_name = wa_result
            if jid_raw_string == wa_jid:
                key = (display_name, wa_name, phone_number)
                if key not in sorted_results:
                    sorted_results[key] = [expiration_setting]
                else:
                    sorted_results[key].append(expiration_setting)
                break

    return sorted_results

def main():
    print("**Android WhatsApp Self-destruction Reporter**\n")
    print("Developed by Luca Cadonici\n")
    print("This script connects to the 'msgstore.db' database, retrieving and displaying details on contacts with enabled self-destructing message settings.")
    print("It also connects to the 'wa.db' database to retrieve display names and WhatsApp names of contacts. If decrypted backup files of 'msgstore.db' are present in the folder, they will be analyzed.")
    input("Press Enter to continue...")
    print("Please ensure you have the 'msgstore.db', 'wa.db' databases, and any decrypted backup .db files (NO .crypt12, .crypt13, .crypt14 etc.) in the same folder.")
    input("Press Enter to continue...")
    conn_wa = sqlite3.connect('wa.db')
    cursor_wa = conn_wa.cursor()

    query_wa = """
        SELECT jid, display_name, wa_name
        FROM wa_contacts
        ORDER BY display_name;
    """

    cursor_wa.execute(query_wa)
    results_wa = cursor_wa.fetchall()
    conn_wa.close()

    # Process 'msgstore.db'
    print("Processing data from: msgstore.db")
    msgstore_db_results = process_database("msgstore.db", results_wa)

    # Display results from 'msgstore.db'
    total_msgstore_results = len(msgstore_db_results)
    print("\nTotal contacts with self-destruction in msgstore.db:", total_msgstore_results)
    print("\nConsolidated results from 'msgstore.db':")
    for key, expiration_setting in msgstore_db_results.items():
        print("Display Name:", key[0])
        print("WhatsApp Name:", key[1])
        print("Phone Number:", key[2])
        print("Expiration Setting:", expiration_setting)
        print("-" * 30)

    # Prompt to extend the operation to other backup files
    prompt = input("\nDo you want to extend the operation to other backup files? (yes/no): ").strip().lower()
    if prompt == "yes":
        # Get a list of backup files with 'msgstore' in the name
        database_files = [filename for filename in os.listdir('.') if "msgstore" in filename and filename != "msgstore.db"]

        for db_file in database_files:
            if db_file != "msgstore.db":
                print("\nProcessing data from:", db_file)
                backup_results = process_database(db_file, results_wa)
                total_backup_results = len(backup_results)
                print(f"\nTotal contacts with self-destruction in {db_file}: {total_backup_results}")
                
                differences_found = False
                for key, expiration_setting in msgstore_db_results.items():
                    if key not in backup_results:
                        differences_found = True
                        break
                
                if differences_found:
                    print(f"\nDifferences from 'msgstore.db' analysis:")
                    for key, expiration_setting in msgstore_db_results.items():
                        if key not in backup_results:
                            print(f"File: {db_file}\n")
                            print("Display Name:", key[0])
                            print("WhatsApp Name:", key[1])
                            print("Phone Number:", key[2])  # Extract the phone number from the key tuple
                            print("Expiration Setting:", "Not Activated")
                            print("-" * 30)
                    for key, expiration_setting in backup_results.items():
                        if key not in msgstore_db_results:
                            print(f"File: {db_file}\n")
                            print("Display Name:", key[0])
                            print("WhatsApp Name:", key[1])
                            print("Phone Number:", key[2])  # Extract the phone number from the key tuple
                            print("Expiration Setting:", expiration_setting)
                            print("-" * 30)
                else:
                    print("No differences from msgstore.db")

if __name__ == '__main__':
    main()
