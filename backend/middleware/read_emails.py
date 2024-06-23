from email.parser import BytesParser
import os.path
import base64
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from bs4 import BeautifulSoup
import logging
import re


# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def authenticate_gmail():
    """Authenticate with Gmail API and obtain credentials."""
    creds = None
    token_file = "token.json"
    credentials_file = "credentials.json"

    try:
        if os.path.exists(token_file):
            creds = Credentials.from_authorized_user_file(token_file, SCOPES)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    credentials_file, SCOPES
                )
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open(token_file, "w") as token:
                token.write(creds.to_json())
        return creds
    except Exception as e:
        logger.error(f"Failed to authenticate: {e}")
        raise


def fetch_emails(service):
    """Fetch unread emails from Gmail inbox."""
    try:
        # Fetch unread emails from the inbox
        results = service.users().messages().list(
            userId="me", labelIds=["INBOX"], q="is:unread").execute()
        messages = results.get("messages", [])
        emails = []

        for msg in messages:
            msg = service.users().messages().get(
                userId="me", id=msg["id"], format="full").execute()
            emails.append(msg)

        return emails

    except HttpError as error:
        logger.error(f"HttpError occurred: {error}")
        raise
    except Exception as e:
        logger.error(f"Failed to fetch emails: {e}")
        raise


def parse_email_content(email_message):
  """Parse email content and identify internship emails with details."""
  try:
    payload = email_message['payload']
    headers = payload['headers']
    subject = ''
    sender = ''
    for d in headers:
      if d['name'] == 'Subject':
        subject = d['value']
      if d['name'] == 'From':
        sender = d['value']

    # The body of the email is encoded in base64
    parts = payload.get('parts')
    if parts:
      data = parts[0]['body']['data']
      data = data.replace("-", "+").replace("_", "/")
      decoded_data = base64.b64decode(data)

      # Parse the email content with BeautifulSoup
      soup = BeautifulSoup(decoded_data, "lxml")
      body = soup.get_text().lower()  # Convert body to lowercase for easier searching
    else:
      body = "No body content"

    is_internship_related = False
    internship_keywords = ["internship", "intern"]
    for keyword in internship_keywords:
      if keyword in subject.lower() or keyword in body:
        is_internship_related = True
        break

    logger.info(f"Subject: {subject}")
    logger.info(f"From: {sender}")
    logger.info(f"Message: {body}")

    if is_internship_related:
      # Look for specific details in body or attachments (if available)
      # This part requires additional logic to parse for dates, positions, etc.
      # Here's a basic example (replace with more sophisticated parsing)
      # Find dates in format MM/DD/YYYY
      potential_dates = re.findall(r"\d{1,2}/\d{1,2}/\d{4}", body)
      potential_positions = [word for word in body.split() if word.lower(
      ) in ["intern", "assistant"]]  # Find words like "intern" or "assistant"

      logger.info("** This email is related to internship!**")
      if potential_dates:
        logger.info(f"Potential start/end dates: {', '.join(potential_dates)}")
      if potential_positions:
        logger.info(f"Potential internship positions: {
                    ', '.join(potential_positions)}")

      # Check for attachments and potentially extract details from them (if needed)
      if parts and len(parts) > 1:
        logger.info(
            "** Email might contain attachments with internship details. Please check them manually.")

    else:
      logger.info("")  # Add an empty line for better readability

  except Exception as e:
    logger.error(f"Failed to parse email: {e}")
    raise


def main():
    try:
        creds = authenticate_gmail()
        service = build("gmail", "v1", credentials=creds)

        emails = fetch_emails(service)

        for email_message in emails[:10]:
            parse_email_content(email_message)

    except Exception as e:
        logger.error(f"An error occurred in main function: {e}")
        raise


if __name__ == "__main__":
    main()
