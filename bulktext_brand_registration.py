from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By 
import time
from pyairtable import Api
from selenium.webdriver.chrome.options import Options
from dotenv import load_dotenv
import os


URL_FORM = 'https://docs.google.com/forms/d/1FqCs-DbBLkxU-kYMv3CSQIyjprbZ3zhSVW54Toq3u4k/preview'



load_dotenv()

AIRTABLE_API = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
AIRTABLE_TABLE_NAME = 'Brands'
AIRTABLE_TABLE_NAME_COPIES = 'Registration'

DATA = {
    # "Our Airtable field":"The question in the form where we need to fill it"
    "Name (from Entity)":"Legal Company Name",
    "EIN/VAT (from Entity)":"Tax Number/ID/EIN",
    "Address (from Entity)":"Business Address",
    "Domain":"Website/Online Presence",
    "Owner name (from Entity)":"Your Name"
}

# Airtable Data -> how it's given to us
"""{
    'id': 'recXXXXXXXXXXXXXX',
    'createdTime': '2024-01-01T00:00:00.000Z',
    'fields': {
        'Name': 'Laxmaxs',
        'Phone (from Entity)': ['555-1234'],
        'Owner name (from Entity)': ['John Doe'],
        'Address (from Entity)': ['123 Main St\nDallas, TX 75001'],
        'EIN/VAT (from Entity)': ['12-3456789'],
    }
}"""

def get_record_by_name(name):
    try:
        api = Api(AIRTABLE_API)
        table = api.table(AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME)

        records = table.all(formula=f"{{Name}} = '{name}'")

        if records:
            print(f"The record {name} was fetched")
            return records[0]
        else:
            print(f"The record {name} was not fetched")
            return None


    except Exception as e:
        print(e)
        return None



def get_copies(copies):
    api = Api(AIRTABLE_API)
    table = api.table(AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME_COPIES)

    records = table.all(formula=f"{{Name}} = '{copies}'")

    if records:
        return records[0]['fields']
    return None



def clean_value(value):
    if isinstance(value, list):
        return ", ".join(str(v) for v in value)
    return value



def extract_form_data(name, copies=None):
    # here we get the fields dict (example above)
    fields = name.get('fields', {})

    # extract DBA
    dba = clean_value(fields.get("Name", ""))

    form_dict = {}

    if copies:
        fields.update(copies)

    for airtable_record_name, form_question in DATA.items():
        # here we get a specific value from each field
        value = clean_value(fields.get(airtable_record_name, ""))
        # value = fields.get("Name", "")  # gives you 'Laxmaxs'

        form_dict[form_question] = value
        # then we store the form question as key and the value coresponding to that as value
        # "Company name" = "Name"
    

    # Hardcoded Values
    form_dict["DBA or Brand Name"] = dba
    form_dict["Country of Registration"] = "US"
    
    return form_dict



def fill_field_by_question_text(driver, key, value):
    try:
        time.sleep(0.5)

        # Step 1
        questions = driver.find_elements(By.CLASS_NAME, "M7eMe") # this is the class name for the question text

        question_element = None # for storing the matching q when we fill it
        for q in questions:
            if key.lower() in q.text.lower():
                question_element = q
                print(f"Found question: {q.text}...")
                break
        
        if not question_element:
            print("Could not find question")
            return False
        
        # Step 2 -> get the parent container

        parent = question_element.find_element(By.XPATH, "./ancestor::div[@jsmodel]")

        # Step 3 -> Find the input area or the text area in this container

        try:
            field = parent.find_element(By.TAG_NAME, "input")
        except:
            try:
                field = parent.find_element(By.TAG_NAME, "textarea")
            except:
                print(f"Could not find input/textarea for: {key}")
                return False
        
        # Step 4 - >  Scroll into view (scroll down the page)

        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", field)
        time.sleep(0.3)

        # Step 5 -> fill the fields

        field.click()
        field.clear()
        field.send_keys(str(value))

        print(f"Filled {key} - > {value}")

        return True
    
    except Exception as e:
        print(e)
        return False
    


def select_dropdown(driver, question_text, option_text):
    try:
        time.sleep(0.5)

        questions = driver.find_elements(By.CLASS_NAME, "M7eMe")

        question_element = None
        for q in questions:
            if question_text.lower() in q.text.lower():
                question_element = q
                print("Found question")
                break
        
        if not question_element:
            print("Couldn't find the question")
            return False
        
        parent = question_element.find_element(By.XPATH, "./ancestor::div[@jsmodel]")

        dropdown = parent.find_element(By.CSS_SELECTOR, "div[role='listbox']")

        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", dropdown)
        time.sleep(0.3)
        dropdown.click()
        time.sleep(0.5)

        options = WebDriverWait(driver, 10).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div[role='option']"))
                )


        for option in options:
            if option_text == option.text.strip():
                time.sleep(0.3)
                option.click()
                time.sleep(0.5)
                return True
            
        return False

    except Exception as e:
        print(e)



def fill_form_with_data(driver, form_data, dropdown):
    filled_count = 0

    for key, value in form_data.items():
        if value:
            if fill_field_by_question_text(driver, key, value):
                filled_count += 1
            time.sleep(0.5)


    # Filling the Vertcal Question
    if select_dropdown(driver, "Vertical", dropdown):
        filled_count += 1
    time.sleep(0.5)


    # Filling the DrpopDow menu (Hardcoded)
    try:
        questions = driver.find_elements(By.CLASS_NAME, "M7eMe")

        for q in questions:
            if "What type of legal" in q.text:
                parent = q.find_element(By.XPATH, "./ancestor::div[@jsmodel]")
                dropdowns = parent.find_element(By.CSS_SELECTOR, "div[role='listbox']")
                
                # This line instructs the browser to execute JavaScript that scrolls the page so the specified element becomes visible in the viewport 
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", dropdowns)
                time.sleep(0.3)
                dropdowns.click()
                time.sleep(0.5)

                options = WebDriverWait(driver, 10).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div[role='option']"))
                )

                for option in options:
                    if "Private Company" == option.text.strip():
                        time.sleep(0.3)
                        option.click()
                        time.sleep(0.5)
                        break

    except Exception as e:
        print(e)


    return filled_count



def process_single_record(record, copies, dropdown):
    form_data = extract_form_data(record, copies)

    for key, value in form_data.items():
        print(f"{key} -> {str(value)}")
    
    # Chrome Set-up
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
        driver.get(URL_FORM)
        time.sleep(10)

        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.TAG_NAME, "form"))
        )
        time.sleep(1)

        filled_form = fill_form_with_data(driver, form_data, dropdown)

        if filled_form > 0:
            print("Review")
            time.sleep(180)
        else:
            print("No fields filled")


    finally:
        driver.quit()



def main_bl(value1, value2, number_type):
    name = value1.strip()
    copies = value2.strip()

    record = get_record_by_name(name)
    other_fields = get_copies(copies)
    dropdown = number_type

    if record:
        process_single_record(record, other_fields, dropdown)
    else:
        print("No record found")




if __name__ == "__main__":
    main_bl()
