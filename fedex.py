import requests 
import json
import os
from progress.bar import Bar
from time import sleep


def authenticate():
    """Authenticate with the server, collect api key(FEDEX)"""

    api_key = os.environ.get("FEDEX_API_KEY")
    if(api_key == None):
        print("key refresh")
        url = "https://apis.fedex.com/oauth/token"

        payload = {
            'grant_type':'client_credentials',
            'client_id':'',
            'client_secret':''
        }

        headers = {
            'Content-Type': "application/x-www-form-urlencoded"
        }

        response = requests.request("POST", url, data=payload, headers=headers)
        api_key = response.json()['access_token']
        os.environ['FEDEX_API_KEY'] = str(api_key)
    return api_key


def validate_addresses(addressline1, addressline2, city, state, zipCode, api_key=authenticate()):
    """"validate provided address, return dict"""

    url = 'https://apis.fedex.com/address/v1/addresses/resolve'
    headers = {
                'Content-Type': "application/json",
                'X-locale': "en_US",
                'Authorization': "Bearer " + api_key}

    payload = json.dumps({"validateAddressControlParameters": {
                        "includeResolutionTokens": 'true'},
                        "addressesToValidate": [{
                        "address": {
                            "streetLines": [
                                addressline1,
                                addressline2],
                            "city": city,
                            "stateOrProvinceCode": state,
                            "postalCode": zipCode,
                            "countryCode": 'US'}}]})

    response = requests.request('POST', url, data=payload, headers=headers)
    if(response.status_code == 401):
        api_key = authenticate()
        os.environ["FEDEX_API_KEY"] = api_key
    response = response.json()['output']['resolvedAddresses'][0]
   
    if (response['attributes']['Matched'] == 'true' and response['attributes']['Resolved'] == 'true' and response['attributes']['InvalidSuiteNumber'] == 'false' and
        response['attributes']['SuiteRequiredButMissing'] == 'false'):
        new_addressline1 = response['streetLinesToken'][0]
        try:
            new_addressline2 = response['streetLinesToken'][1]
        except IndexError:
            new_addressline2 = None
        new_city = response['cityToken'][0]['value']
        new_state = response['stateOrProvinceCodeToken']['value']
        new_zipCode = response['parsedPostalCode']['base'] + '-' + response['parsedPostalCode']['addOn']

        if new_addressline2 == None:
            validly_formed =  '`'+ new_addressline1 + '`' + '\n' + '`' + new_city + ', ' + new_state + ', ' + new_zipCode + '`'
        else:
            validly_formed =  '`'+ new_addressline1 + '`' + '\n' + '`' + new_addressline2 + '`' + '\n' + '`' + new_city + ', ' + new_state + ', ' + new_zipCode + '`'

        return "Valid Address. :white_check_mark:\n" + validly_formed
        
    else :
        try:
            new_addressline2 = response['streetLinesToken'][1]
        except IndexError:
            new_addressline2 = None
        try:
            if response['attributes']['InvalidSuiteNumber'] == 'true':
                return 'Invalid address line 2'
            elif response['customerMessages'][0]['code'] == 'STANDARDIZED.ADDRESS.NOTFOUND':
                return 'Address not found:x:'
        except KeyError:
            pass
        try:
            if response['customerMessages'][0]['code'] == 'SUITE.NUMBER.REQUIRED':
                if new_addressline2 == None:
                    return "Multi-unit building. Address line 2 required."
        except KeyError:
            pass

    return response.json()

def track_shipment(tracking_num, api_key=authenticate()):
    """Retrieve tracking info from tracking number"""
        
    url = 'https://apis.fedex.com/track/v1/trackingnumbers'

    headers = {
        'Content-Type': "application/json",
        'X-locale': "en_US",
        'Authorization': "Bearer " + api_key
    }

    payload = json.dumps({"trackingInfo": 
                    [{"trackingNumberInfo":
                        {"trackingNumber": tracking_num}
                        }],"includeDetailedScans": "false"})
    
    response = requests.request("POST", url, data=payload, headers=headers)

    if(response.status_code == 401):
        api_key = authenticate()
        os.environ["FEDEX_API_KEY"] = api_key
    print(response.json())
    return response.json()


def transit_time(recipient_postal_code : str, shipper_postal_code : str, weight : str, api_key=authenticate()):
    url = 'https://apis.fedex.com/availability/v1/transittimes'

    headers = headers = {
            'Content-Type': "application/json",
            'X-locale': "en_US",
            'Authorization': "Bearer " + api_key
    }

    payload = json.dumps({
                "requestedShipment": {
                "shipper": {
                    "address": {
                    "postalCode": shipper_postal_code,
                    "countryCode": "US"}},
        "recipients": [{
        "address": {
          "postalCode": recipient_postal_code,
          "countryCode": "US"}}],
                "packagingType": "FEDEX_MEDIUM_BOX",
                "requestedPackageLineItems": [{
            "weight": {
          "units": "LB",
          "value": weight}}]},
            "carrierCodes": [
                "FDXE"]})

    response = requests.request("POST", url, data=payload, headers=headers)

    if(response.status_code == 401):
        api_key = authenticate()
        os.environ["FEDEX_API_KEY"] = api_key

    return response.json()
    



                
      

