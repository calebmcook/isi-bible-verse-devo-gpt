import json
from openai import OpenAI
import boto3
from boto3.dynamodb.conditions import Attr
from twilio.rest import Client
import logging

logger = logging.getLogger(__name__)

def lambda_handler(event, context):
    #get twilio auth token from AWS systems manager parameter store
    ssm = boto3.client('ssm')

    twilio_account_sid = ssm.get_parameter(
        Name='/twilio/isiaccount/twilio_account_sid',
        WithDecryption=True
    )['Parameter']['Value']

    twilio_auth_token = ssm.get_parameter(
        Name='/twilio/isiaccount/twilio_auth_token',
        WithDecryption=True
    )['Parameter']['Value']

    openai_organization_id = ssm.get_parameter(
        Name='/openai/isi_devo_gpt/organization_id',
    )['Parameter']['Value']

    openai_organization_id = ssm.get_parameter(
            Name='/openai/isi_devo_gpt/organization_id',
        )['Parameter']['Value']

    openai_thread_id_isidevogpt = ssm.get_parameter(
            Name='/openai/isi_devo_gpt/thread_id_isidevogpt',
        )['Parameter']['Value']
    
    openai_assistant_100_id = ssm.get_parameter(
            Name='/openai/isi_devo_gpt/assistant_100',
        )['Parameter']['Value']
    
    openai_api_key = ssm.get_parameter(
            Name='/openai/isi_devo_gpt/api_key',
            WithDecryption=True
        )['Parameter']['Value']

    # start OpenAI interaction
    openai_client = OpenAI(
        organization=openai_organization_id,
        api_key=openai_api_key
    )

    #get ongoing dev thread
    my_thread = openai_client.beta.threads.retrieve(thread_id=openai_thread_id_isidevogpt)

    # create a new message to get the next devo
    thread_message = openai_client.beta.threads.messages.create(
        thread_id=openai_thread_id_isidevogpt,
        role="user",
        content="Please share the next devotional message.",
    )

    # create the run
    run = openai_client.beta.threads.runs.create(
        thread_id=openai_thread_id_isidevogpt,
        assistant_id=openai_assistant_100_id
    )

    # retreive the run
    run_results = openai_client.beta.threads.runs.retrieve(
        thread_id=openai_thread_id_isidevogpt,
        run_id=run.id
    )

    #get the messages list
    messages = openai_client.beta.threads.messages.list(
        thread_id=openai_thread_id_isidevogpt
    )

    # isolate the output
    output = messages.data[0].content[0].text.value
    print(output)

    # create Twilio client
    twilio_client = Client(twilio_account_sid, twilio_auth_token)

    # Get subscribers
    #dynamodb = boto3.resource('dynamodb')
    #clients_table = dynamodb.Table('isi-bible-verse-clients-db3-dev')
    # scan for only subscribers to daily-devo and pull out their phone numbers
    #subscribers = clients_table.scan(FilterExpression=Attr('current_status').eq('DAILY-DEVO')|Attr('current_status').eq('ALL'))
    #subscriber_numbers = [k['phone_number'] for k in subscribers['Items']]
    
    subscriber_numbers = ['14802088265']

    # send messages
    for phone_num in subscriber_numbers:
        try: 
            message = twilio_client.messages.create(
                    messaging_service_sid='MGe8378c0c9e461b6c628995ba22ed4444',
                    body='[Iron Sharpens Iron - Men\'s Ministry]\n{}\n"STOP-SERVICES" to unsubscribe. Try "DAILY-IMAGE", "DAILY-SMS", "HOPE-SMS"'.format(output),
                    send_as_mms=True,
                    to=phone_num
            )
            logger.warning(message)
            pass

        except Exception as err:
            logger.warning("Couldn't send message to number %s.",
                    phone_num)
            continue

    return {
        'statusCode': 200
    }
