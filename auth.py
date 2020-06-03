import pickle
import os.path

from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.compose'
]

def load_creds():
    creds = None
    if os.path.exists('configuration/token.pickle'):
        with open('configuration/token.pickle', 'rb') as token:
            creds = pickle.load(token)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('configuration/credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('configuration/token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    return creds