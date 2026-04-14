from flask import Flask, render_template, request
import requests
from google_form_selenium import main
from google_form_selenium_tcrpy import main_tcr
from google_form_selenium_bulktext import main_bulk_text
from zarkon_brand_registration import main_zbr
from xeebi import main_xeebi
from bulktext_brand_registration import main_bl

app = Flask(__name__) # our app instance

@app.route('/') # app route to our home page
def home():
    return render_template('index.html') # this helps us render the html file

@app.route('/run', methods = ['POST', 'GET'])
def run_script():
    value1 = request.form.get('CampaingerField1')
    value2 = request.form.get('CampaingerField2')
    main(value1, value2)
    return 'Ok'

@app.route('/run-tcr', methods = ['POST', 'GET'])
def run_tcr():
    value1 = request.form.get('TCRField1')
    value2 = request.form.get('TCRField2')
    number_type = request.form.get('numberType')
    main_tcr(value1, value2, number_type)
    return 'Ok'

@app.route('/run-bulk-text', methods = ['POST', 'GET'])
def run_bulk_text():
    value1 = request.form.get('BulkTextField1')
    value2 = request.form.get('BulkTextField2')
    number_type = request.form.get('numberTypeBulkText')
    main_bulk_text(value1, value2, number_type)
    return 'Ok'

@app.route('/run-zbr', methods = ['POST', 'GET'])
def run_zbr():
    value1 = request.form.get("ZbrField1")
    value2 = request.form.get("ZbrField2")
    main_zbr(value1, value2)
    return 'Ok'

@app.route('/run-xeebi', methods = ['POST', 'GET'])
def run_xeebi():
    value1 = request.form.get('XeebiField1')
    value2 = request.form.get('XeebiField2')
    number_type = request.form.get('numberTypeXeebi')
    main_xeebi(value1, value2, number_type)
    return 'Ok'


@app.route('/run-bl', methods = ['POST', 'GET'])
def run_bl():
    value1 = request.form.get('BlField1')
    value2 = request.form.get('BlField2')
    number_type = request.form.get('numberTypeBl')
    main_bl(value1, value2, number_type)
    return 'Ok'

@app.route("/run-xeebi-tfn", methods=['POST'])
def run_xeebi_tfn():
    webhook = 'https://clicklabai.app.n8n.cloud/webhook/1b6c676f-b2dd-43b5-af37-f860999fde0b'
    value1 = request.form.get('XeebiTFNField1')
    url = request.form.get('XeebiTFNURL')
    

    payload = {
        "col1": value1,
        "col2": value1,
        "url": url
    }

    r = requests.post(url=webhook, json=payload)

    return str(r.status_code)



@app.route("/run-bind-10dlc", methods=['POST'])
def run_bind_10dlc():
    webhook = 'https://clicklabai.app.n8n.cloud/webhook/ea1d7f8d-c0d2-4191-be7e-2b564e88204b'
    value1 = request.form.get('Bind10DLC1')
    

    payload = {
        "col1": value1,
        "col2": value1,
    }

    r = requests.post(url=webhook, json=payload)

    return str(r.status_code)





@app.route("/run-d7", methods=['POST'])
def run_d7():
    webhook = 'https://clicklabai.app.n8n.cloud/webhook/6e2e8902-dcea-418f-a351-cd1e2774d373'
    value1 = request.form.get('D7Field1')
    url = request.form.get('D7URL')
    

    payload = {
        "col1": value1,
        "col2": value1,
        "url": url
    }

    r = requests.post(url=webhook, json=payload)

    return str(r.status_code)

@app.route("/run-reve-tfn", methods=['POST'])
def run_reve_tfn():
    webhook = 'https://clicklabai.app.n8n.cloud/webhook/301a265d-4d57-4676-876a-99574cc6e8f5'
    value1 = request.form.get('ReveTFNField1')
    url = request.form.get('ReveTFNURL')
    

    payload = {
        "col1": value1,
        "col2": value1,
        "url": url
    }

    r = requests.post(url=webhook, json=payload)

    return str(r.status_code)

@app.route("/run-deliveryhub", methods=['POST'])
def run_deliveryhub():
    webhook = 'https://clicklabai.app.n8n.cloud/webhook/2ad83cdf-84e2-404c-bfe5-8036dbb6d1ab'
    value1 = request.form.get('DeliveryHubField1')
    url = request.form.get('DeliveryHubURL')

    payload = {
        "col1": value1,
        "col2": value1,
        "url": url
    }

    r = requests.post(url=webhook, json=payload)
    return str(r.status_code)

@app.route("/run-bindtfn", methods=['POST'])
def run_bindtfn():
    webhook = 'https://clicklabai.app.n8n.cloud/webhook/04fb8d07-c98c-49ea-9203-ee8186aa4573'
    value1 = request.form.get('BindTFNField1')
    url = request.form.get('BindTFNURL')

    payload = {
        "col1": value1,
        "col2": value1,
        "url": url
    }

    r = requests.post(url=webhook, json=payload)
    return str(r.status_code)

if __name__ == "__main__":
    app.run(debug=True, port=5015)