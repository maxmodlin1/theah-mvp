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
                "type": "image_file",
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

def upload_files_openai(uploaded_file,type=None):
    
    client = OpenAI(api_key="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")

    # Create a temporary directory
    temp_dir = tempfile.mkdtemp()
    
    # Define the path where the file will be saved
    file_path = os.path.join(temp_dir, uploaded_file.name)
    
    # Write the uploaded file to the temporary directory
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getvalue())
    
    # UPLOAD TO OPENAI
    try:
        # UPLOAD TO OPENAI
        upload = client.files.create(
            file=open(file_path, 'rb'),  # Open the image file in binary mode
            purpose="vision"
        )
        print(f"File uploaded successfully: {upload}")
    except Exception as e:
        print(f"An error occurred during file upload: {e}")

    if type == "floorplan":
        st.session_state['floorplan_id'].append(upload.id)
        return st.session_state['floorplan_id']
    elif type == "propertyphotos":
        st.session_state['property_photo_ids'].append(upload.id)
        return st.session_state['property_photo_ids']

def go_home():
    st.session_state.page = 0

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
        address = st.text_input("Enter the Street Name of the property")
        
        # Update session state with form data
        st.session_state.form_data.update({"property_address": address})
        
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
                if property_floorplan is not None:
                    upload_files_openai(property_floorplan, type="floorplan")
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
                            upload_files_openai(photo, type="propertyphotos")
                        
                        # CREATE THE ASSISTANT
                        name = "Theah Content Generator V2"      
                        initial_instruction = get_theah_content("system")                                                                                                                                                                                                                                                                                                                                                                                                                                                                               
                        assistant = create_assistant(name=name,instructions=initial_instruction,model=st.session_state['model'])
                        st.session_state['assistant_id'] = assistant['assistantid']
                        st.session_state['thread_id'] = assistant["threadid"]
                        print(st.session_state['assistant_id'])
                        print(st.session_state['thread_id'])

                        # REVIEW THE FLOORPLAN  
                        floorplan_instruction = get_theah_content("get_floorplan_review")   
                        new_thread_message = add_thread(thread_id=st.session_state['thread_id'] ,message=floorplan_instruction,files=st.session_state['floorplan_id'],role="user")
                        run_assistant(threadid=st.session_state['thread_id'],assistantid=st.session_state['assistant_id'])
                        final_json = print_last_assistant_message(threadid=st.session_state['thread_id'])
                    
                next_step()

def page_5():
    st.title("Layout and Specifications")
        # Place the "Back" and "Next" buttons at the top
    col1, col2, col3 = st.columns([1, 0.1, 1])
    with col1:
        if st.button("Back"):
            st.session_state.page -= 1
            st.session_state.scroll_to_top = True
            st.rerun()
    with col3:
        if st.button("Next"):
            st.session_state.page += 1
            st.session_state.scroll_to_top = True
            st.rerun()
    st.markdown("<br>", unsafe_allow_html=True)  # Add vertical spacing
    st.write("Please confirm we've got the floor plan features correct. You can add or remove floor plan specifics as you see fit. This helps us to tailor a truly accurate listing description.")
    st.image("https://storage.googleapis.com/bucket-quickstart_maxs-first-project-408116/corum/OverleeRoad/all_floors_1_overlee_road_glasgow_with_dim-scaled.jpg", width=500)
    


    # Initialize session state for selected features
    if 'selected_features' not in st.session_state:
        st.session_state.selected_features = {}

    # Iterate through the floorplan data
    for floor in st.session_state['data']["floorplan"]:
        for floor_name, floor_details in floor.items():
            formatted_floor_name = floor_name.replace('_', ' ').title()
            st.markdown(f'<div class="orange-text">{formatted_floor_name}</div><br>', unsafe_allow_html=True)
            if floor_name not in st.session_state.selected_features:
                st.session_state.selected_features[floor_name] = floor_details["features"]

            # Display checkboxes for each feature
            updated_features = []
            for feature in st.session_state.selected_features[floor_name]:
                is_selected = st.checkbox(feature, key=f"{floor_name}_{feature}", value=feature in st.session_state.selected_features[floor_name])
                if is_selected:
                    updated_features.append(feature)

            # Add a text area for additional features
            st.markdown('<div class="custom-text-area">', unsafe_allow_html=True)
            additional_features = st.text_area(f"Add more features to {formatted_floor_name}", key=f"additional_features_{floor_name}")
            st.markdown('</div>', unsafe_allow_html=True)

            if additional_features:
                additional_features_list = additional_features.split('\n')
                updated_features.extend(additional_features_list)

            # Update the session state with the updated features
            st.session_state.selected_features[floor_name] = updated_features

    # Scroll to top after rerun if needed
    if st.session_state.scroll_to_top:
        st.session_state.scroll_to_top = True
        
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
            st.session_state.page += 1
            st.session_state.scroll_to_top = True
            st.rerun()
    st.markdown("<br>", unsafe_allow_html=True)  # Add vertical spacing
    st.write("We've summarized your property in 4 steps. Please verify you are happy with these points. You can add or remove as required.")

    # Add a text area for property overview
    property_overview = st.session_state['data'].get("property_overview", "")
    property_overview = preprocess_text(property_overview)
    property_overview_text = st.text_area("Property Overview", value=property_overview, key="property_overview")

    external_features = st.session_state['data'].get("external_features", "")
    external_features = preprocess_text(external_features)
    external_features_text = st.text_area("External Features", value=external_features, key="external_features")

    local_area_highlights = st.session_state['data'].get("local_area_highlights", "")
    local_area_highlights = preprocess_text(local_area_highlights)
    local_area_highlights_text = st.text_area("Local Area Highlights", value=local_area_highlights, key="local_area_highlights")

    additional_notes_text = st.text_area("Please add any additional features you wish to add to the description.", key="additional_notes")

def page_7():
    st.title("Your Property Listing Description.")
    address = st.session_state.form_data.get("property_address", "")
    st.write(address)

    st.image("https://storage.googleapis.com/bucket-quickstart_maxs-first-project-408116/corum/OverleeRoad/P1311672-Medium.jpg",width=500)
    
    #with open('/Users/maxmodlin/maxdev/Streamlit_UI_Template/templates/description.txt', 'r') as f:
    with open('C:\\Users\\Administrator\\theah-mvp\\templates\\description.txt', 'r') as f:
        desc = f.read()
        desc = desc.replace('\n', '<br>')

    
    css = """
    <style>
        .custom-markdownn {
            border: 1px dashed #ffffff; /* Slightly thinner border for a cleaner look */  
            border-radius: 2px; /* Rounded corners for a modern touch */  
            padding: 8px 12px; /* Adjusted padding for better alignment */  
            background-color: #0D1342; /* Light background color for contrast */  
            font-size: 16px; /* Slightly larger font for readability */  
            color: #ffffff; /* Darker text color for better readability */  
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1); /* Subtle shadow for depth */  
            transition: border-color 0.3s ease, box-shadow 0.3s ease; /* Smooth transition for hover effects */  
  

        }
    </style>
    """

    styled_desc = f"{css}<div class='custom-markdownn'>{desc}</div>"

    # Display the styled markdown content
    st.markdown(styled_desc, unsafe_allow_html=True)


def main(): 

    #with open('/Users/maxmodlin/maxdev/Streamlit_UI_Template/templates/generation.json', 'r') as f:
    with open('C:\\Users\\Administrator\\theah-mvp\\templates\\generation.json', 'r') as f:
        data = json.load(f)
        st.session_state['data'] = data

    with open('C:\\Users\\Administrator\\theah-mvp\\prompts\\theah_conversation.yml', 'r') as file:
        theah_convo = yaml.safe_load(file)
        st.session_state['theah_convo'] = theah_convo



    if 'page' not in st.session_state:
        st.session_state.page = 0

    if 'form_data' not in st.session_state:
        st.session_state.form_data = {}

    if "scroll_to_top" not in st.session_state:
        st.session_state.scroll_to_top = False

    if 'floorplan_id' not in st.session_state:
        st.session_state['floorplan_id'] = []
    
    if 'property_photo_ids' not in st.session_state:
        st.session_state['property_photo_ids'] = []
    
    if 'model' not in st.session_state:
        st.session_state.model = "ft:gpt-4o-2024-08-06:personal::AGXYRssh"

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