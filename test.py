import json
import openai
from openai import OpenAI

messages = []

def add_message(role, text, image_url=None):
    content = [{"type": "text", "text": text}]
    if image_url:
        content.append({
            "type": "image_url",
            "image_url": {
                "url": image_url,
            }
        })
    message = {
        "role": role,
        "content": content
    }
    messages.append(message)

add_message(
    role="user",
    text="What's in this image?",
    image_url="https://upload.wikimedia.org/wikipedia/commons/thumb/d/dd/Gfp-wisconsin-madison-the-nature-boardwalk.jpg/2560px-Gfp-wisconsin-madison-the-nature-boardwalk.jpg"
)

# Pretty print the messages object
pretty_messages = json.dumps(messages, indent=4)
print(pretty_messages)


client = OpenAI(api_key="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")

assistant = client.beta.assistants.create(
    name="Test Image Upload",
    instructions="Follow my instructions",
    model="ft:gpt-4o-2024-08-06:personal::AGXYRssh"
)

thread = client.beta.threads.create()

response = client.beta.threads.messages.create(
    thread_id=thread.id,
    role="user",
    content=messages
)

print(response)