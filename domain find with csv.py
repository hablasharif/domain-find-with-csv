import streamlit as st
import re
from urllib.parse import urlparse
import requests
import random
from bs4 import BeautifulSoup
import io
import base64
import datetime
import pandas as pd
import os

# Define a list of User-Agent strings
user_agents = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:54.0) Gecko/20100101 Firefox/54.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.91 Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; AS; rv:11.0) like Gecko'
]

# Define a function to randomly select a User-Agent
def get_random_user_agent():
    return random.choice(user_agents)

# Define a function to extract and sort domains and main domains from text using regular expressions
def extract_and_sort_domains(text):
    # Regular expression pattern to match domains with various TLDs, subdomains, and URL schemes
    domain_pattern = r"(https?://)?([a-zA-Z0-9.-]+(\.[a-zA-Z]{2,}))|www\.[a-zA-Z0.9.-]+\.[a-zA-Z]{2,}"
    
    # Find all domain matches in the input text
    domains = re.findall(domain_pattern, text)
    
    # Extract, add "https://" if not present, and sort the unique domains
    sorted_domains = sorted(set(domain[0] + domain[1] if domain[0] else 'https://' + domain[1] for domain in domains))
    
    # Extract and sort the unique main domains
    main_domains = sorted(set(urlparse(domain).netloc for domain in sorted_domains))
    
    return sorted_domains, main_domains

# Define a function to fetch the title of a web page with a random User-Agent and handle getaddrinfo failed errors
def get_page_title(url):
    try:
        headers = {'User-Agent': get_random_user_agent()}  # Randomly select a User-Agent
        response = requests.get(url, headers=headers, allow_redirects=True, verify=False)  # Add verify=False to ignore SSL certificate verification
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        title_tag = soup.title
        if title_tag:
            return title_tag.string.strip(), response.url
        else:
            return "Title not available", response.url
    except requests.exceptions.RequestException as e:
        # Handle getaddrinfo failed error
        if "getaddrinfo failed" in str(e):
            return "Failed to establish a connection to the domain", url
        return "Title not available", str(e)

# Streamlit app title
st.title("Domain Extractor, Sorter, and Title Checker App")

# Input text area for user input
input_text = st.text_area("Enter text:")

# Check if the CSV file exists
csv_file_path = 'found_domains.csv'

if not os.path.exists(csv_file_path):
    # If the CSV file does not exist, create an empty DataFrame
    existing_data = pd.DataFrame(columns=["Domain", "Title", "Extracted Date"])
else:
    # If the CSV file exists, load its contents into memory
    existing_data = pd.read_csv(csv_file_path)

# Initialize a counter for serial numbers
serial_number = 1

# Add a button to extract and display domain information
if st.button("Extract Domains"):
    # Extract and sort domains and main domains from the input text
    sorted_domains, main_domains = extract_and_sort_domains(input_text)

    # Filter out invalid domains
    sorted_domains = [domain for domain in sorted_domains if not domain.startswith('https://39267-jawan.html')]

    # Display the total number of domains
    st.write(f"Total Valid Domains Found: {len(sorted_domains)}")

    # Load existing CSV data if the file exists
    existing_data = pd.read_csv(csv_file_path) if st.checkbox("Load Existing Data", False) and st.session_state.get('existing_data_loaded') is None else existing_data

    # Display domain titles one by one
    st.header("Domain Titles:")
    
    for domain in sorted_domains:
        title, redirect_url = get_page_title(domain)
        extracted_date = datetime.datetime.now().strftime("%d %B %Y %A %I:%M %p")
        row_color = random.choice(["lightgray", "lightpink", "lightblue"])

        # Display domain and title
        st.write(f"Serial: {serial_number}")
        st.write(f"Domain: {domain}")
        st.write(f"Title: {title}")
        st.write(f"Extracted Date: {extracted_date}")

        # Add data to the new_data list
        new_data = {'Domain': domain, 'Title': title, 'Extracted Date': extracted_date}
        existing_data = pd.concat([existing_data, pd.DataFrame([new_data])], ignore_index=True)
        serial_number += 1

    # If existing data is loaded, concatenate it with new data and remove duplicates
    if existing_data is not None:
        combined_df = existing_data.drop_duplicates()
        # Save the updated data to the CSV file
        combined_df.to_csv(csv_file_path, index=False)

        # Set a session state flag to indicate that existing data has been loaded
        st.session_state['existing_data_loaded'] = True

# Display the download button after the code completes its extraction
if not input_text:
    st.write("Please enter some text to extract domains and titles.")

# Add a button to download the CSV file
if st.button("Download CSV"):
    st.markdown(f'<a href="data:file/csv;base64,{base64.b64encode(existing_data.to_csv(index=False).encode()).decode()}" download="found_domains.csv">Click to download CSV file</a>', unsafe_allow_html=True)
