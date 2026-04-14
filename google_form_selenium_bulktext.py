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


FORM_URL = 'https://docs.google.com/forms/d/e/1FAIpQLSeonX3eiCek1yBUPN9aXhMkwZG9FB76-L5kJPqYiPiyp5nYzQ/viewform'

AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")  # Get from https://airtable.com/account
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")  # Found in your Airtable URL
AIRTABLE_TABLE_NAME = "Brands" # The name of your
AIRTABLE_TABLE_NAME_COPIES = "Registration"

DATA = {
    "Use-Case": "Campaign Description",
    "Safe Page URL": "Opt-in URL",
    "Message Flow": "Call to Action/Message Flow",
    "Opt-In Screenshot":"Opt-in Workflow Image URL",

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
    
    # Your name and company name
    owner_name = clean_value(fields.get("Owner name (from Entity)", ""))
    name_company = clean_value(fields.get("Name", ""))

    phone_number = clean_value(fields.get("Phone (from Entity)", ""))

    email = f"info@{name_company.lower()}.com"

    domain = clean_value(fields.get("Domain", ""))


    if other_fields:
        fields.update(other_fields)

    form_data = {} # create an empty dict to store the key, value pairs

    # Map each Airtable field to form field using FIELD_MAPPING


    for airtable_field, form_keyword in DATA.items():
        # Get value from Airtable (default to empty string if not found)
        value = clean_value(fields.get(airtable_field, "")) # get the filed in airtable or just return empty string if field doesn't exist

        # Store with form keyword as key
        form_data[form_keyword] = value


    registered_copies = clean_value(fields.get("Registered copies", ""))

    if registered_copies:
        message = []
    
        if '\n' in registered_copies:
            messages = registered_copies.split('\n')
        elif '|' in registered_copies:
            messages = registered_copies.split('|')
        elif ';' in registered_copies:
            messages = registered_copies.split(';')
        else:
            messages = [registered_copies]

        form_data["Sample Message 1"] = messages[0].strip()
        form_data["Sample Message 2"] = messages[3].strip()
        form_data["Sample Message 3"] = messages[2].strip()
    
    else:
        form_data["Sample Message 1"] = ""
        form_data["Sample Message 2"] = ""
        form_data["Sample Message 3"] = ""

    # HardCoded Values
    form_data["Volume of messages"] = "100k"
    form_data["Opt-in Keyword(s)"] = "Join"
    form_data["Opt-in message"] = f"Thank you for joining {name_company} SMS alerts! You'll now receive exclusive updates and notifications. Reply HELP for assistance. Msg & data rates may apply."
    form_data["Opt-out Keyword"] = "Stop"
    form_data["Opt-out message"] = f"You have successfully unsubscribed from {name_company} SMS alerts. We're sorry to see you go. If you change your mind, text JOIN to resubscribe. Msg & data rates may apply."
    form_data["Help Keyword"] = "Help"
    form_data["Help message"] = f"For assistance with {name_company} SMS alerts, please contact our customer service at  {phone_number} or email us at {email}. Msg & data rates may apply"
    form_data["Customer Service email"] = f"{email}  {phone_number}"
    form_data["Link to Privacy Policy page"] = f"https://{name_company.lower()}.com/privacy-policy/index.html"
    form_data["Link to Terms and Condition page"] = f"https://{name_company.lower()}.com/terms-and-conditions/index.html"
    form_data["Your name and company"] = f"{owner_name}  {name_company}"
    form_data["List all the Short links"] = f"{domain}/log\n{domain}"
    form_data["Frequency of Messages"] = "4"




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
                print(f"Found dropdown question: {q.text}...")
                break

        if not question_element:
            print(f"✗ Could not find dropdown question: {question_text_partial}")
            return False

        parent = question_element.find_element(By.XPATH, "./ancestor::div[@jsmodel]")

        # Find and click the dropdown to open it
        dropdown = parent.find_element(By.CSS_SELECTOR, "div[role='listbox']")
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", dropdown)
        time.sleep(0.3)
        dropdown.click()
        time.sleep(0.5)

        # Wait for options to appear
        options = WebDriverWait(driver, 5).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div[role='option']"))
        )

        # Find and click the matching option
        for option in options:
            if option_text.lower() in option.text.lower():
                option.click()
                print(f"✓ Selected dropdown option: {option_text}")
                return True

        print(f"✗ Could not find option: {option_text}")
        return False

    except Exception as e:
        print(f"✗ Error selecting dropdown: {e}")
        return False

def fill_form_with_data(driver, form_data, dropdown):
    print("Filling fields...")
    print("-" * 70)

    filled_count = 0 # Create counter variable, starting at 0. Why: Track how many fields we successfully fill


    for question_keyword, value in form_data.items(): # we loop through the new dict containing the
        if value:  # Only fill if there's a value
            if fill_field_by_question_text(driver, question_keyword, value): # we call the fill field function
                filled_count += 1
            time.sleep(0.5)
    
    # Select the dropdown menu
    if select_dropdown_by_question(driver, "Type of number", dropdown):  # Use the value from HTML!
        filled_count += 1
    time.sleep(0.5)

    # Select the Dropdown (hardcoded)
    try:
        questions = driver.find_elements(By.CLASS_NAME, "M7eMe")
        
        for q in questions:
            if "Use Case" in q.text:
                parent = q.find_element(By.XPATH, "./ancestor::div[@jsmodel]")
                dropdown = parent.find_element(By.CSS_SELECTOR, "div[role='listbox']")
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", dropdown)
                time.sleep(0.3)
                dropdown.click()
                time.sleep(0.5)

                options = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div[role='option']"))
                )
                
                for option in options:
                        
                    # Hardcoded: Check "Marketing" and "Account"
                    if "Account Notification" in option.text:
                        option.click()
                        print(f"✔ Checked: {option.text}")
                        time.sleep(2)
                        break


                        
                filled_count += 1
                break

    except Exception as e:
        print(f"✗ Error selecting checkboxes: {e}")

    # Select the radio button (hardcoded)
    try:
        for q in questions:
            if "split your traffic" in q.text:  # Change to match your radio question
                parent = q.find_element(By.XPATH, "./ancestor::div[@jsmodel]")
                radios = parent.find_elements(By.CSS_SELECTOR, "div[role='radio']")
                
                for radio in radios:
                    try:
                        label = radio.find_element(By.XPATH, 
                            "./ancestor::div[contains(@class, 'nWQGrd')]//span[@class='aDTYNe snByac OvPDhc OIC90c']")
                        
                        # Hardcoded: Select "Yes"
                        if "Yes" in label.text:
                            radio.click()
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


def process_single_record(record, other_fields, dropdown):
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
    service = Service('/usr/bin/chromedriver')
    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        # Open form
        print("Opening form...")
        driver.get(FORM_URL)

        # Wait for form to load
        print("Waiting for form to load...")
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.TAG_NAME, "form"))
        )
        time.sleep(1)

        print("Handeling email gate")
        try:
            email_field = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='email']"))
            )
        
            email_field.click()
            email_field.clear()
            email_field.send_keys("harry.stone.digital@gmail.com")
            time.sleep(5)

            print("Email submitted, moving to main form...")

            WebDriverWait(driver, 15).until(
                EC.presence_of_all_elements_located((By.CLASS_NAME, "M7eMe"))
            )

            time.sleep(2)
            print("Main form loaded")
        
        except Exception as e:
            print(f"Error on email gate: {e}")


        # Fill the form
        filled_count = fill_form_with_data(driver, form_data, dropdown)

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


def main_bulk_text(value1, value2, number_type):
    print("\n" + "=" * 70)
    print("GOOGLE FORM AUTO-FILLER WITH AIRTABLE")
    print("=" * 70 + "\n")

    name = value1.strip()
    copies_name = value2.strip()
    dropdown = number_type

    record = get_record_by_name(name)
    other_fields = get_copies(copies_name)

    if record:
        process_single_record(record, other_fields, dropdown)
    else:
        print("No record found. Exiting.")



if __name__ == "__main__":
    main_bulk_text()
    
