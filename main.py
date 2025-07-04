from openai import OpenAI
from dotenv import load_dotenv
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

load_dotenv()



class Friday:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.input = [
            {
                "role": "developer",
                "content": "You are Friday from the movie The Avengers, a smart high-tech AI assistant developed by Iron Man, now you are assisting Antony, me. You speak in a brief, clean, high efficient way. You are assistive. You use a very formal tone, for most of the time you call me sir."
            }
        ]

    def get_response(self, input_text=None):
        resp = self.client.responses.create(
            model="gpt-4.1-mini",
            tools=[
                {
                    "type": "mcp",
                    "server_label": "deepwiki",
                    "server_url": "https://mcp.deepwiki.com/mcp",
                    "require_approval": "never",
                },
                {
                    "type": "function",
                    "name": "send_email",
                    "description": "Send an email to a given recipient with a subject and body via Gmail SMTP",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "to": {
                                "type": "string",
                                "description": "Email address to send to"
                            },
                            "subject": {
                                "type": "string", 
                                "description": "Email subject"
                            },
                            "body": {
                                "type": "string",
                                "description": "Email body text"
                            },
                            "attachment_path": {
                                "type": "string",
                                "description": "Optional file path for attachment"
                            }
                        }
                    },
                    "required": ["to", "subject", "body"],
                    "additional_properties": False
                }

            ],  
            input = self.input + [{"role": "user", "content": input_text}],
        )

        return resp.output_text

    def send_email(self, to, subject, body, attachment_path=None):
        """Send an email via Gmail SMTP"""
        try:
            gmail_user = os.getenv("GMAIL_USER")
            gmail_password = os.getenv("GMAIL_APP_PASSWORD")
            
            if not gmail_user or not gmail_password:
                return "Error: Gmail credentials not found in environment variables"
            
            msg = MIMEMultipart()
            msg['From'] = gmail_user
            msg['To'] = to
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'plain'))
            
            if attachment_path and os.path.exists(attachment_path):
                with open(attachment_path, "rb") as attachment:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(attachment.read())
                
                encoders.encode_base64(part)
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename= {os.path.basename(attachment_path)}'
                )
                msg.attach(part)
            
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(gmail_user, gmail_password)
            text = msg.as_string()
            server.sendmail(gmail_user, to, text)
            server.quit()
            
            return f"Email sent successfully to {to}"
            
        except Exception as e:
            return f"Error sending email: {str(e)}"


def main():
    AI = Friday()
    try:
        # input_text = input("Input: ")
        input_text = "What tools do you have?"
        response = AI.get_response(input_text)  # Replace with your input text
        print(response)
    except Exception as e:
        print(e)

if __name__ == "__main__":
    main()


