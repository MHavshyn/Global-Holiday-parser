import requests
import json
import argparse
from datetime import datetime
from typing import List, Dict, Any
from dotenv import load_dotenv
import os

load_dotenv()

API_KEY = os.getenv('CALENDARIFIC_API_KEY')
BASE_URL = 'https://calendarific.com/api/v2/holidays'

RED = '\033[91m'
RESET = '\033[0m'


def fetch_holidays(country: str, year: int) -> List[Dict[str, Any]]:
    holidays = []
    params = {
        'api_key': API_KEY,
        'country': country,
        'year': year
    }

    try:
        response = requests.get(BASE_URL, params=params)
        response.raise_for_status()
        data = response.json()

        if 'response' in data and 'holidays' in data['response']:
            holidays.extend(data['response']['holidays'])
        else:
            print(f"No holidays found for country {country} in year {year}.")

    except requests.exceptions.HTTPError as http_err:
        print(f"{RED}HTTP error occurred: {http_err}{RESET}")
    except requests.exceptions.RequestException as req_err:
        print(f"{RED}Request error occurred: {req_err}{RESET}")
    except Exception as err:
        print(f"{RED}An unexpected error occurred: {err}{RESET}")

    return holidays


def filter_holidays_by_date(holidays: List[Dict[str, Any]], start_date: datetime, end_date: datetime) -> List[
    Dict[str, Any]]:
    filtered_holidays = []
    for holiday in holidays:
        try:
            holiday_date = datetime(
                year=holiday['date']['datetime']['year'],
                month=holiday['date']['datetime']['month'],
                day=holiday['date']['datetime']['day']
            )
            if start_date <= holiday_date <= end_date:
                filtered_holidays.append(holiday)
        except KeyError as key_err:
            print(f"{RED}Missing key in holiday data: {key_err}{RESET}")
        except Exception as err:
            print(f"{RED}An error occurred while processing holiday data: {err}{RESET}")

    return filtered_holidays


def save_to_file(filename: str, data: List[Dict[str, Any]]) -> None:
    try:
        with open(filename, 'w') as file:
            for holiday in data:
                file.write(json.dumps(holiday) + '\n')
        print(f"Data successfully saved to {filename}")
    except IOError as io_err:
        print(f"{RED}Failed to write to file {filename}: {io_err}{RESET}")
    except Exception as err:
        print(f"{RED}An unexpected error occurred while saving data to file: {err}{RESET}")


def validate_dates(start_date: str, end_date: str) -> (datetime, datetime):
    try:
        start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
        end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
        if start_date_obj > end_date_obj:
            raise ValueError("Start date must not be after end date.")
        return start_date_obj, end_date_obj
    except ValueError as val_err:
        print(f"{RED}Invalid date format or range. Please use YYYY-MM-DD. Error: {val_err}{RESET}")
        raise


def main(countries_list: List[str], start_date: str, end_date: str) -> None:
    try:
        start_date_obj, end_date_obj = validate_dates(start_date, end_date)
    except ValueError:
        return

    for country in countries_list:
        all_holidays = []
        start_year = start_date_obj.year
        end_year = end_date_obj.year

        for year in range(start_year, end_year + 1):
            holidays = fetch_holidays(country, year)
            all_holidays.extend(holidays)

        filtered_holidays = filter_holidays_by_date(all_holidays, start_date_obj, end_date_obj)
        filename = f"{country}_{start_date_obj.strftime('%d-%m-%Y')}_{end_date_obj.strftime('%d-%m-%Y')}.txt"
        save_to_file(filename, filtered_holidays)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Fetch holidays for given countries between start and end dates.')
    parser.add_argument('countries', type=str, nargs='+', help='List of country codes in ISO 3166 format (e.g., UA US GB)')
    parser.add_argument('start_date', type=str, help='Start date in YYYY-MM-DD format')
    parser.add_argument('end_date', type=str, help='End date in YYYY-MM-DD format')
    args = parser.parse_args()

    main(args.countries, args.start_date, args.end_date)