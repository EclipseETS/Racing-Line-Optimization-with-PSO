import csv
import json
from pyproj import Proj, transform

# !!! MAKE SURE YOU HAVE THE CORRECT UTM ZONE OR ELSE YOU WILL CRY !!!

# Define projections for longitude/latitude and UTM
wgs84 = Proj(proj='latlong', datum='WGS84')
utm_zone_16 = Proj(proj='utm', zone=16, datum='WGS84')

def lonlat_to_utm(lon, lat):
    return transform(wgs84, utm_zone_16, lon, lat)

def read_csv_to_utm(csv_file):
    track_layout_utm = []
    with open(csv_file, mode='r') as file:
        csv_reader = csv.reader(file, delimiter=';')
        next(csv_reader)  # Skip the header row
        for row in csv_reader:
            lon, lat, elevation = float(row[2]), float(row[1]), float(row[3])
            x, y = lonlat_to_utm(lon, lat)
            track_layout_utm.append([x, y, elevation])
    return track_layout_utm

def main():
    # Path to the CSV file
    csv_file = 'data/20240624162924-04039-data.csv'
    
    # Read CSV and convert to UTM
    track_layout_utm = read_csv_to_utm(csv_file)

    # Define track width (you can adjust as necessary)
    track_width = 10 # MEASURE MANUALLY ON GOOGLE EARTH
    
    # Create the JSON structure
    track_data = {
        "test_track": {
            "layout": track_layout_utm,
            "width": track_width,
        }
    }
    
    # Save to JSON file
    with open('tracks.json', 'w') as json_file:
        json.dump(track_data, json_file, indent=4)
    
    print("Track data has been successfully converted and saved to tracks.json")

if __name__ == "__main__":
    main()
