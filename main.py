from openai import OpenAI





class Jarvis:
    def __init__(self):
        self.client = OpenAI()

    def get_response(self, input_text):
        resp = self.client.responses.create(
            model="gpt-4.1-mini",
            tools=[
                {
                    "type": "mcp",
                    "server_label": "deepwiki",
                    "server_url": "https://mcp.deepwiki.com/mcp",
                    "require_approval": "never",
                },
            ],
            input=input_text,
        )

        return resp.output_text


def main():
    AI = Jarvis()
    try:
        input_text = input("Input: ")
        response = AI.get_response(input_text=input_text)
        print(response)
    except Exception as e:
        print(e)

if __name__ == "__main__":
    main()


