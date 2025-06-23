from openai import OpenAI



class Friday:
    def __init__(self):
        self.client = OpenAI()
        self.input = [
            {
                "role": "user",
                "content": "What tools do you have?"
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
            input = self.input
        )

        return resp.output_text


def main():
    AI = Friday()
    try:
        # input_text = input("Input: ")
        # input_text = "What tools do you have?"
        response = AI.get_response()  # Replace with your input text
        print(response)
    except Exception as e:
        print(e)

if __name__ == "__main__":
    main()


