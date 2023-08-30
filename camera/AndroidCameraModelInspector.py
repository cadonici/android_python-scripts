import os
import zipfile
from PIL import Image
import tempfile
import shutil
from collections import defaultdict
import piexif
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
import hashlib
from PIL.ExifTags import TAGS, GPSTAGS
from datetime import datetime 

print("Android Camera Model Inspector")
print("Developed by Luca Cadonici")
print("This script inspects image files in a directory or ZIP archive and extracts EXIF metadata such as camera make, model, GPS information, and more.")
print("Required libraries: Pillow (PIL), piexif, geopy")
print("\n")
print("You can install the required libraries using the following commands:")
print("pip install Pillow piexif geopy\n")

def get_decimal_from_dms(dms, ref):
    degrees, minutes, seconds = dms
    decimal_value = degrees + minutes / 60 + seconds / 3600
    if ref in ['S', 'W']:
        decimal_value = -decimal_value
    return decimal_value

def get_image_metadata_png(image_path):
    try:
        with Image.open(image_path) as img:
            exif_data = img.getexif()
            return exif_data
    except (IOError, OSError):
        return None

def get_image_metadata(image_path):
    try:
        with Image.open(image_path) as img:
            if img.format == 'GIF':
                return None
            else:
                exif_data = img.getexif()
                return exif_data
    except (IOError, OSError):
        return None

geolocator = Nominatim(user_agent="my_geocoder", timeout=2000)
current_directory = '.'

def find_image_files_in_zip(zip_file_path):
    image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp']
    image_files = []

    with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
        for zip_info in zip_ref.infolist():
            if any(zip_info.filename.lower().endswith(ext) for ext in image_extensions):
                image_files.append(zip_info.filename)

    return image_files

def convert_coordinate(degrees, minutes, seconds, direction):
    decimal_value = degrees + (minutes / 60) + (seconds / 3600)
    if direction in [b'S', b'W']:
        decimal_value = -decimal_value
    return decimal_value

def get_address_from_gps_nominatim(latitude, longitude):
    try:
        location = geolocator.reverse((latitude, longitude), exactly_one=True)
        if location:
            return location.address
        else:
            return "Unknown Address"
    except GeocoderTimedOut:
        return "Geocoding service timed out. Unable to retrieve address."

all_images_report = []  
while True:
    with tempfile.TemporaryDirectory() as temp_dir:
        metadata_counts = defaultdict(int)

        for filename in os.listdir(current_directory):
            if filename.lower().endswith('.zip'):
                zip_path = os.path.join(current_directory, filename)
                zip_name = os.path.splitext(filename)[0]
                image_files = find_image_files_in_zip(zip_path)

                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(temp_dir)

                for image_file in image_files:
                    image_path = os.path.join(temp_dir, image_file)
                    
                    exif_data = get_image_metadata(image_path)
                    if exif_data and 271 in exif_data and 272 in exif_data:
                        make = exif_data.get(271, '').strip()
                        model = exif_data.get(272, '').strip()
                        if make and model:
                            metadata_counts[(make, model)] += 1

        sorted_metadata = sorted(metadata_counts.items(), key=lambda item: (-item[1], item[0][0], item[0][1]))

        header = ("Make", "Model", "Count")
        max_col_width = (max(len(col) for col in header) + 2) * 4

        print("Report - Count of Images Grouped by Make and Model")
        print("=" * (max_col_width * len(header)))
        print("{:^{width}} {:^{width}} {:^{width}}".format(header[0], header[1], header[2], width=max_col_width))
        print("=" * (max_col_width * len(header)))

        for (make, model), total_count in sorted_metadata:
            print("{:^{width}} {:^{width}} {:^{width}}".format(make, model, total_count, width=max_col_width))

        valid_make_values = {make for (make, _), _ in sorted_metadata}
        valid_model_values = {model for (_, model), _ in sorted_metadata}

        while True:
            selected_make = input("\nEnter the camera make: ").strip()
            if selected_make in valid_make_values:
                break
            else:
                print("Invalid Make value. Please enter a valid Make.")

        while True:
            selected_model = input("Enter the camera model: ").strip()
            if selected_model in valid_model_values:
                break
            else:
                print("Invalid Model value. Please enter a valid Model.")

        output_directory = os.path.join(current_directory, "images_exif", f"{selected_make}_{selected_model}")
        report_directory = os.path.join(current_directory, "images_exif")
        os.makedirs(output_directory, exist_ok=True)


        # Copy and process images
        for filename in os.listdir(current_directory):
            if filename.lower().endswith('.zip'):
                zip_path = os.path.join(current_directory, filename)
                image_files = find_image_files_in_zip(zip_path)

                for image_file in image_files:
                    image_path_in_zip_short = '/'.join(image_file.split('/')[1:])
                    image_name = os.path.basename(image_file)
                    image_path = os.path.join(temp_dir, image_file)
                    
                    if image_file.lower().endswith('.png'):
                        exif_data = get_image_metadata_png(image_path)
                    else:
                        exif_data = get_image_metadata(image_path)
                    
                    if exif_data and 271 in exif_data and 272 in exif_data:
                        make = exif_data.get(271, '').strip()
                        model = exif_data.get(272, '').strip()
                        if make == selected_make and model == selected_model:
                            new_image_name = image_name
                            count = 1
                            while os.path.exists(os.path.join(output_directory, new_image_name)):
                                    base_name, extension = os.path.splitext(image_name)
                                    new_image_name = f"{base_name}_{count}{extension}"
                                    count += 1
                            new_image_path = os.path.join(output_directory, new_image_name)

                            # Process and print EXIF data
                            if image_file.lower().endswith('.png'):  
                                def get_exif_data(image):
                                        exif_data = image._getexif()
                                        if exif_data is None:
                                            return None
                                        exif_info = {}
                                        for tag, value in exif_data.items():
                                            tag_name = TAGS.get(tag, tag)
                                            exif_info[tag_name] = value
                                        return exif_info
                                def get_gps_info(exif_info):
                                    if 'GPSInfo' in exif_info:
                                        gps_info = {}
                                        for tag, value in exif_info['GPSInfo'].items():
                                            tag_name = GPSTAGS.get(tag, tag)
                                            gps_info[tag_name] = value
                                        return gps_info
                                    return None
                                image = Image.open(image_path)
                                exif_info = get_exif_data(image)
                                
      
                                            
                                
                                if exif_info is not None:
                                    exif_datetime = None  # Initialize the variable
                                    for key, value in exif_info.items():
                                     if key == "DateTimeOriginal":
                                        exif_datetime = value
                                        print(f"Exif date: {value}")
                                        gps_info = get_gps_info(exif_info)
                                        if gps_info is not None:
                                            latitude = get_decimal_from_dms(gps_info.get('GPSLatitude', (0, 0, 0)), gps_info.get('GPSLatitudeRef', 'N'))
                                            longitude = get_decimal_from_dms(gps_info.get('GPSLongitude', (0, 0, 0)), gps_info.get('GPSLongitudeRef', 'E'))
                                            altitude = gps_info.get('GPSAltitude', None)
                                            print("Image path:", image_file)
                                            print("Latitude:", latitude)
                                            print("Longitude:", longitude)                                                                                        
                                            if altitude is not None:
                                                print(f"Altitude: {altitude} meters")
                                            latitude_string = str(latitude)
                                            longitude_string = str(longitude)
                                            numerator_str, denominator_str = latitude_string.split('/')
                                            numerator = int(numerator_str)
                                            denominator = int(denominator_str)
                                            result = numerator / denominator
                                            print("Latitude:", result)
                                            numerator_str, denominator_str = longitude_string.split('/')
                                            numerator = int(numerator_str)
                                            denominator = int(denominator_str)
                                            result = numerator / denominator
                                            print("Longitude:", result)
                                            address = get_address_from_gps_nominatim(latitude, longitude)
                                            print("Address:", address)
                                            with open(image_path, 'rb') as img_file:
                                                    image_content = img_file.read()
                                                    image_hash = hashlib.sha1(image_content).hexdigest()
                                                    print("SHA-1 Hash:", image_hash)
                                            print("=" * 60)

                            else:
                                exif_dict = piexif.load(image_path)  # Use the function piexif.load
                                exif_make = exif_dict["0th"].get(piexif.ImageIFD.Make, b"Unknown").decode("utf-8")
                                exif_model = exif_dict["0th"].get(piexif.ImageIFD.Model, b"Unknown").decode("utf-8")
                                exif_datetime = exif_dict["0th"].get(piexif.ImageIFD.DateTime, b"Unknown").decode("utf-8")
                                gps_data = exif_dict.get("GPS", {})
                                gps_altitude = gps_data.get(piexif.GPSIFD.GPSAltitude, (0, 0))
                                gps_latitude = gps_data.get(piexif.GPSIFD.GPSLatitude, [])
                                gps_longitude = gps_data.get(piexif.GPSIFD.GPSLongitude, [])
                                if gps_altitude and len(gps_altitude) >= 2 and gps_altitude[1] != 0:
                                    numerator, denominator = gps_altitude
                                    altitude = numerator / denominator
                                    gps_altitude_ref = gps_data.get(piexif.GPSIFD.GPSAltitudeRef, 0)
                                    if gps_altitude_ref == 1:
                                        altitude = -altitude
                                    altitude_in_meters = altitude if gps_altitude_ref == 0 else -altitude
                                else:
                                    altitude_in_meters = 0

                                if len(gps_latitude) >= 3 and len(gps_longitude) >= 3:
                                        gps_latitude_decimal = convert_coordinate(gps_latitude[0][0], gps_latitude[1][0], gps_latitude[2][0], gps_data.get(piexif.GPSIFD.GPSLatitudeRef, b'N'))
                                        gps_longitude_decimal = convert_coordinate(gps_longitude[0][0], gps_longitude[1][0], gps_longitude[2][0], gps_data.get(piexif.GPSIFD.GPSLongitudeRef, b'E'))
                                        address_nominatim = get_address_from_gps_nominatim(gps_latitude_decimal, gps_longitude_decimal)
                                        print("Image path:", image_path_in_zip_short)
                                        print("Exif date:", exif_datetime)
                                        print("Exif GPS Latitude:", gps_latitude_decimal)
                                        print("Exif GPS Longitude:", gps_longitude_decimal)
                                        print("Address):", address_nominatim)
                                        with open(image_path, 'rb') as img_file:
                                                    image_content = img_file.read()
                                                    image_hash = hashlib.sha1(image_content).hexdigest()
                                                    print("SHA-1 Hash:", image_hash)
                                        print("=" * 60)                               
                                else:
                                        print("Image:", image_path_in_zip_short)
                                        print("Exif date:", exif_datetime)
                                        print("Exif GPS Altitude: Not available")
                                        print("Exif GPS Latitude: Not available")
                                        print("Exif GPS Longitude: Not available")
                                        # Calculate the SHA-1 hash of the image content
                                        with open(image_path, 'rb') as img_file:
                                                    image_content = img_file.read()
                                                    image_hash = hashlib.md5(image_content).hexdigest()
                                                    print("MD5 Hash:", image_hash)
                                        print("=" * 60)


                            # Create subdirectory with EXIF DateTime name
                            if exif_datetime:
                                exif_datetime_obj = datetime.strptime(exif_datetime, "%Y:%m:%d %H:%M:%S")
                                subfolder_name = exif_datetime_obj.strftime("%Y-%m-%d")
                                output_subdirectory = os.path.join(output_directory, subfolder_name)
                                os.makedirs(output_subdirectory, exist_ok=True)
                            elif DateTimeOriginal:
                                exif_datetime_obj = datetime.strptime(DateTimeOriginal, "%Y:%m:%d %H:%M:%S")
                                subfolder_name = exif_datetime_obj.strftime("%Y-%m-%d")
                                output_subdirectory = os.path.join(output_directory, subfolder_name)
                                os.makedirs(output_subdirectory, exist_ok=True)

                            # Copy image to subdirectory
                            new_image_path = os.path.join(output_subdirectory, new_image_name)
                            #shutil.copy(image_path, new_image_path)
                            new_image_name = image_name
                            count = 1
                            while os.path.exists(os.path.join(output_subdirectory, new_image_name)):
                                base_name, extension = os.path.splitext(image_name)
                                new_image_name = f"{base_name}_{count}{extension}"
                                count += 1

                            # Copy image to subdirectory
                            new_image_path = os.path.join(output_subdirectory, new_image_name)
                            shutil.copy(image_path, new_image_path)
                            
                            all_images_report.append(f"Image path: {image_path_in_zip_short}")
                            all_images_report.append(f"Exif date: {exif_datetime}")
                            all_images_report.append(f"Exif GPS Latitude: {gps_latitude_decimal}")
                            all_images_report.append(f"Exif GPS Longitude: {gps_longitude_decimal}")
                            all_images_report.append(f"Address: {address_nominatim}")
                            all_images_report.append(f"SHA-1 Hash: {image_hash}")
                            all_images_report.append("=" * 60)

        print("Images have been copied to:", output_directory)

    # Ask user if they want to analyze another camera model
    repeat = input("Do you want to analyze another camera model? (yes/no): ").strip().lower()
    while repeat not in ["yes", "no"]:
        print("Invalid input. Please enter 'yes' or 'no'.")
        repeat = input("Do you want to analyze another camera model? (yes/no): ").strip().lower()
    if repeat == "no":
        print("Program closed.")
        break

# Save the all_images_report to report.txt
all_images_report_path = os.path.join(report_directory, f"{zip_name}_exif_image_report.txt")
with open(all_images_report_path, 'w') as report_file:
    report_file.write("\n".join(all_images_report))
