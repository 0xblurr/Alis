import os
import json
import requests
import csv
import fedex
import yams
from slack_bolt import App
from modals import address_validate_input as validate

alis = App(
    #token = os.environ.get("SLACK_BOT_TOKEN"),
    token = '',
    signing_secret = ''
    #signing_secret = os.environ.get("SLACK_SIGNING_SECRET")
)

def post_message(message, token=alis._token):
    """Posts a message to provided channel"""
    url = 'https://slack.com/api/chat.postMessage'

    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + token
    }

    payload = json.dumps({
        'channel': 'C04JAK9NG3Z',
        'text': message
    })

    requests.request('POST', url, headers=headers, data=payload)


@alis.event('message')
def address_validation(event, ack):
    """listens for messages from user, performs appropriate actions based on keywords"""
    print(event)
    ack()
    message = event['blocks'][0]['elements'][0]['elements'][0]['text']
 
    if message.find('alis validate') > -1:
        message = message[13:len(message)]
        reader = csv.reader(message.strip().splitlines())
        address = None
        for i in reader:
            address = i
        
        try:
            addressline1 = address[0].strip()
            city = address[2].strip()
            state =address[3].strip()
            zipCode = address[4].strip()
            addressline2 = address[1].strip()
        except IndexError:
            post_message('Please enter the address in the following format:\n`Address Line 1,Address Line 2,City,State,Zip`\nIf there is no apt/suite number, place an additional comma as demonstrated below.\n`Address Line 1,,City,State,Zip`')

        response_string = fedex.validate_addresses(addressline1, addressline2, city, state, zipCode)
        print(response_string)
        post_message(response_string)

    if message.find('alis track') > -1: 
        tracking_num = message[10:len(message)].strip()
        tracking_info = fedex.track_shipment(tracking_num)
        status = tracking_info['output']['completeTrackResults'][0]['trackResults'][0]['latestStatusDetail']['statusByLocale']

        for i in tracking_info['output']['completeTrackResults'][0]['trackResults'][0]['dateAndTimes']:
            if i['type'] == 'ESTIMATED_DELIVERY':
                status_info = i['dateTime'][0:(i['dateTime']).index('T')]
                post_message('*Status*: ' + status + '\n' + '*Estimated Delivery*: ' + '`'+status_info+'`')
            elif i['type'] == 'ACTUAL_DELIVERY':
                status_info = i['dateTime'][0:(i['dateTime']).index('T')]
                post_message('*Status*: ' + status + '\n' + '*Delivered*: ' + '`'+status_info+'`')
  
    if message.find('zheidemann') > -1:
        post_message("My creator:heart:")
        
    if message.find('sorry alis') > -1:
        post_message(':saulgoodman:')

    if message.find('alice') > -1:
        post_message('You mean alis?:angry:')

@alis.shortcut('validate_addy')
def validate_address_shortcut(shortcut, ack, token=alis._token):
    ack()
    url = 'https://slack.com/api/views.open'
    trigger_id = shortcut['trigger_id']
    user_id = shortcut['user']['id']

    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + token
    }

    payload = json.dumps({
            "trigger_id": trigger_id,
                "view": validate.modal})

    requests.request('POST', url, headers=headers, data=payload)

@alis.view("")
def address_validate_modal_submitted(view, ack):
    ack()
    print(view)
    addressline1_id, addressline2_id, city_id, state_id, zipCode_id = None, None, None, None, None
    addressline1, addressline2, city, state, zipCode = None, None, None, None, None

    #retrieve block ids from modal submission
    for i in view['blocks']:
        if i['label']['text'] == 'Address Line 1':
            addressline1_id = i['block_id']
        elif i['label']['text'] == 'Address Line 2':
            addressline2_id = i['block_id']
        elif i['label']['text'] == 'City':
            city_id = i['block_id']
        elif i['label']['text'] == 'State':
            state_id = i['block_id']
        elif i['label']['text'] == 'Zip Code':
            zipCode_id = i['block_id']
        
    #pull input data from response payload via block ids
    addressline1 = view['state']['values'][addressline1_id]['plain_text_input-action']['value'].strip()
    addressline2 = view['state']['values'][addressline2_id]['plain_text_input-action']['value'].strip()
    city = view['state']['values'][city_id]['plain_text_input-action']['value'].strip()
    state = view['state']['values'][state_id]['plain_text_input-action']['value'].strip()
    zipCode = view['state']['values'][zipCode_id]['plain_text_input-action']['value'].strip()

    message_string = fedex.validate_addresses(addressline1, addressline2, city, state, zipCode)
    post_message(message_string)






    
if __name__ == '__main__':
    alis.start(port=int(os.environ.get('PORT', 80)))