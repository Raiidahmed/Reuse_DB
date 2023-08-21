from Data_Processing.Converters.Circular_NYC_Convert import circular_kml_to_csv
from Data_Processing.Converters.ReUse_Orgs_Convert import reuse_kml_to_csv
from datetime import datetime
import os  # Import the os module for directory handling
import csv

def merge_arrays(arrays, header):
    if not arrays or not header:
        raise ValueError("Both the arrays and header must be provided.")

    # Start with the new header
    merged_array = [header]

    # Add the content of all arrays
    for arr in arrays:
        merged_array.extend(arr)

    return merged_array


def save_to_csv(data, output_filename):
    with open(output_filename, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerows(data)
        print(f"Data saved to {output_filename}")

api_key = os.environ["GOOGLE_API_KEY"]
header = ["Name", "Address", "City", "State", "Website", "Phone Number", "Category", "Source"]

# Create a new directory named after the unique filename
output_dir = f"./Output/Output_{datetime.now().strftime('%Y%m%d_%H%M%S')}/"
os.makedirs(output_dir, exist_ok=True)  # Creates the directory if it doesn't exist

Circular_Data = circular_kml_to_csv(api_key, "Data/Circular NYC.kml", output_dir)  # Save outputs in the new directory
Reuse_Data = reuse_kml_to_csv(api_key, "Data/ReUse Orgs.kml", output_dir)  # Save outputs in the new directory

merged_df = merge_arrays([Circular_Data, Reuse_Data], header)
save_to_csv(merged_df, output_dir + "merged.csv")  # Save the merged CSV in the new directory
