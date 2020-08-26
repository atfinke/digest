from googleapiclient.discovery import build
from apiclient import errors
from email.mime.text import MIMEText

from datetime import datetime

import base64
import configuration.secrets as secrets
from auth import load_creds

import schedule
import time

def fetch_labels(service):
    results = service.users().labels().list(userId='me').execute()
    labels = results.get('labels', [])

    if not labels:
        return []
    else:
        return labels

def fetch_message_ids(service):
    results = service.users().messages().list(userId='me', q='-in:sent is:unread').execute()
    messages = results.get('messages', [])
    
    if not messages:
        return []
    else:
        return list(map(lambda x: x['id'], messages))

def fetch_message(service, message_id, labels):
    message = service.users().messages().get(userId='me', id=message_id).execute()
    headers = message['payload']['headers']

    for header in headers:
        if header['name'] == 'Subject':
            subject = header['value']

            for label in message['labelIds']:
                if 'INBOX' in label:
                    return ('Inbox', subject)
                elif 'Label_' in label:
                    for service_label in labels:
                        if label == service_label['id']:
                            return (service_label['name'], subject)

    return None


def digest_str(label, subjects):
    digest = ""
    digest += '<b>' + label + ' ({}):</b><br><ul>'.format(len(subjects))
    for subject in subjects:
        digest += '<li>' + subject + '</li><br>'
    digest += '</ul>'
    return digest

def send_email(service, report_messages, count):
    digest = '<html><head></head><body>'

    indox_messages = report_messages.pop('Inbox', None)
    if indox_messages:
        digest += digest_str('Inbox', indox_messages) + '<br>'
    
    for label, subjects in report_messages.items():
        digest += digest_str(label, subjects)

    digest += '<a href="https://mail.google.com/mail/u/1/#inbox">Open</a><br><br>/eom</body></html>'
    date = datetime.now()

    message = MIMEText(digest, 'html')
    message['to'] = secrets.TO_EMAIL
    message['from'] = secrets.FROM_EMAIL
    message['subject'] = 'NU {}/{} Digest ({} Unread)'.format(date.month, date.day, count)

    encoded = base64.urlsafe_b64encode(message.as_bytes())
    message_body = {
        'raw': encoded.decode()
    }

    try:
        service.users().messages().send(userId='me', body=message_body).execute()
    except errors.HttpError as error:
        print(error)


def run():
    print('run')
    
    creds = load_creds()
    service = build('gmail', 'v1', credentials=creds)

    labels = fetch_labels(service)
    message_ids = fetch_message_ids(service)
    
    count = 0
    report_messages = {}
    error_message = ('*Unknown*', 'Error')

    for message_id in message_ids:
        label = None
        subject = None
        try:
            metadata = fetch_message(service, message_id, labels)
            if not metadata:
                metadata = error_message
            label = metadata[0]
            subject = metadata[1]
        except:
            label = error_message[0]
            subject = error_message[1]
        
        count += 1
        existing = report_messages.get(label, [])
        existing.append(subject)
        report_messages[label] = existing

    if count > 0:
        print('creating digest')
        send_email(service, report_messages, count)
    else:
        print('no count')

def job_try():
    try:
        run()
    except Exception as exc:
        print('Unexpected error: {}'.format(exc))

schedule.every().day.at('22:00').do(job_try)
if __name__ == '__main__':
    print('first run')
    job_try()
    while True:
        print('waiting')
        schedule.run_pending()
        time.sleep(60 * 10)