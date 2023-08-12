#WhatsApp Message Exchange Reporter
# This script generates a report of phone numbers involved in WhatsApp message exchanges. The report includes details such as the display name (if available), phone number, message count, and raw string associated with the contact. The script first connects to the 'msgstore.db' and 'wa.db' SQLite databases, which are commonly used by WhatsApp. It then retrieves information from these databases and sorts the results based on message count and display name.

import sqlite3

# Explanation about the sorting criteria
print("\nScript to generate a report of all phone numbers involved in WhatsApp message exchanges.\n")
print("Results are sorted by Message Count (descending) and then by Display Name.\n\n")

# Prompt the user to place 'msgstore.db' and 'wa.db' databases in the script's directory
input("Please ensure that 'msgstore.db' and 'wa.db' databases are in the same directory as this script. Press Enter to continue...")

# Explanation about the script
# ... (rest of the script remains unchanged)

# 

# Connect to the msgstore.db database
conn_msgstore = sqlite3.connect('msgstore.db')
cursor_msgstore = conn_msgstore.cursor()

# Query to retrieve phone numbers and their associated message counts
query_msgstore = """
    SELECT jid.user AS "Phone Number",
           COUNT(*) AS "Message Count",
           jid.raw_string AS "Raw String"
    FROM jid
    INNER JOIN chat ON chat.jid_row_id = jid._id
    INNER JOIN message ON chat._id = message.chat_row_id
    GROUP BY jid.user, jid.raw_string
    ORDER BY "Message Count" DESC, jid.user;
"""

# Execute the query in msgstore.db
cursor_msgstore.execute(query_msgstore)
results_msgstore = cursor_msgstore.fetchall()

# Close the connection to msgstore.db
conn_msgstore.close()

# Connect to the wa.db database
conn_wa = sqlite3.connect('wa.db')
cursor_wa = conn_wa.cursor()

# Query to retrieve display names from wa_contacts in wa.db
query_wa = """
    SELECT jid, display_name
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
    phone_number, message_count, raw_string = msgstore_result
    for wa_result in results_wa:
        wa_jid, display_name = wa_result
        if raw_string == wa_jid:
            sorted_results.append((display_name, phone_number, message_count, raw_string))
            break

# Sort results by Message Count (descending) and then by Display Name
sorted_results.sort(key=lambda x: (x[2], x[0] if x[0] is not None else ""), reverse=True)

# Print sorted results
for display_name, phone_number, message_count, raw_string in sorted_results:
    print("Display Name:", display_name)
    print("Phone Number:", phone_number)
    print("Message Count:", message_count)
    print("Raw String:", raw_string)
    print("-" * 30)

# Print the total number of contacts with message exchanges
print("\nTotal number of contacts with message exchanges:", len(sorted_results))


