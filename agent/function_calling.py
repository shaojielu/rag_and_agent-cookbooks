from openai import OpenAI

client = OpenAI(base_url="https://www.DMXapi.com/v1",
                    api_key="")

tools = [
  {
      "type": "function",
      "function": {
          "name": "get_weather",
          "parameters": {
              "type": "object",
              "properties": {
                  "location": {"type": "string"}
              },
          },
      },
  },
    {
      "type": "function",
      "function": {
          "name": "get_name",
          "parameters": {
              "type": "object",
              "properties": {
                  "location": {"type": "string"}
              },
          },
      },
  }
]

completion = client.chat.completions.create(
  model="gpt-4o",
  messages=[{"role": "user", "content": "What's the weather like in Paris today?"}],
  tools=tools,
)
# print(completion.choices[0].message)
print(completion.choices[0].message.tool_calls)