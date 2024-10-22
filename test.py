import json
import re

with open('/Users/maxmodlin/maxdev/Streamlit_UI_Template/templates/generation.json', 'r') as f:
    data = json.load(f)

property_overview = data.get("property_overview", "")

# Check if property_overview is a list
if isinstance(property_overview, list):
    # Join the list elements into a single string with each element on a new line
    property_overview = '\n'.join(property_overview)

print(property_overview)

