import streamlit as st  
from styling import template1_page_style
import json
import re
import streamlit.components.v1 as components
from streamlit.components.v1 import html
import time
import tempfile
import os
import yaml
import openai
from openai import OpenAI
from google.cloud import storage
import random

def update_json_object(key, value):
    st.session_state['json_object'][key] = value

def next_step():
    st.session_state.page += 1
    st.rerun()  # Use experimental_rerun to force a rerun

def previous_step():
    st.session_state.page -= 1
    st.rerun()  # Use experimental_rerun to force a rerun

def preprocess_text(text):
    # Check if property_overview is a list
    if isinstance(text, list):
        # Join the list elements into a single string with each element on a new line
        new_text = '\n'.join(text)
    return new_text

def get_theah_content(role_name):
    for message in st.session_state['theah_convo']['conversation']['messages']:
        if message['role'] == role_name:
            return message['content']
    return None

def add_message(role, text, image_url=None):
    content = []

    content = [{"type": "text", "text": text}]

    if image_url is not None:
        for img in image_url:
            content.append({
                "type": "image_url",
                "image_url": {
                    "url": img,
                    "detail": "high"
                }
            })
            
    message = {
        "role": role,
        "content": content
    }

    print(message)

    st.session_state['chat_messages'].append(message)

def add_thread(thread_id,message,role,files=None):

    client = OpenAI(api_key="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")

    messages = []

    if files:
        
        msg = {
            "type": "text",
            "text": message
        }
        messages.append(msg)

        for file in files:
            file_obj = {
                "type": "image_url",
                "image_file": {
                    "file_id": str(file)
                }
            }

            messages.append(file_obj)
    else:
        msg = {
            "type": "text",
            "text": message
        }
        messages.append(msg)

    response = client.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=messages
    )

    return messages

def upload_to_gcs(source_file_path,file_name):

    bucket_name = "bucket-quickstart_maxs-first-project-408116"
    destination_blob_name = f"client_uploads/{file_name}"

    # Initialize the storage client
    storage_client = storage.Client()

    # Get the bucket
    bucket = storage_client.bucket(bucket_name)

    # Create a blob object and upload the file
    try:
        blob = bucket.blob(destination_blob_name)
        blob.upload_from_filename(source_file_path)
        #print(f"File {source_file_path} uploaded to gs://{bucket_name}/{destination_blob_name}")
        public_url = f"https://storage.googleapis.com/{bucket_name}/{destination_blob_name}"
        return str(public_url)
    except Exception as e:
        print(f"An error occurred: {e}")

def upload_files(uploaded_file,type=None):
    
    client = OpenAI(api_key="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")

    # Create a temporary directory
    temp_dir = tempfile.mkdtemp()
    
    # Define the path where the file will be saved
    file_path = os.path.join(temp_dir, uploaded_file.name)
    
    # Write the uploaded file to the temporary directory
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getvalue())
    
    upload_google_cloud = upload_to_gcs(source_file_path=file_path,file_name=uploaded_file.name)

    if type == "floorplan":
        st.session_state['floorplan_url'].append(upload_google_cloud)
        return st.session_state['floorplan_url']
    elif type == "propertyphotos":
        st.session_state['property_photo_urls'].append(upload_google_cloud)
        return st.session_state['property_photo_urls']

def go_home():
    st.session_state.clear()
    st.session_state.page = 0
    st.rerun()

def create_assistant(name,instructions,model):
    
    client = OpenAI(api_key="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")

    assistant = client.beta.assistants.create(
        name=name,
        instructions=instructions,
        model=st.session_state['model']
    )

    thread = client.beta.threads.create()

    obj = {"assistantid": assistant.id, "threadid": thread.id}

    return obj

def run_assistant(threadid,assistantid):

    client = OpenAI(api_key="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")

    run = client.beta.threads.runs.create(
        thread_id=threadid,
        assistant_id=assistantid
        )

    while True:

        run_status = client.beta.threads.runs.retrieve(
            thread_id=threadid, 
            run_id=run.id
        )

        if run_status.status == "completed":
            break
        elif run_status.status == "failed":
            print("Run failed:", run_status.last_error)
            break
        time.sleep(2)  # wait for 2 seconds before checking again

def print_last_assistant_message(threadid):
    
    client = OpenAI(api_key="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")

    messages = client.beta.threads.messages.list(
            thread_id=threadid
        )
    
    if messages.data:  # Check if there are any messages
        return (messages.data[0].content[0].text.value) 

def generate_json():
    print("----------------------------------------------------------")
    st.session_state['chat_messages'] = []
    client = OpenAI(api_key="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")
    json_obj = st.session_state['json_object']
    json_str = json.dumps(json_obj)
    system = get_theah_content("system_buildjson")

    # system_prompt = system.replace('{{ JSON }}', json_str)
    # system_prompt = system_prompt.replace('{{ PROPERTY_ADDRESS }}', str(st.session_state['property_address']))

    print("SYSTEM!")
    print(system)

    features_update = get_theah_content("user_buildjson")
    features_update = features_update.replace('{{ JSON }}', json_str)

    add_message(
        role="system",
        text=system
    )

    add_message(
        role="user",
        text=features_update,
        image_url=st.session_state['property_photo_urls']
    )

    print("SENDING------->")

    print(st.session_state['chat_messages'])
    m = st.session_state['chat_messages']
    json_print = json.dumps(m, indent=4)
    print(json_print)

    # Make a chat completion call
    response = client.chat.completions.create(
        model="ft:gpt-4o-2024-08-06:personal::ANMvB86e",
        messages=[
            *st.session_state['chat_messages']
        ],
        temperature=0.1
    )

    content = response.choices[0].message.content

    try:
        # Parse the content to a dictionary
        new_data = json.loads(content)
        print("NEW DATA")
        print(new_data)
        
        # Update the relevant fields
        if 'local_area_highlights' in new_data:
            st.session_state['json_object']['local_area_highlights'] = new_data['local_area_highlights']
        if 'property_overview' in new_data:
            st.session_state['json_object']['property_overview'] = new_data['property_overview']
        if 'external_features' in new_data:
            st.session_state['json_object']['external_features'] = new_data['external_features']
        print("Updated json_object:", st.session_state['json_object'])
    except json.JSONDecodeError as e:
        print("Failed to parse JSON:", e)

def make_floorplan_review_call(floorplan_url):   
    
    floorurl = st.session_state['floorplan_url']
    print("Floorplan")
    for i in st.session_state['floorplan_url']: 
        print(i)
    
 
    client = OpenAI(api_key="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")
    system = get_theah_content("system_floorplan")
    floorplan = get_theah_content("user_floorplan")

    add_message(
        role="system",
        text=system,
    )

    add_message(
        role="user",
        text=floorplan,
        image_url=floorurl
    )

    print("CHAT")
    m = st.session_state['chat_messages']
    # json_print = json.dumps(m, indent=4)
    # print(json_print)

    # Make a chat completion call
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            *m
        ],
        temperature=0.5
    )

    content = response.choices[0].message.content
    print("RESPONSE1-FLOORPLAN")
    print(content)

    try:
        st.session_state['json_object'] = json.loads(content)
    except json.JSONDecodeError as e:
        print("Failed to parse JSON:", e) 

def generate_description():
    st.session_state['chat_messages'] = []
    pretty_json = json.dumps(st.session_state['json_object'], indent=4)
    print(pretty_json)

    validjson = json.dumps(st.session_state['json_object'])

    client = OpenAI(api_key="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")
    system = get_theah_content("system_gendescription")
    description = get_theah_content("user_gendescription")
    update_description = description.replace('{{ JSON }}', str(pretty_json))

    add_message(
        role="system",
        text=system
    )

    add_message(
        role="user",
        text=update_description,
    )

    # Make a chat completion call
    response = client.chat.completions.create(
        model="ft:gpt-4o-2024-08-06:personal:corum-beta-v2-gendescriptions:ANSZjUc7",
        messages=[
            *st.session_state['chat_messages']
        ],
        temperature=0.2
    )

    content = response.choices[0].message.content

    print("FIRST GENERATION")
    print(content)

    ### VALIDATE DESCRIPTON ###
    validate_prompt = get_theah_content("user_validate")
    pass_json = validate_prompt.replace('{{ JSON }}', str(pretty_json))
    pass_description = pass_json.replace('{{ DESCRIPTION }}', content)


    add_message(
        role="user",
        text=pass_description
    )

    # Make a chat completion call
    response2 = client.chat.completions.create(
    model="o1-preview",
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": pass_description
                },
            ],
        }
    ]
)


    content2 = response2.choices[0].message.content
    print("FIRST GENERATION")
    print(content2)
    return content2


def page_1():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.image("https://storage.googleapis.com/bucket-quickstart_maxs-first-project-408116/corum/no-property-img.webp", width=500)  # Adjust the width as needed
        if st.button("Get Started"):
            next_step()

def page_2():
    col1, col2 = st.columns([2, 1])
    with col1:
        st.title("Where is the property located?")
        
        # Address input fields
        address = st.text_input("Enter the Street Name and Postcode of the property",placeholder='1 Overlee Road, Clarkston, Glasgow, G76')
        st.session_state['property_address'] = address
        
        # Back and Next buttons
        col_back, col_next = st.columns([1, 1])
        with col_back:
            if st.button("Back"):
                previous_step()
        with col_next:
            if st.button("Next"):
                next_step()

def page_3():
 
    col1, col2 = st.columns([2, 1])
    with col1:
        st.title("Please upload the floorplan of your property.")
        property_floorplan = st.file_uploader("Upload your floorplan", key="photos", type=["jpg", "jpeg", "png"])
        st.markdown("<br>", unsafe_allow_html=True)  # Add vertical spacing
        
        col_back, col_next = st.columns([1, 1])
        with col_back:
            if st.button("Back"):
                previous_step()
        with col_next:
            if st.button("Next"):
                with st.spinner('Processing...'):
                    if property_floorplan is not None:
                        upload_files(uploaded_file=property_floorplan, type="floorplan")
                        print(st.session_state['floorplan_url'])
                next_step()

def page_4():
    col1, col2 = st.columns([2, 1])
    with col1:
        st.title("Please upload some photos of your property.")
        property_photos = st.file_uploader("Upload your photos", key="photos", type=["jpg", "jpeg", "png"],accept_multiple_files=True)
        st.markdown("<br>", unsafe_allow_html=True)  # Add vertical spacing
        col_back, col_next = st.columns([1, 1])
        with col_back:
            if st.button("Back"):
                previous_step()
        with col_next:
            if st.button("Next"):
                print(property_photos)
                if property_photos:
                    with st.spinner('Processing...'):
                        for photo in property_photos:
                            upload_files(photo, type="propertyphotos")
                        print("Now making the call..")
                        make_floorplan_review_call(st.session_state['floorplan_url'])
                    next_step()
                else:
                    st.error("Please upload at least one photo")

def page_5():
    # HTML and CSS for the pop-up image effect
    html_content = """
    <style>
    .image-container {
        position: relative;
        display: inline-block;
        width: 100%;
        cursor: pointer;
    }
    .image-container img {
        width: 100%;
        height: auto;
        transition: all 0.3s ease;
    }
    .image-container img:hover {
        transform: scale(1.05);
    }
    .popup-image {
        display: none;
        position: fixed;
        z-index: 9999;
        left: 0;
        top: 0;
        width: 100%;
        height: 100%;
        overflow: auto;
        background-color: rgba(0,0,0,0.9);
        justify-content: center;
        align-items: center;
    }
    .popup-content {
        max-width: 90%;
        max-height: 90%;
        object-fit: contain;
    }
    .close {
        position: absolute;
        top: 15px;
        right: 35px;
        color: #f1f1f1;
        font-size: 40px;
        font-weight: bold;
        cursor: pointer;
    }
    </style>

    <div id="imagePopup" class="popup-image" onclick="closeImage()">
        <span class="close">&times;</span>
        <img class="popup-content" id="popupImg" onclick="event.stopPropagation()">
    </div>

    <script>
    function showImage(src) {
        var popup = document.getElementById("imagePopup");
        var popupImg = document.getElementById("popupImg");
        popup.style.display = "flex";
        popupImg.src = src;
    }

    function closeImage() {
        var popup = document.getElementById("imagePopup");
        popup.style.display = "none";
    }
    </script>
    """

    st.title("Floorplan Review")

    # Navigation Buttons
    col_back, col_next = st.columns([2, 1])
    with col_back:
        if st.button("Back"):
            previous_step()
    with col_next:
        if st.button("Next"):
            print(st.session_state['json_object'])
            generate_json()
            next_step()

    st.markdown("<br>", unsafe_allow_html=True)
    st.write("We've reviewed the floorplan— now it's your turn to help us bring each floor to life. By adding details about each space, you'll help us craft a captivating description of your property. The more specifics you share, the better the result!")
    st.markdown("<br>", unsafe_allow_html=True)

    # Display Floorplan Image with pop-out functionality
    if 'floorplan_url' in st.session_state:
        url_floorplan = st.session_state['floorplan_url'][0]
        st.markdown(f"""
            <div class="image-container" onclick="showImage('{url_floorplan}')">
                <img src="{url_floorplan}" alt="Floorplan">
            </div>
            {html_content}
            """, unsafe_allow_html=True)

    # Initialize session state for floors and selected features
    if 'floors' not in st.session_state:
        st.session_state.floors = [{floor_name: floor_details} for floor in st.session_state['json_object']["floorplan"] for floor_name, floor_details in floor.items()]

    if 'selected_features' not in st.session_state:
        st.session_state.selected_features = {}
        for floor in st.session_state.floors:
            for floor_name, floor_details in floor.items():
                st.session_state.selected_features[floor_name] = floor_details["features"]

    # Initialize current_floor_names
    if 'current_floor_names' not in st.session_state:
        st.session_state.current_floor_names = [list(floor.keys())[0] for floor in st.session_state.floors]

    # Existing Floors Section
    # Custom CSS for header and columns
    custom_css = """
    <style>
        .stHeader {
            font-size: 24px;
            color: orange;
        }
    </style>
    """

    # Inject custom CSS
    st.markdown(custom_css, unsafe_allow_html=True)

    # Use custom styled header
    st.markdown('<h1 class="stHeader">Update Floors</h1>', unsafe_allow_html=True)
   
    for i, floor in enumerate(st.session_state.floors):
        current_floor_name = st.session_state.current_floor_names[i]
        with st.expander(f"Floor: {current_floor_name.replace('_', ' ').title()}", expanded=False):
            floor_name, floor_details = list(floor.items())[0]  # Each floor is a single-item dictionary
            
            # Allow user to edit floor name
            new_floor_name = st.text_area(f"Edit Floor Name", value=current_floor_name.replace('_', ' ').title(), key=f"floor_name_{i}")
            new_floor_key = new_floor_name.lower().replace(' ', '_')
            
            if new_floor_key != current_floor_name:
                # Update floor name in session state
                st.session_state.floors[i] = {new_floor_key: floor_details}
                if floor_name in st.session_state.selected_features:
                    st.session_state.selected_features[new_floor_key] = st.session_state.selected_features.pop(floor_name)
                st.session_state.current_floor_names[i] = new_floor_key
                st.rerun()

            # Ensure the floor is in selected_features
            if new_floor_key not in st.session_state.selected_features:
                st.session_state.selected_features[new_floor_key] = floor_details.get("features", [])

            # Combine existing features into a single string
            existing_features = '\n'.join(st.session_state.selected_features[new_floor_key])

            # Add a text area for editing features
            updated_features = st.text_area(f"Edit Features for {new_floor_name}", value=existing_features, key=f"features_{new_floor_key}")

            # Split the updated features into a list
            updated_features_list = [feature.strip() for feature in updated_features.split('\n') if feature.strip()]

            # Update the session state with the updated features
            st.session_state.selected_features[new_floor_key] = updated_features_list

            # Update the floor's "features" section with the new features
            floor_details["features"] = updated_features_list

            # Add button to remove floor
            if st.button(f"Remove {new_floor_name}", key=f"remove_{new_floor_key}"):
                st.session_state.floors.pop(i)
                del st.session_state.selected_features[new_floor_key]
                st.session_state.current_floor_names.pop(i)
                st.rerun()
    
    # Add New Floor Section
    st.markdown('<h1 class="stHeader">Add New Floor</h1>', unsafe_allow_html=True)
    new_floor_name = st.text_input("Enter new floor name (e.g., 'Ground Floor', 'First Floor')", key="new_floor_input")

    add_button = st.button("Add Floor", key="add_floor_button")

    if add_button and new_floor_name:
        new_floor_key = new_floor_name.lower().replace(' ', '_')
        if not any(new_floor_key in floor for floor in st.session_state.floors):
            new_floor = {new_floor_key: {"features": []}}
            st.session_state.floors.append(new_floor)
            st.session_state.selected_features[new_floor_key] = []
            st.session_state.current_floor_names.append(new_floor_key)
            st.rerun()

    # Update the json_object with the modified floors
    st.session_state['json_object']["property_address"] = st.session_state['property_address']
    st.session_state['json_object']["floorplan"] = st.session_state.floors

    # Scroll to top after rerun if needed
    if st.session_state.get('scroll_to_top', False):
        st.session_state.scroll_to_top = False  

def page_6():
    st.title("Your Property Summary.")
    # Place the "Back" and "Next" buttons at the top
    col1, col2, col3 = st.columns([1, 0.1, 1])
    with col1:
        if st.button("Back"):
            st.session_state.page -= 1
            st.session_state.scroll_to_top = True
            st.rerun()
    with col3:
        if st.button("Next"):
            with st.spinner('Processing...'):
                st.session_state['json_object']["property_overview"] =  st.session_state['property_overview_text']
                st.session_state['json_object']["external_features"] = st.session_state['external_features_text']
                st.session_state['json_object']["local_area_highlights"] = st.session_state['local_area_highlights_text']
                st.session_state['json_object']["additional_notes"] = st.session_state['additional_notes_text']
                st.session_state['the_description'] = generate_description()
                st.session_state.page += 1
                st.session_state.scroll_to_top = True
                st.rerun()
    st.markdown("<br>", unsafe_allow_html=True)  # Add vertical spacing
    st.write("We’ve captured the key highlights of your property in four simple sections. Please review them and make any adjustments you’d like—feel free to add or remove details to ensure everything feels just right.")

    # Add a text area for property overview
    property_overview = st.session_state['json_object'].get("property_overview", "")
    property_overview = preprocess_text(property_overview)
    st.session_state['property_overview_text'] = st.text_area("Property Overview", value=property_overview, key="property_overview")

    external_features = st.session_state['json_object'].get("external_features", "")
    external_features = preprocess_text(external_features)
    st.session_state['external_features_text'] = st.text_area("External Features", value=external_features, key="external_features")

    local_area_highlights = st.session_state['json_object'].get("local_area_highlights", "")
    local_area_highlights = preprocess_text(local_area_highlights)
    st.session_state['local_area_highlights_text'] = st.text_area("Local Area Highlights", value=local_area_highlights, key="local_area_highlights")

    st.session_state['additional_notes_text'] = st.text_area("Please add any additional features you wish to add to the description.", key="additional_notes")


    # # Add text areas for each floor of the floorplan
    # floorplan = st.session_state['json_object'].get("floorplan", [])

    # for floor in floorplan:
    #     for floor_name, floor_details in floor.items():
    #         formatted_floor_name = floor_name.replace('_', ' ').title()
            
    #         # Combine existing features into a single string
    #         existing_features = '\n'.join(floor_details["features"])
            
    #         # Add a text area for editing features
    #         st.markdown('<div class="custom-text-area">', unsafe_allow_html=True)
    #         updated_features = st.text_area(f"Edit features for {formatted_floor_name}", value=existing_features, key=f"features_{floor_name}")
    #         st.markdown('</div>', unsafe_allow_html=True)
            
    #         # Split the updated features into a list
    #         updated_features_list = updated_features.split('\n')
            
    #         # Update the session state with the updated features
    #         floor_details["features"] = updated_features_list

def page_7():
    st.title("Your Property Listing Description.")
    address = st.session_state.form_data.get("property_address", "")
    st.write(address)
    st.image("https://storage.googleapis.com/bucket-quickstart_maxs-first-project-408116/corum/OverleeRoad/P1311672-Medium.jpg",width=500)
    
    # with open('/Users/maxmodlin/maxdev/Streamlit_UI_Template/templates/description.txt', 'r') as f:
    # #with open('C:\\Users\\Administrator\\theah-mvp\\templates\\description.txt', 'r') as f:
    #     desc = f.read()
    #     desc = desc.replace('\n', '<br>')

    # newjson = st.session_state['json_object']
    # validjson = json.dumps(newjson, indent=4)
    
    # css = """
    # <style>
    #     .custom-markdownn {
    #         border: 1px dashed #ffffff; /* Slightly thinner border for a cleaner look */  
    #         border-radius: 2px; /* Rounded corners for a modern touch */  
    #         padding: 8px 12px; /* Adjusted padding for better alignment */  
    #         background-color: #0D1342; /* Light background color for contrast */  
    #         font-size: 16px; /* Slightly larger font for readability */  
    #         color: #ffffff; /* Darker text color for better readability */  
    #         box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1); /* Subtle shadow for depth */  
    #         transition: border-color 0.3s ease, box-shadow 0.3s ease; /* Smooth transition for hover effects */  
  

    #     }
    # </style>
    # """

    # styled_desc = f"{css}<div class='custom-markdownn'>{desc}</div>"

    # # Display the styled markdown content
    # st.markdown(styled_desc, unsafe_allow_html=True)

    desc = st.session_state['the_description']
    st.markdown(desc)

def main(): 

    with open('/Users/maxmodlin/maxdev/Streamlit_UI_Template/templates/generation.json', 'r') as f:
    #with open('C:\\Users\\Administrator\\theah-mvp\\templates\\generation.json', 'r') as f:
        data = json.load(f)
        st.session_state['data'] = data

    with open('/Users/maxmodlin/maxdev/theah-mvp/prompts/theah_conversation.yml', 'r') as file:
    #with open('C:\\Users\\Administrator\\theah-mvp\\prompts\\theah_conversation.yml', 'r') as file:
        theah_convo = yaml.safe_load(file)
        st.session_state['theah_convo'] = theah_convo

    if 'page' not in st.session_state:
        st.session_state.page = 0

    if 'form_data' not in st.session_state:
        st.session_state.form_data = {}

    if "scroll_to_top" not in st.session_state:
        st.session_state.scroll_to_top = False

    if 'floorplan_url' not in st.session_state:
        st.session_state['floorplan_url'] = []
    
    if 'property_photo_urls' not in st.session_state:
        st.session_state['property_photo_urls'] = []
    
    if 'model' not in st.session_state:
        st.session_state.model = "ft:gpt-4o-2024-08-06:personal::AGXYRssh"

    if 'json_object' not in st.session_state:
        st.session_state['json_object'] = None
    
    if 'chat_messages' not in st.session_state:
        st.session_state['chat_messages'] = []
    
    if 'property_overview_text' not in st.session_state:
        st.session_state['property_overview_text'] = ""
    
    if 'external_features_text' not in st.session_state:
        st.session_state['external_features_text'] = ""
    
    if 'local_area_highlights_text' not in st.session_state:
        st.session_state['local_area_highlights_text'] = ""
    
    if 'additional_notes_text' not in st.session_state:
        st.session_state['additional_notes_text'] = ""

    st.sidebar.button("New Description", on_click=go_home)
    
    pages = [page_1, page_2, page_3, page_4, page_5, page_6,page_7]
    
    if st.session_state.page < len(pages):
        pages[st.session_state.page]()
    else:
        st.error("Invalid page")

    if st.session_state.scroll_to_top:
        
        js = '''
        <script>
            var body = window.parent.document.querySelectorAll('.stElementContainer element-container st-emotion-cache-u1rfgn e1f1d6gn4');
            console.log(body);
            body.scrollTop = 0;
        </script>
        '''

        st.components.v1.html(js)


if __name__ == "__main__":  
    template1_page_style()
    main()