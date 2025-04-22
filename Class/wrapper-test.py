from langchain.chat_models import ChatHchat
from langchain.schema import HumanMessage, SystemMessage

# Initialize with your API key
chat = ChatHchat(
    model="gpt-3.5-turbo",  # or your model name
    hchat_api_key="your-api-key-here",
    hchat_api_base="https://your-api-endpoint.com"  # default is https://api.hchat.com
)

# Create a simple conversation
messages = [
    SystemMessage(content="You are a helpful assistant."),
    HumanMessage(content="Hello, how are you today?")
]

# Get a response
response = chat(messages)
print(response.content)

# For streaming responses
chat = ChatHchat(
    model="gpt-3.5-turbo",
    streaming=True,
    hchat_api_key="your-api-key-here"
)

for chunk in chat.stream(messages):
    print(chunk.content, end="", flush=True)
