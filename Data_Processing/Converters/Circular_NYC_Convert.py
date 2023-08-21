import csv
from bs4 import BeautifulSoup
import requests
import usaddress
import urllib.parse
import os
import datetime
import uuid


def get_address_from_name(api_key, business_name):
    print(f"Fetching address for business: {business_name}")
    endpoint = f"https://maps.googleapis.com/maps/api/place/findplacefromtext/json?input={business_name}&inputtype=textquery&fields=formatted_address&key={api_key}"
    response = requests.get(endpoint)
    data = response.json()

    if data['status'] == "OK" and data['candidates']:
        address = data['candidates'][0]['formatted_address']
        print(f"Successfully fetched address for {business_name}: {address}")
        return address
    print(f"Failed to fetch address for business: {business_name}")
    return None


def parse_address(address):
    try:
        parsed_address, _ = usaddress.tag(address)
        standardized_address = []

        # Reconstruct the address in a standardized format
        if 'AddressNumber' in parsed_address:
            standardized_address.append(parsed_address['AddressNumber'])
        if 'StreetName' in parsed_address:
            standardized_address.append(parsed_address['StreetName'])
        if 'StreetNamePostType' in parsed_address:
            standardized_address.append(parsed_address['StreetNamePostType'])
        if 'PlaceName' in parsed_address:
            standardized_address.append(parsed_address['PlaceName'])
        if 'StateName' in parsed_address:
            standardized_address.append(parsed_address['StateName'])
        if 'ZipCode' in parsed_address:
            standardized_address.append(parsed_address['ZipCode'])

        return ', '.join(standardized_address)
    except usaddress.RepeatedLabelError:
        print(f"Failed to parse address: {address}. Using original address.")
        return address


def extract_city_from_address(address):
    try:
        parsed_address, _ = usaddress.tag(address)
        return parsed_address.get('PlaceName', None)
    except usaddress.RepeatedLabelError:
        print(f"Failed to extract city from address: {address}. Using original address.")
        return None

def extract_state_from_address(address):
    try:
        parsed_address, _ = usaddress.tag(address)
        return parsed_address.get('StateName', None)
    except usaddress.RepeatedLabelError:
        return None


def circular_kml_to_csv(api_key, kml_file_path, output_dir):
    print(f"Starting KML to CSV conversion.")
    print(f"Reading KML file: {kml_file_path}")
    with open(kml_file_path, "r", encoding="utf-8") as file:
        soup = BeautifulSoup(file, "xml")

    data = []
    total_placemarks = len(soup.find_all("Placemark"))
    print(f"Found {total_placemarks} Placemark entries in the KML file.")

    for idx, placemark in enumerate(soup.find_all("Placemark"), 1):
        print(f"\nProcessing Placemark {idx} of {total_placemarks}")

        name = placemark.find("name").text.strip() if placemark.find("name") else ""
        print(f"Business name: {name}")

        # Extract folder name
        folder = placemark.find_parent("Folder")
        folder_name = folder.find("name").text.strip() if folder and folder.find("name") else "Unknown"

        address_tag = placemark.find("address")
        address = address_tag.text.strip() if address_tag else get_address_from_name(api_key, name)

        # If the address is not found or is None, skip this Placemark
        if not address:
            print(f"Skipping {name} as no address was found.")
            continue

        address = parse_address(address)  # Parsing the address

        # Check if the address mostly contains just the city/borough, state, and zipcode
        if address and len(address.split(',')) <= 3:
            address = name + ", " + address

        # Extract state
        state = extract_state_from_address(address)

        # Fetch website and phone number (This assumes the KML might have tags named 'website' and 'phoneNumber')
        website = placemark.find("Data", {"name": "Website"}).value.text if placemark.find("Data", {
            "name": "Website"}) else None
        phone_number = placemark.find("Data", {"name": "Phone"}).value.text if placemark.find("Data", {
            "name": "Phone"}) else None

        # If website isn't available, default to a Google search link for the business name
        if not website or website.lower() == "not available":
            website = f"https://www.google.com/search?q={name}"

        city = extract_city_from_address(address)
        source_file_name = kml_file_path.split('/')[-1]

        data.append([name, address, city, state, website, phone_number, folder_name, source_file_name])

    # Extract base name from input filename
    base_name = os.path.basename(kml_file_path).split(".")[0]

    # Generate unique filename using base name
    current_time = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    random_str = uuid.uuid4().hex[:6]  # get a random string of 6 characters
    csv_file_name = "circular_orgs.csv"

    print("\nWriting extracted data to CSV.")
    with open(output_dir + csv_file_name, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(
            ["Name", "Address", "City", "State", "Website", "Phone Number", "Folder Name", "Source File Name"])
        writer.writerows(data)

    print(f"Data extraction complete. Saved to {output_dir + csv_file_name}")
    return data


