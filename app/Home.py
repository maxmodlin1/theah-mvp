import streamlit as st  
import streamlit.components.v1 as components
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
import logging
import pyperclip


# Configure logging
logging.basicConfig(
    level=logging.DEBUG,  # Set the logging level
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # Log to console
        logging.FileHandler("app.log")  # Log to file
    ]
)

# Set logging levels for specific libraries
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('google.auth').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)
logging.getLogger('http').setLevel(logging.WARNING)
logging.getLogger('openai').setLevel(logging.WARNING)
logging.getLogger('httpcore').setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

def update_json_object(key, value):
    logger.debug(f"Updating JSON object: {key} = {value}")
    st.session_state['json_object'][key] = value

def next_step():
    logger.info("User selected the next step")
    st.session_state.page += 1
    st.rerun()

def previous_step():
    logger.info("User selected the previous step")
    st.session_state.page -= 1
    st.rerun()

def preprocess_text(text):
    logger.debug(f"Preprocessing text: {text}")
    if isinstance(text, list):
        new_text = '\n'.join(text)
    return new_text

def get_theah_content(role_name):
    logger.debug(f"Getting content for role: {role_name}")
    for message in st.session_state['theah_convo']['conversation']['messages']:
        if message['role'] == role_name:
            return message['content']
    return None

def add_message(role, text, image_url=None):
    logger.debug(f"Building the message to send to OpenAI")
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
    message = {"role": role, "content": content}
    st.session_state['chat_messages'].append(message)

def add_thread(thread_id, message, role, files=None):
    logger.debug(f"Adding thread: thread_id={thread_id}, message={message}, role={role}, files={files}")
    client = OpenAI(api_key="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")
    messages = [{"type": "text", "text": message}]
    if files:
        for file in files:
            file_obj = {"type": "image_url", "image_file": {"file_id": str(file)}}
            messages.append(file_obj)
    response = client.beta.threads.messages.create(thread_id=thread_id, role="user", content=messages)
    return messages

def upload_to_gcs(source_file_path, file_name):
    #logger.debug(f"Uploading to GCS: source_file_path={source_file_path}, file_name={file_name}")
    bucket_name = "bucket-quickstart_maxs-first-project-408116"
    destination_blob_name = f"client_uploads/{file_name}"
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    try:
        blob = bucket.blob(destination_blob_name)
        blob.upload_from_filename(source_file_path)
        public_url = f"https://storage.googleapis.com/{bucket_name}/{destination_blob_name}"
        logger.info(f"File uploaded to GCS: {public_url}")
        return str(public_url)
    except Exception as e:
        logger.error(f"An error occurred during GCS upload: {e}")

def upload_files(uploaded_file, type=None):
    #logger.debug(f"Uploading file: {uploaded_file.name}, type={type}")
    client = OpenAI(api_key="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")
    temp_dir = tempfile.mkdtemp()
    file_path = os.path.join(temp_dir, uploaded_file.name)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getvalue())
    upload_google_cloud = upload_to_gcs(source_file_path=file_path, file_name=uploaded_file.name)
    if type == "floorplan":
        st.session_state['floorplan_url'].append(upload_google_cloud)
        return st.session_state['floorplan_url']
    elif type == "propertyphotos":
        st.session_state['property_photo_urls'].append(upload_google_cloud)
        return st.session_state['property_photo_urls']

def go_home():
    logger.info("Returning to home page")
    st.session_state.clear()
    st.session_state.page = 0
    st.rerun()

def create_assistant(name, instructions, model):
    logger.debug(f"Creating assistant: name={name}, instructions={instructions}, model={model}")
    client = OpenAI(api_key="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")
    assistant = client.beta.assistants.create(name=name, instructions=instructions, model=st.session_state['model'])
    thread = client.beta.threads.create()
    obj = {"assistantid": assistant.id, "threadid": thread.id}
    return obj

def run_assistant(threadid, assistantid):
    logger.debug(f"Running assistant: threadid={threadid}, assistantid={assistantid}")
    client = OpenAI(api_key="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")
    run = client.beta.threads.runs.create(thread_id=threadid, assistant_id=assistantid)
    while True:
        run_status = client.beta.threads.runs.retrieve(thread_id=threadid, run_id=run.id)
        if run_status.status == "completed":
            break
        elif run_status.status == "failed":
            logger.error(f"Run failed: {run_status.last_error}")
            break
        time.sleep(2)

def print_last_assistant_message(threadid):
    logger.debug(f"Printing last assistant message: threadid={threadid}")
    client = OpenAI(api_key="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")
    messages = client.beta.threads.messages.list(thread_id=threadid)
    if messages.data:
        return messages.data[0].content[0].text.value

def generate_json():
    st.session_state['chat_messages'] = []
    client = OpenAI(api_key="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")
    json_obj = st.session_state['json_object']
    json_str = json.dumps(json_obj)
    system = get_theah_content("system_buildjson")
    features_update = get_theah_content("user_buildjson")
    features_update = features_update.replace('{{ JSON }}', json_str)

    add_message(role="system", text=system)
    add_message(role="user", text=features_update, image_url=st.session_state['property_photo_urls'])
    logger.info("Sending the following JSON object to OpenAI to populate the JSON...")
    prettyjson = json.dumps(st.session_state['chat_messages'], indent=4)
    logger.debug(prettyjson)

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=st.session_state['chat_messages'],
        temperature=0.1
    )
    
    content = response.choices[0].message.content

    try:
        new_data = json.loads(content)
        prettyjson = json.dumps(new_data, indent=4)
        logger.debug("The Response from OpenAI and presented to the user..")
        logger.debug(prettyjson)

        if 'local_area_highlights' in new_data:
            st.session_state['json_object']['local_area_highlights'] = new_data['local_area_highlights']
        if 'property_overview' in new_data:
            st.session_state['json_object']['property_overview'] = new_data['property_overview']
        if 'external_features' in new_data:
            st.session_state['json_object']['external_features'] = new_data['external_features']
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON: {e}")

def make_floorplan_review_call(floorplan_url):
    client = OpenAI(api_key="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")
    system = get_theah_content("system_floorplan")
    floorplan = get_theah_content("user_floorplan")
    add_message(role="system", text=system)
    add_message(role="user", text=floorplan, image_url=st.session_state['floorplan_url'])
    
    prettyjson = json.dumps(st.session_state['chat_messages'], indent=4)
    logger.debug(f"Sending this JSON Object to OpenAI: {prettyjson}")

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=st.session_state['chat_messages'],
        temperature=0.5
    )
    content = response.choices[0].message.content
    logger.debug(f"Response content: {content}")
    try:
        st.session_state['json_object'] = json.loads(content)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON: {e}")

def generate_description():
    st.session_state['chat_messages'] = []
    validjson = json.dumps(st.session_state['json_object'])
    pretty_json = json.dumps(st.session_state['json_object'], indent=4)
    #logger.debug(f"Pretty JSON: {pretty_json}")

    client = OpenAI(api_key="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")
    system = get_theah_content("system_gendescription")
    description = get_theah_content("user_gendescription")
    update_description = description.replace('{{ JSON }}', str(pretty_json))
    
    add_message(role="system", text=system)
    add_message(role="user", text=update_description)

    logger.info("Sending this JSON object to OpenAI to generate the description...")
    prettyjson = json.dumps(st.session_state['chat_messages'], indent=4)

    response = client.chat.completions.create(
        model="ft:gpt-4o-2024-08-06:personal:corum-beta-v2-gendescriptions:ANSZjUc7",
        messages=st.session_state['chat_messages'],
        temperature=0.2
    )
    content = response.choices[0].message.content

    logger.debug(f"First generation response..")
    logger.debug("")
    logger.debug(content)

    logger.debug("Validating the description against new AI model..")

    st.session_state['chat_messages'] = []
    validate_prompt = get_theah_content("user_validate")
    pass_json = validate_prompt.replace('{{ JSON }}', str(pretty_json))
    pass_description = pass_json.replace('{{ DESCRIPTION }}', content)
    
    add_message(role="user", text=pass_description)

    logger.info("Sending the this prompt to OpenAI to validate the description...")
    prettyjson = json.dumps(st.session_state['chat_messages'], indent=4)
    logger.debug(prettyjson)

    response2 = client.chat.completions.create(
        model="o1-mini",
        messages=[{"role": "user", "content": [{"type": "text", "text": pass_description}]}]
    )
    content2 = response2.choices[0].message.content
    logger.debug(f"Validation content: {content2}")
    return content2

def page_1():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.image("https://storage.googleapis.com/bucket-quickstart_maxs-first-project-408116/corum/no-property-img.webp", width=500)
        if st.button("Get Started"):
            logger.info("User Selected Get Started")
            next_step()

def page_2():
    col1, col2 = st.columns([2, 1])
    with col1:
        st.title("Where is the property located?")

        # Custom CSS for placeholder text color
        custom_css = """
        <style>
            .stTextInput input::placeholder {
                color: grey !important; /* Set placeholder text color to white */
                opacity: 1; /* Ensure the placeholder text is fully opaque */
                font-size: 14px;
            }

            .stTextInput input {
                caret-color: white !important; /* Set cursor color to white */
                font-size: 14px; /* Set input text font size */
            }
        </style>
        """

        # Inject the custom CSS into the Streamlit app
        st.markdown(custom_css, unsafe_allow_html=True)

        # Text input with placeholder
        address = st.text_input("Enter the full address of the property including the postcode", placeholder='1 Overlee Road, Clarkston, Glasgow, G76 8BU')

        st.session_state['property_address'] = address
        col_back, col_next = st.columns([1, 1])
        with col_back:
            if st.button("Back"):
                previous_step()
        with col_next:
            if st.button("Next"):
                logger.info(f"User inputted Property Address: {address}")
                next_step()

def page_3():
    col1, col2 = st.columns([2, 1])
    with col1:
        st.title("Please upload the floorplan of your property.")
        property_floorplan = st.file_uploader("Upload your floorplan", key="photos", type=["jpg", "jpeg", "png"])
        st.markdown("<br>", unsafe_allow_html=True)
        col_back, col_next = st.columns([1, 1])
        with col_back:
            if st.button("Back"):
                previous_step()
        with col_next:
            if st.button("Next"):
                with st.spinner('Processing...'):
                    if property_floorplan is not None:
                        upload_files(uploaded_file=property_floorplan, type="floorplan")
                        logger.debug(f"Floorplan URL: {st.session_state['floorplan_url']}")
                next_step()

def page_4():
    col1, col2 = st.columns([2, 1])
    with col1:
        st.title("Please upload some photos of your property.")
        property_photos = st.file_uploader("Upload your photos", key="photos", type=["jpg", "jpeg", "png"], accept_multiple_files=True)
        st.markdown("<br>", unsafe_allow_html=True)
        col_back, col_next = st.columns([1, 1])
        with col_back:
            if st.button("Back"):
                previous_step()
        with col_next:
            if st.button("Next"):
                #logger.debug(f"Property photos: {property_photos}")
                if property_photos:
                    with st.spinner('Processing...'):
                        for photo in property_photos:
                            upload_files(photo, type="propertyphotos")
                        logger.info("Making the OpenAI call to review the floorplan")
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
            logger.info("User populated the floorplan section and selected the next step. Their choices are noted below")
            prettyjson = json.dumps(st.session_state['json_object'], indent=4)
            logger.info(prettyjson)
            logger.info("Moving on to the populate the 'local area, overview and external features' section")
            generate_json()
            next_step()


    st.markdown("<br>", unsafe_allow_html=True)
    st.write("We've reviewed the floor plan, and now it's your turn to help bring each space to life. Please review each area in the floor plan and add any details you think would enhance the description. You can also add or remove floors incase we've not got it quite right.")
    
    st.write("Simple updates like changing 'Living Room' to 'Spacious living room' or changing 'Kitchen' to 'Modern kitchen with integrated appliances' can make a big difference. The more specifics you add, the better the result!")

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
    st.markdown('<h1 class="stHeader">Update Floor Information</h1>', unsafe_allow_html=True)

    custom_css = """
        <style>
            .stTextInput input {
                caret-color: white !important; /* Set cursor color to white */
                font-size: 14px; /* Set input text font size */
            }
            .stTextInput p {
                colour: orange !important;
            }
        </style>
        """

    # Inject the custom CSS into the Streamlit app
    st.markdown(custom_css, unsafe_allow_html=True)
   
    for i, floor in enumerate(st.session_state.floors):
        current_floor_name = st.session_state.current_floor_names[i]
        with st.expander(f"Floor: {current_floor_name.replace('_', ' ').title()}", expanded=False):
            floor_name, floor_details = list(floor.items())[0]  # Each floor is a single-item dictionary
            
            # Allow user to edit floor name
            new_floor_name = st.text_input(f"Edit Floor Name", value=current_floor_name.replace('_', ' ').title(), key=f"floor_name_{i}")
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
                logger.info("User populated the local area, overview and external features section and selected the next step. Their choices are noted below")
                prettyjson = json.dumps(st.session_state['json_object'], indent=4)
                logger.info(prettyjson)
                logger.info("Going to generate the description based on the JSON object above")
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
    
    st.title("Your Property Listing Description")
    st.write("We've generated a description based on the information you've provided. Feel free to edit the description below to make it your own.")

    # Create a string with the image URLs
    image_urls = st.session_state['property_photo_urls']
    url_string = ",".join(image_urls)

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
    /* Your existing CSS here */
    </style>
    </head>
    <body>
    <div class="slideshow-container" id="slideshow-container">
    <!-- Slides will be dynamically inserted here -->
    </div>
    <br>

    <div style="text-align:center" id="dots-container">
    <!-- Dots will be dynamically inserted here -->
    </div>

    <script>
    // Split the URL string into an array
    const imageUrls = "{url_string}".split(",");
    let slideIndex = 0;

    // Function to create slides
    function createSlides() {{
        const container = document.getElementById("slideshow-container");
        const dotsContainer = document.getElementById("dots-container");
        
        imageUrls.forEach((url, index) => {{
            const slide = document.createElement("div");
            slide.className = "mySlides fade";
            
            const numberText = document.createElement("div");
            numberText.className = "numbertext";
            numberText.textContent = `${{index + 1}} / ${{imageUrls.length}}`;
            
            const img = document.createElement("img");
            img.src = url;
            img.style.width = "100%";
            
            const text = document.createElement("div");
            text.className = "text";
            text.textContent = `Caption ${{index + 1}}`;
            
            slide.appendChild(numberText);
            slide.appendChild(img);
            slide.appendChild(text);
            
            container.appendChild(slide);
            
            const dot = document.createElement("span");
            dot.className = "dot";
            dotsContainer.appendChild(dot);
        }});
    }}

    function showSlides() {{
        let slides = document.getElementsByClassName("mySlides");
        let dots = document.getElementsByClassName("dot");
        
        for (let i = 0; i < slides.length; i++) {{
            slides[i].style.display = "none";  
        }}
        slideIndex++;
        if (slideIndex > slides.length) {{slideIndex = 1}}    
        for (let i = 0; i < dots.length; i++) {{
            dots[i].className = dots[i].className.replace(" active", "");
        }}
        slides[slideIndex-1].style.display = "block";  
        dots[slideIndex-1].className += " active";
        setTimeout(showSlides, 3000); // Change image every 2 seconds
    }}

    // Create slides when the page loads
    createSlides();
    // Start the slideshow
    showSlides();
    </script>

    </body>
    </html>
    """

    st.components.v1.html(html_content, height=500)

    # Custom CSS for text area height
    custom_css = """
        <style>
            .stTextArea textarea {
                height: 500px !important; /* Set the height of the text area */
            }
        </style>
        """

    # Inject the custom CSS into the Streamlit app
    st.markdown(custom_css, unsafe_allow_html=True)
        
    # Get the description from session state
    desc = st.session_state.get('the_description', '')
    
    # Create an editable text area
    edited_desc = st.text_area("Edit your description:", value=desc)
    
    # Create a copy to clipboard button
    if st.button("Copy to Clipboard"):
        pyperclip.copy(edited_desc)
        st.success("Description copied to clipboard!")
    
    # Update the session state with the edited description
    st.session_state['the_description'] = edited_desc
def main(): 

    #with open('/Users/maxmodlin/maxdev/Streamlit_UI_Template/templates/generation.json', 'r') as f:
    with open('C:\\Users\\Administrator\\theah-mvp\\templates\\generation.json', 'r') as f:
        data = json.load(f)
        st.session_state['data'] = data

    #with open('/Users/maxmodlin/maxdev/theah-mvp/prompts/theah_conversation.yml', 'r') as file:
    with open('C:\\Users\\Administrator\\theah-mvp\\prompts\\theah_conversation.yml', 'r') as file:
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