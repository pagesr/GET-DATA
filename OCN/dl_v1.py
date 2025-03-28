import requests
from bs4 import BeautifulSoup
import re
import os
import time

# Set the year here
year = 2013  # Change this to the desired year

# Loop through all months
for month in range(1, 13):
    # URL for the repository
    url = f"https://www.ncei.noaa.gov/data/climate-forecast-system/access/operational-9-month-forecast/6-hourly-ocean/{year}/{year}{month:02d}/{year}{month:02d}01/{year}{month:02d}0100/"

    # Directory to save downloaded files
    download_dir = f'./grb_file/{year}/{month:02d}01'
    os.makedirs(download_dir, exist_ok=True)
    print(f"URL: {url}")
    print(f"Download directory: {download_dir}")

    # Log file for download failures
    log_file = './download_failures.log'

    # Minimum file size to consider a file as "complete" (in bytes)
    min_file_size = 9 * 1024 * 1024  # 9MB

    # Function to download a file from a given URL with retry logic
    def download_file(file_url, download_path, max_retries=3):
        file_name = os.path.join(download_path, file_url.split("/")[-1])
        attempts = 0
        success = False

        # Check if the file already exists and its size
        if os.path.exists(file_name):
            file_size = os.path.getsize(file_name)
            if file_size > min_file_size:
                print(f"File {file_name} already exists and is larger than {min_file_size / (1024 * 1024)}MB. Skipping download.")
                return
            else:
                print(f"File {file_name} exists but is smaller than {min_file_size / (1024 * 1024)}MB. Downloading again.")

        while attempts < max_retries and not success:
            try:
                response = requests.get(file_url, stream=True, timeout=10)
                response.raise_for_status()  # Check for HTTP errors

                with open(file_name, 'wb') as file:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            file.write(chunk)
                print(f"Downloaded: {file_name}")
                success = True

            except (requests.exceptions.RequestException, IOError) as e:
                attempts += 1
                print(f"Attempt {attempts} failed for {file_name}. Retrying...")
                time.sleep(2)  # Wait before retrying

        if not success:
            print(f"Failed to download {file_name} after {max_retries} attempts. Logging to {log_file}.")
            with open(log_file, 'a') as log:
                log.write(f"{file_url}\n")

    # Get the HTML content of the page
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    # Regular expression to match files like "ocnf*.grb2" but not ".md5" or other extensions
    pattern = re.compile(r'ocnf.*\.grb2$')

    # Find all the files that match the pattern
    file_links = [link.get('href') for link in soup.find_all('a', href=True) if pattern.match(link.get('href'))]

    # Download each file with retries
    for file_link in file_links:
        file_url = url + file_link
        download_file(file_url, download_dir)

