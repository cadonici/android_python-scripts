print("**Android WhatsApp Self-destruction Reporter**\n")
print("Developed by Luca Cadonici\n")
print("This script is designed to retrieve and display information about WhatsApp contacts for whom the self-destruction setting is activated.")
print("It connects to the 'msgstore.db' and 'wa.db' databases, presenting details on contacts with enabled self-destructing messages settings.\n")
input("Press Enter to continue...")


import sqlite3

def main():
    # Connect to the msgstore.db database
    conn_msgstore = sqlite3.connect('msgstore.db')
    cursor_msgstore = conn_msgstore.cursor()

    # Define the SQL query for msgstore.db
    query_msgstore = '''
    SELECT
        jid.raw_string,
        jid.user AS "Phone Number",
        CASE
            WHEN message_ephemeral_setting.setting_duration >= 86400 THEN
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
    
    # Execute the query on msgstore.db
    cursor_msgstore.execute(query_msgstore)
    results_msgstore = cursor_msgstore.fetchall()

    # Close the connection to msgstore.db
    conn_msgstore.close()

    # Connect to the wa.db database
    conn_wa = sqlite3.connect('wa.db')
    cursor_wa = conn_wa.cursor()

    # Query to retrieve display names and WhatsApp names from wa_contacts in wa.db
    query_wa = """
        SELECT jid, display_name, wa_name
        FROM wa_contacts
        ORDER BY display_name;
    """

    # Execute the query in wa.db
    cursor_wa.execute(query_wa)
    results_wa = cursor_wa.fetchall()

    # Close the connection to wa.db
    conn_wa.close()

    # Compare and print results
    sorted_results = []
    for msgstore_result in results_msgstore:
        jid_raw_string = msgstore_result[0]
        phone_number = msgstore_result[1]
        expiration_setting = msgstore_result[2]

        for wa_result in results_wa:
            wa_jid, display_name, wa_name = wa_result
            if jid_raw_string == wa_jid:
                sorted_results.append((display_name, phone_number, wa_name, expiration_setting))
                break


    # Connect to the wa.db database
    conn_wa = sqlite3.connect('wa.db')
    cursor_wa = conn_wa.cursor()

    # Define the SQL query for wa.db (contacts with self-destructing messages)
    query_wa_self_destruct = '''
    SELECT
        number AS "Phone Number",
        display_name AS "Display Name",
        wa_name AS "WhatsApp Name",
        CASE
            WHEN disappearing_mode_duration >= 86400 THEN
                CAST(disappearing_mode_duration / 86400 AS VARCHAR) || ' days'
            WHEN disappearing_mode_duration >= 3600 THEN
                CAST(disappearing_mode_duration / 3600 AS VARCHAR) || ' hours'
            WHEN disappearing_mode_duration >= 60 THEN
                CAST(disappearing_mode_duration / 60 AS VARCHAR) || ' minutes'
            ELSE
                CAST(disappearing_mode_duration AS VARCHAR) || ' seconds'
        END AS "Expiration Setting"
    FROM 
        wa_contacts
    WHERE disappearing_mode_duration IS NOT null
    '''
    
    # Execute the query on wa.db
    cursor_wa.execute(query_wa_self_destruct)
    result_wa = cursor_wa.fetchall()



    conn_wa.close()

    # Calculate total contacts with self-destruction
    total_msgstore_results = len(sorted_results)
    total_wa_results = len(result_wa)
    total_contacts_with_self_destruction = total_msgstore_results + total_wa_results

    print("\nTotal contacts with self-destruction from 'msgstore.db':", total_msgstore_results)
    print("Total contacts with self-destruction from 'wa.db':", total_wa_results)
    print("Overall total of contacts with self-destruction:", total_contacts_with_self_destruction)


    input("\nPress Enter to retrieve results from 'msgstore.db'...")
    
    # Print the results
    print("\nResults from 'msgstore.db':\n")
    for display_name, phone_number, wa_name, expiration_setting in sorted_results:
        print("Display Name:", display_name if display_name is not None else "N/A")
        print("WhatsApp Name:", wa_name)
        print("Phone Number:", phone_number)
        print("Expiration Setting:", expiration_setting)
        print("------------------------")


    input("\nPress Enter to retrieve results from 'wa.db'...")
    print("\nResults from 'wa.db':\n")
    for contact_row in result_wa:
        phone_number = contact_row[0]
        display_name = contact_row[1]
        wa_name = contact_row[2]
        expiration_setting = contact_row[3]
        print("Phone Number:", phone_number)
        print("Display Name:", display_name)
        print("WhatsApp Name:", wa_name)
        print("Expiration Setting:", expiration_setting)
        print("------------------------")

if __name__ == '__main__':
    main()
