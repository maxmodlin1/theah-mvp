import streamlit as st  
from styling import template1_page_style
import json
import re
import streamlit.components.v1 as components
from streamlit.components.v1 import html
import time
import tempfile
import os


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

def upload_files_openai(image_path, client):
    upload = client.files.create(
        file=open(image_path, 'rb'),  # Open the image file in binary mode
        purpose="vision",
    )
    return upload  # Return the list of uploaded image IDs

def create_temp_file(uploaded_file,type=None):
    # Create a temporary directory
    temp_dir = tempfile.mkdtemp()
    
    # Define the path where the file will be saved
    file_path = os.path.join(temp_dir, uploaded_file.name)
    
    # Write the uploaded file to the temporary directory
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getvalue())
    
    # Now you can use file_path as needed
    st.session_state['floorplan_path'].append(file_path)
    print(st.session_state['floorplan_path'])

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
        postcode = st.text_input("Enter the postcode of the property")
        
        # Update session state with form data
        st.session_state.form_data.update({"property_address": address, "property_postcode": postcode})
        
        # Back and Next buttons
        col_back, col_next = st.columns([1, 1])
        with col_back:
            if st.button("Back"):
                previous_step()
        with col_next:
            if st.button("Next"):
                next_step()

def page_3():
    st.session_state['floorplan_path'] = []
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
                    create_temp_file(property_floorplan, type="floorplan")
                next_step()

def page_4():
    col1, col2 = st.columns([2, 1])
    with col1:
        st.title("Please upload some photos of your property.")
        property_photos = st.file_uploader("Upload your photos", key="photos", type=["jpg", "jpeg", "png"])
        st.markdown("<br>", unsafe_allow_html=True)  # Add vertical spacing
        col_back, col_next = st.columns([1, 1])
        with col_back:
            if st.button("Back"):
                previous_step()
        with col_next:
            if st.button("Next"):
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
    
    with open('/Users/maxmodlin/maxdev/Streamlit_UI_Template/templates/description.txt', 'r') as f:
        desc = f.read()

    st.markdown(desc)

def main():  
    with open('/Users/maxmodlin/maxdev/Streamlit_UI_Template/templates/generation.json', 'r') as f:
        data = json.load(f)
        st.session_state['data'] = data

    if 'page' not in st.session_state:
        st.session_state.page = 0

    if 'form_data' not in st.session_state:
        st.session_state.form_data = {}

    if "scroll_to_top" not in st.session_state:
        st.session_state.scroll_to_top = False
    
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