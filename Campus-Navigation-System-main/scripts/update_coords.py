#!/usr/bin/env python3
"""
Script to geocode place names found in map_urls.csv using Google Geocoding API
and write a `coords.csv` file with the canonical latitude and longitude for each
unique place name.

Usage:
  Set environment variable `GOOGLE_API_KEY` or pass the key as argument.
  python scripts/update_coords.py --key YOUR_KEY

This script requires the `requests` package.
"""
import os
import csv
import argparse
import requests
from urllib.parse import quote_plus


def collect_place_names(csv_path='map_urls.csv'):
    names = set()
    if not os.path.exists(csv_path):
        print(f"{csv_path} not found.")
        return names

    with open(csv_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            src = row.get('SOURCE')
            dst = row.get('DESTINATION')
            if src:
                names.add(src.strip())
            if dst:
                names.add(dst.strip())
    return names


def geocode_place(place, api_key):
    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={quote_plus(place)}&key={api_key}"
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    if data.get('status') != 'OK' or not data.get('results'):
        return None
    loc = data['results'][0]['geometry']['location']
    return loc['lat'], loc['lng']


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--key', help='Google Geocoding API key')
    parser.add_argument('--in', dest='infile', default='map_urls.csv')
    parser.add_argument('--out', dest='outfile', default='coords.csv')
    args = parser.parse_args()

    api_key = args.key or os.environ.get('GOOGLE_API_KEY')
    if not api_key:
        print('Google API key required via --key or GOOGLE_API_KEY environment variable')
        return

    names = collect_place_names(args.infile)
    if not names:
        print('No place names found to geocode.')
        return

    results = []
    for name in sorted(names):
        try:
            latlng = geocode_place(name, api_key)
            if latlng:
                lat, lng = latlng
                print(f"{name}: {lat}, {lng}")
                results.append((name, lat, lng))
            else:
                print(f"No result for {name}")
        except Exception as e:
            print(f"Error geocoding {name}: {e}")

    if results:
        with open(args.outfile, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['NAME', 'LAT', 'LON'])
            for r in results:
                writer.writerow([r[0], r[1], r[2]])
        print(f'Wrote {len(results)} entries to {args.outfile}')


if __name__ == '__main__':
    main()
