import json
import openai
from openai import OpenAI
import yaml

messages = []

client = OpenAI(api_key="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")

with open('/Users/maxmodlin/maxdev/theah-mvp/prompts/theah_conversation.yml', 'r') as file:
    theah_convo = yaml.safe_load(file)

def get_theah_content(role_name):
    for message in theah_convo['conversation']['messages']:
        if message['role'] == role_name:
            return message['content']
    return None

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


# # Pretty print the messages object
# pretty_messages = json.dumps(messages, indent=4)
# print(pretty_messages)

# Initialize OpenAI client
openai.api_key = "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"

system = get_theah_content("system")
floorplan = get_theah_content("get_floorplan_review")

add_message(
    role="user",
    text=floorplan,
    image_url="https://storage.googleapis.com/bucket-quickstart_maxs-first-project-408116/corum/CarolsideAvenue/floorplan.jpg"
)

json.dumps(messages, indent=4)
# Make a chat completion call
response = client.chat.completions.create(
    model="ft:gpt-4o-2024-08-06:personal:corum-v1-october:ALQtVsTt",
    messages=[
        {"role": "system", "content": system},
        *messages
    ],
    temperature=0
)

print(response.choices[0].message.content)