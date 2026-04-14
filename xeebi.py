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


FORM_URL = 'https://docs.google.com/forms/d/e/1FAIpQLSfUdXosJNuA4kT04KAsjAoH9TFpo2rJlbgC_zrrcDRqPudHQA/viewform'

AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")  # Get from https://airtable.com/account
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")  # Found in your Airtable URL
AIRTABLE_TABLE_NAME = "Brands" # The name of your
AIRTABLE_TABLE_NAME_COPIES = "Registration"

DATA = {
    "EIN/VAT (from Entity)":"Tax Number/ID/EIN",
    "Name (from Entity)":"Legal company name",
    "Domain":"Website",
    "Phone (from Entity)":"Phone number",
    "Registered copies": "Example Messages",

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
    form_data = {} # create an empty dict to store the key, value pairs

    
    # Your name and company name
    owner_name = clean_value(fields.get("Owner name (from Entity)", ""))
    if owner_name:
        parts = owner_name.split(" ", 1)
        form_data["First name"] = parts[0]
        form_data["Last name"] = parts[1]

    name_company = clean_value(fields.get("Name", ""))
    email = f"info@{name_company.lower()}.com"
    form_data["Email"] = email

    phone_number = clean_value(fields.get("Phone (from Entity)", ""))

    address = clean_value(fields.get("Address (from Entity)", ""))

    
    if address:
        parts = address.split("\n")

        # Street
        if len(parts) > 0:
            form_data["Address / Street"] = parts[0]

        # City, State ZIP
        if len(parts) > 1:
            other_parts = parts[1].split(", ")

            if len(other_parts) > 0:
                form_data["City"] = other_parts[0]

            if len(other_parts) > 1:
                new_parts = other_parts[1].split(" ")

                if len(new_parts) > 0:
                    form_data["State / Region"] = new_parts[0]

                if len(new_parts) > 1:
                    form_data["Postal / Zip code"] = new_parts[1]

        


    if other_fields:
        fields.update(other_fields)


    # Map each Airtable field to form field using FIELD_MAPPING


    for airtable_field, form_keyword in DATA.items():
        # Get value from Airtable (default to empty string if not found)
        value = clean_value(fields.get(airtable_field, "")) # get the filed in airtable or just return empty string if field doesn't exist

        # Store with form keyword as key
        form_data[form_keyword] = value

    # HardCoded Values
    form_data["DBA or Brand name"] = name_company
    form_data["Country of registration"] = "US"
    form_data["Welcome Message"] = f"Thank you for joining {name_company} SMS alerts! You'll now receive exclusive updates and notifications. Reply HELP for assistance. Msg & data rates may apply."
    form_data["Opt-Out MTs"] = f"You have successfully unsubscribed from {name_company} SMS alerts. We're sorry to see you go. If you change your mind, text JOIN to resubscribe. Msg & data rates may apply."
    form_data["Help MT"] = f"For assistance with {name_company} SMS alerts, please contact our customer service at  {phone_number} or email us at {email}. Msg & data rates may apply"





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

def select_dropdown_by_question(driver, question_text_partial, option_text):
    try:
        time.sleep(0.5)
        questions = driver.find_elements(By.CLASS_NAME, "M7eMe")

        question_element = None
        for q in questions:
            if question_text_partial.lower() in q.text.lower():
                question_element = q
                print(f"Found radio question: {q.text}...")
                break

        if not question_element:
            print(f"✗ Could not find dropdown question: {question_text_partial}")
            return False

        parent = question_element.find_element(By.XPATH, "./ancestor::div[@jsmodel]")
        
        radio_options = parent.find_elements(By.CSS_SELECTOR, "div[role='radio']")

        for radio in radio_options:
            try:
                span = radio.find_element(By.CSS_SELECTOR, "span.aDTYNe")
                label = span.text
            except:
                label = radio.get_attribute("data-value") or ""
            
            if option_text.lower() in label.lower():
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", radio)
                time.sleep(0.3)
                radio.click()
                print(f"✓ Selected radio: {label}")
                return True
                
        return False

    except Exception as e:
        print(f"✗ Error selecting dropdown: {e}")
        return False


def fill_email_field(driver, value):
    try:
        time.sleep(0.5)
        
        # Find email input directly, no ancestor search needed
        field = driver.find_element(By.CSS_SELECTOR, "input[type='email']")
        
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", field)
        time.sleep(0.3)
        
        field.click()
        field.clear()
        field.send_keys(str(value))
        
        print(f"✓ Filled email: {value}")
        return True

    except Exception as e:
        print(f"✗ Error filling email: {e}")
        return False

def fill_form_with_data(driver, form_data, radio):
    print("Filling fields...")
    print("-" * 70)

    filled_count = 0 # Create counter variable, starting at 0. Why: Track how many fields we successfully fill

    fields = driver.find_elements(By.CSS_SELECTOR, "input[type='email']")
    for field in fields:
        print(field.get_attribute("value"))
        print(field.get_attribute("name"))

    fill_email_field(driver, form_data.get("Email", ""))

    for question_keyword, value in form_data.items(): # we loop through the new dict containing the
        if value:  # Only fill if there's a value
            if question_keyword == "Email":
                continue
            if fill_field_by_question_text(driver, question_keyword, value): # we call the fill field function
                filled_count += 1
            time.sleep(0.5)
    
    # Select the radio button
    if select_dropdown_by_question(driver, "Vertical type", radio):  # Use the value from HTML!
        filled_count += 1
    time.sleep(0.5)


    # Select the radio button (hardcoded)
    try:

        questions = driver.find_elements(By.CLASS_NAME, "M7eMe")

        for q in questions:
            if "split your traffic" in q.text:  # Change to match your radio question
                parent = q.find_element(By.XPATH, "./ancestor::div[@jsmodel]")
                radios = parent.find_elements(By.CSS_SELECTOR, "div[role='radio']")
                
                for r in radios:
                    try:
                        label = r.find_element(By.XPATH, 
                            "./ancestor::div[contains(@class, 'nWQGrd')]//span[@class='aDTYNe snByac OvPDhc OIC90c']")
                        
                        # Hardcoded: Select "Yes"
                        if "Private Profit" in label.text:
                            r.click()
                            print(f"✓ Selected: {label.text}")
                            time.sleep(0.2)
                            filled_count += 1
                            break
                    except:
                        continue
                break
    except Exception as e:
        print(f"✗ Error selecting radio: {e}")

    print("-" * 70)
    print(f"\n✓ Successfully filled {filled_count}/{len(form_data)} fields!\n")

    return filled_count


def process_single_record(record, other_fields, radio):
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
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    # Keep these exactly as they are
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        # Open form
        print("Opening form...")
        driver.get(FORM_URL)
        time.sleep(15)


        # Wait for form to load
        print("Waiting for form to load...")
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CLASS_NAME, "M7eMe"))
        )
        time.sleep(2)

        print("✓ Form loaded!\n")

        # Fill the form
        filled_count = fill_form_with_data(driver, form_data, radio)

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


def main_xeebi(value1, value2, number_type):
    print("\n" + "=" * 70)
    print("GOOGLE FORM AUTO-FILLER WITH AIRTABLE")
    print("=" * 70 + "\n")

    name = value1.strip()
    copies_name = value2.strip()
    radio = number_type

    record = get_record_by_name(name)
    other_fields = get_copies(copies_name)

    if record:
        process_single_record(record, other_fields, radio)
    else:
        print("No record found. Exiting.")



if __name__ == "__main__":
    main_xeebi()
    
