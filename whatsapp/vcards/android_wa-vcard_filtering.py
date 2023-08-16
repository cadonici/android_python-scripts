import sqlite3

# Connect to the database
conn = sqlite3.connect('msgstore.db')
cursor = conn.cursor()

# Execute query to fetch distinct vCards
distinct_vcards_query = "SELECT DISTINCT vcard FROM message_vcard"
cursor.execute(distinct_vcards_query)
distinct_vcards = cursor.fetchall()

# Calculate the number of distinct vCards
num_distinct_vcards = len(distinct_vcards)
print("Number of distinct vCards:", num_distinct_vcards)
print("-" * 30)

# Create a list to store extracted vCard details
vcard_details = []

# Function to clean phone number
def clean_phone_number(number):
    # Remove spaces and numbers between ":" and "+"
    clean_number = ''.join(part for part in number.split(':') if not part.strip().isdigit() and part != '+')
    return clean_number

# Loop through distinct vCards and extract details
for vcard_row in distinct_vcards:
    vcard_data = vcard_row[0]
    fn = ""
    tel = ""
    label = ""

    lines = vcard_data.split('\n')
    for line in lines:
        if line.startswith('FN:'):
            fn = line[3:]
        elif "TEL" in line:
            tel_parts = line.split('TEL')[1].strip()
            tel = ""
            label = ""

            for part in tel_parts.split(';'):
                if part.startswith('type='):
                    label = part[5:]
                elif part.startswith('waid='):
                    tel = part[5:].strip()  # Apply strip() to remove spaces
            if not tel:
                tel = tel_parts.strip()  # Apply strip() to remove spaces
        elif line.startswith('item1.X-ABLabel:'):
            label = line[16:]

    # If item1.TEL: is not present, look for item1.TEL;waid=
    if not tel:
        for line in lines:
            if "waid=" in line:
                tel = line.split('=')[1].strip()  # Apply strip() to remove spaces

    if tel:  # Check if tel value is not empty
        tel = clean_phone_number(tel)  # Clean phone number
        vcard_details.append((fn, tel, label))

# Sort the vCard details list alphabetically by FN
vcard_details.sort(key=lambda x: x[0])

# Print the sorted vCard details
for fn, tel, label in vcard_details:
    print("FN:", fn)
    print("Phone Number:", tel.replace(" ", ""))  # Remove spaces from phone number
    print("Label:", label)
    print("-" * 30)
# Close the database connection
conn.close()
