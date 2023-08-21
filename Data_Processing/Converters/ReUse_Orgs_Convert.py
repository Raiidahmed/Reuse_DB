import csv
from bs4 import BeautifulSoup
import requests
import usaddress
import urllib.parse
import os
import datetime
import uuid

def get_place_details(api_key, business_name):
    # First, use the Place Search to find the place_id of the business
    search_url = f"https://maps.googleapis.com/maps/api/place/findplacefromtext/json?input={business_name}&inputtype=textquery&fields=place_id&key={api_key}"

    response = requests.get(search_url)
    result = response.json()

    if result.get("status") == "OK":
        place_id = result["candidates"][0]["place_id"]

        # Use the place_id to get detailed information about the place
        details_url = f"https://maps.googleapis.com/maps/api/place/details/json?place_id={place_id}&fields=formatted_address,formatted_phone_number&key={api_key}"

        details_response = requests.get(details_url)
        details_result = details_response.json()

        if details_result.get("status") == "OK":
            address = details_result["result"].get("formatted_address", None)
            phone_number = details_result["result"].get("formatted_phone_number", None)
            return address, phone_number
        else:
            return None, None
    else:
        return None, None


def parse_address(address):
    try:
        parsed_address, _ = usaddress.tag(address)
        return ', '.join([value for key, value in parsed_address.items()])
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


def reuse_kml_to_csv(api_key, kml_file_path, output_dir):
    print(f"Starting KML to CSV conversion.")
    print(f"Reading KML file: {kml_file_path}")
    with open(kml_file_path, "r", encoding="utf-8") as file:
        soup = BeautifulSoup(file, "xml")

    data = []
    total_placemarks = len(soup.find_all("Placemark"))
    print(f"Found {total_placemarks} Placemark entries in the KML file.")

    for idx, placemark in enumerate(soup.find_all("Placemark"), 1):
        print(f"\nProcessing Placemark {idx} of {total_placemarks}")

        name = placemark.find("Data", {"name": "Org"}).value.text
        print(f"Business name: {name}")

        # Extract folder name
        folder = placemark.find_parent("Folder")
        folder_name = folder.find("name").text.strip() if folder and folder.find("name") else "Unknown"

        address_tag = placemark.find("address")
        address, phone_number = address_tag.text.strip() if address_tag else get_place_details(api_key, name)

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
        website = placemark.find("Data", {"name": "Link"}).value.text if placemark.find("Data", {
            "name": "Link"}) else None


        # If website isn't available, default to a Google search link for the business name
        if not website or website.lower() == "Not Available":
            website = f"https://www.google.com/search?q={name}"

        city = extract_city_from_address(address)
        source_file_name = kml_file_path.split('/')[-1]

        # Skip entries that don't have a state or website
        if not state or not website:
            print(f"Skipping {name} as it lacks a state or website entry.")
            continue

        data.append([name, address, city, state, website, phone_number, folder_name, source_file_name])

    # Extract base name from input filename
    base_name = os.path.basename(kml_file_path).split(".")[0]

    # Generate unique filename using base name
    current_time = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    random_str = uuid.uuid4().hex[:6]  # get a random string of 6 characters
    csv_file_name = "reuse_orgs.csv"

    print("\nWriting extracted data to CSV.")
    with open(output_dir + csv_file_name, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(
            ["Name", "Address", "City", "State", "Website", "Phone Number", "Folder Name", "Source File Name"])
        writer.writerows(data)

    print(f"Data extraction complete. Saved to {output_dir + csv_file_name}")
    return data

