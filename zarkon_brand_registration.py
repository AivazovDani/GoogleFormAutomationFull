from selenium import webdriver # Imports the main Selenium library that controls web browsers

from selenium.webdriver.common.by import By # Imports the By class that provides different ways to find elements
# We use this to find elements by CLASS_NAME, XPATH, TAG_NAME, etc.

from selenium.webdriver.support.ui import WebDriverWait # Imports a tool to wait for elements to appear

from selenium.webdriver.support import expected_conditions as EC # Imports pre-defined conditions to wait for (like "element is present")

from selenium.webdriver.chrome.service import Service # Manages the ChromeDriver service

from selenium.webdriver.chrome.options import Options # Allows us to configure Chrome settings
# Why needed: We use this to set options like headless mode, disable notifications, etc.

from webdriver_manager.chrome import ChromeDriverManager # Automatically downloads and manages ChromeDriver

from pyairtable import Api
import time
from dotenv import load_dotenv
import os

load_dotenv()


FORM_URL = 'https://docs.google.com/forms/d/e/1FAIpQLSdsEq6vVWl2I9cyHDKTvOHvuko-YcIap1pSsJMUqOc4dkLxiQ/viewform'

AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY") # Get from https://airtable.com/account
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")  # Found in your Airtable URL
AIRTABLE_TABLE_NAME = "Brands" # The name of your
AIRTABLE_TABLE_NAME_COPIES = "Registration"

DATA = {
    "Domain": "Website/Online Presence",
    "Address (from Entity)": "Business Address",
    "EIN/VAT (from Entity)": "Tax Number/ID/EIN",
}


def get_record_by_name(name):
    try:
        api = Api(AIRTABLE_API_KEY)
        table = api.table(AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME)

        records = table.all(formula=f"{{Name}} = '{name}'")

        if records:
            print(f"✔ Found record for: {name}")
            return records[0]
        else:
            print(f"✗ No record found for: {name}")
            return None

    except Exception as e:
        print(f"✗ Error fetching record: {e}")
        return None

def clean_value(value):
    if isinstance(value, list):
        return ", ".join(str(v) for v in value)
    return value

def extract_form_data(airtable_record, other_fields=None):
    # Airtable records have structure: {'id': '...', 'fields': {...}, 'createdTime': '...'}
    fields = airtable_record.get('fields', {}) # gets the field with the data, or else returns an empty dict

    brand_name = clean_value(fields.get("Name", ""))
    legal_name = clean_value(fields.get("Name (from Entity)"))


    if other_fields:
        fields.update(other_fields)

    form_data = {} # create an empty dict to store the key, value pairs

    # Map each Airtable field to form field using FIELD_MAPPING

    # Owner name
    owner_name = clean_value(fields.get("Owner name (from Entity)", ""))


    for airtable_field, form_keyword in DATA.items():
        # Get value from Airtable (default to empty string if not found)
        value = clean_value(fields.get(airtable_field, "")) # get the filed in airtable or just return empty string if field doesn't exist

        # Store with form keyword as key
        form_data[form_keyword] = value



    # HardCoded Values
    form_data["Email"] = "harry.stone.digital@gmail.com"
    form_data["Name of Company"] = "ClickLab"
    form_data["Name of person"] = owner_name
    form_data["DBA or Brand Name"] = brand_name
    form_data["Country of Registration"] = "US"
    form_data["Your Name"] = owner_name
    form_data["Legal Company Name"] = legal_name


    return form_data

def fill_field_by_question_text(driver, question_text_partial, value):
    # here we have 3 variables -> the question on the form, the value and the driver (Chrome Browser Instance)
    try:
        time.sleep(0.5)

        questions = driver.find_elements(By.CLASS_NAME, "M7eMe") # we find the field with questions text

        question_element = None # We'll store the matching question here when we find it
        for q in questions:
            if question_text_partial.lower() in q.text.lower():
                question_element = q
                print(f"Found question: {q.text}...")
                break

        if not question_element:
            print(f"✗ Could not find question containing: {question_text_partial}")
            return False

        # Get the parent container (the div with jsmodel)
        parent = question_element.find_element(By.XPATH, "./ancestor::div[@jsmodel]")

        # Find the input or textarea in this container
        try:
            field = parent.find_element(By.TAG_NAME, "input")
        except:
            try:
                field = parent.find_element(By.TAG_NAME, "textarea")
            except:
                print(f"Could not find input/textarea for: {question_text_partial}")
                return False

        # Scroll into view
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", field)
        time.sleep(0.3)

        # Clear and fill
        field.click()  # Click first to focus
        field.clear()
        field.send_keys(str(value))

        print(f"✓ Filled: {question_text_partial} = {value}")
        return True

    except Exception as e:
        print(f"✗ Error filling '{question_text_partial}': {e}")
        return False


def fill_form_with_data(driver, form_data):
    print("Filling fields...")
    print("-" * 70)

    filled_count = 0 # Create counter variable, starting at 0. Why: Track how many fields we successfully fill


    for question_keyword, value in form_data.items(): # we loop through the new dict containing the
        if value:  # Only fill if there's a value
            if fill_field_by_question_text(driver, question_keyword, value): # we call the fill field function
                filled_count += 1
            time.sleep(0.5)

    
    fields = driver.find_elements(By.CSS_SELECTOR, "input[type='text'], input[type='email']")
    fields[0].send_keys("harry.stone.digital@gmail.com")

    print("-" * 70)
    print(f"\n✓ Successfully filled {filled_count}/{len(form_data)} fields!\n")

    return filled_count


def process_single_record(record, other_fields):
    # record_id = record['id']
    #
    # print("\n" + "=" * 70)
    # print(f"PROCESSING RECORD: {record_id}")
    # print("=" * 70 + "\n")

    # Extract form data from Airtable record
    form_data = extract_form_data(record, other_fields)

    # Show what we're about to fill
    print("Data from Airtable:")
    for key, value in form_data.items():
        print(f"  {key}: {str(value)}")
    print()

    # Setup Chrome
    print("Setting up browser...")
    chrome_options = Options()
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--disable-software-rasterizer')
    chrome_options.add_argument('--disable-extensions')
    chrome_options.add_argument('--remote-debugging-port=9222')
    chrome_options.add_argument('--window-size=1920,1080')


    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        # Open form
        print("Opening form...")
        driver.get(FORM_URL)
        

        # Wait for form to load
        print("Waiting for form to load...")
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CLASS_NAME, "M7eMe"))
        )
        time.sleep(2)

        print("✓ Form loaded!\n")

        # Fill the form
        filled_count = fill_form_with_data(driver, form_data)

        if filled_count > 0:
            # Give user time to review
            print("Review the form (5 seconds)...")
            time.sleep(5)


        else:
            print("✗ No fields were filled. Skipping submission.")

        time.sleep(180)

    finally:
        driver.quit()
        print("Browser closed.\n")

def get_copies(name):
    api = Api(AIRTABLE_API_KEY)
    table = api.table(AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME_COPIES)

    record = table.all(formula=f"{{Name}} = '{name}'")

    if record:
        return record[0]['fields']
    return None


def main_zbr(value1, value2):
    print("\n" + "=" * 70)
    print("GOOGLE FORM AUTO-FILLER WITH AIRTABLE")
    print("=" * 70 + "\n")

    name = value1.strip()
    copies_name = value2.strip()

    record = get_record_by_name(name)
    other_fields = get_copies(copies_name)

    if record:
        process_single_record(record, other_fields)
    else:
        print("No record found. Exiting.")



if __name__ == "__main__":
    main_zbr()
    
