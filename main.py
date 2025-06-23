from openai import OpenAI
from dotenv import load_dotenv
import os

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
                }
            ],  
            input = self.input + [{"role": "user", "content": input_text}],
        )

        return resp.output_text


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


