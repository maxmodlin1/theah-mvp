import streamlit as st  
from styling import template1_page_style
import json
import re
from streamlit.components.v1 import html

def next_step():
    st.session_state.step += 1
    scroll_to_top()
    st.rerun() 

def previous_step():
    st.session_state.step -= 1
    scroll_to_top()
    st.rerun()

def preprocess_text(text):

    # Check if property_overview is a list
    if isinstance(text, list):
        # Join the list elements into a single string with each element on a new line
        new_text = '\n'.join(text)

    return new_text

def scroll_to_top():
    js = '''
    <script>
        var body = window.parent.document.querySelector(".main");
        body.scrollTop = 0;
    </script>
    '''
    html(js)

def main():  
    
    if 'step' not in st.session_state:
        st.session_state.step = 1

    with open('/Users/maxmodlin/maxdev/Streamlit_UI_Template/templates/generation.json', 'r') as f:
        data = json.load(f)
        st.session_state['data'] = data
    
    if st.session_state.step == 1:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.image("https://storage.googleapis.com/bucket-quickstart_maxs-first-project-408116/corum/no-property-img.webp", width=500)  # Adjust the width as needed
            submitted = st.button("Next",key="secondary")
            if submitted:
                next_step()

    elif st.session_state.step == 2:
        col1, col2 = st.columns([2,1])
        with col1:
            st.title("Where is the property located?")
            address = st.text_input("Enter the address of the property")
            st.session_state['address'] = address
            col_back, col_next = st.columns([1, 1])
            with col_next:
                submitted = st.button("Next")
            with col_back:
                back = st.button("Back")

            if submitted:
                next_step()
            if back:
                previous_step()

    elif st.session_state.step == 3:
        col1, col2 = st.columns([2,1])
        with col1:
            st.title("Please upload the floorplan of your property.")
            property_floorplan = st.file_uploader("Upload your floorplan",key="photos", type=["jpg", "jpeg", "png"])
            st.markdown("<br>", unsafe_allow_html=True)  # Add vertical spacing
            col_back, col_next = st.columns([1, 1])
            with col_next:
                submitted = st.button("Next")
            with col_back:
                back = st.button("Back")

            if submitted:
                next_step()
            if back:
                previous_step()

    elif st.session_state.step == 4:
        col1, col2 = st.columns([2,1])
        with col1:
            st.title("Please upload some photos of your property.")
            property_floorplan = st.file_uploader("Upload your floorplan",key="photos", type=["jpg", "jpeg", "png"])
            st.markdown("<br>", unsafe_allow_html=True)  # Add vertical spacing
            col_back, col_next = st.columns([1, 1])
            with col_next:
                submitted = st.button("Next")
            with col_back:
                back = st.button("Back")

            if submitted:
                next_step()
            if back:
                previous_step()

    elif st.session_state.step == 5:
            st.title("Layout and Specifications")
            st.write("Please confirm we've got the floor plan features correct. You can add or remove floor plan specifics as you see fit. This helps us to tailor a truly accurate listing description.")
            st.image("https://storage.googleapis.com/bucket-quickstart_maxs-first-project-408116/corum/OverleeRoad/all_floors_1_overlee_road_glasgow_with_dim-scaled.jpg", width=500)


            # Initialize session state for selected features
            if 'selected_features' not in st.session_state:
                st.session_state.selected_features = {}

            with st.form(key='floor_form'):
                # Iterate through the floorplan data
                for floor in data["floorplan"]:
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

                form_back, form_next = st.columns([1, 1])
                with form_back:
                    form_back_button = st.form_submit_button("Back")
                with form_next:
                    form_next_button = st.form_submit_button("Next")

                if form_next_button:
                    next_step()
                if form_back_button:
                    previous_step()

    elif st.session_state.step == 6:
        st.markdown("<a name='top'></a>", unsafe_allow_html=True)
        st.write("#")  # Empty space to scroll to
        col1, col2 = st.columns([2, 1])
        with col1:
            st.title("Your Property Summary.")
            st.write("We've summarized your property in 4 steps. Please verify you are happy with these points. You can add or remove as required.")

            # Add a text area for property overview
            property_overview = data.get("property_overview", "")
            property_overview = preprocess_text(property_overview)
            property_overview_text = st.text_area("Property Overview", value=property_overview, key="property_overview")

            external_features = data.get("external_features", "")
            external_features = preprocess_text(external_features)
            external_features_text = st.text_area("External Features", value=external_features, key="external_features")

            local_area_highlights = data.get("local_area_highlights", "")
            local_area_highlights = preprocess_text(local_area_highlights)
            local_area_highlights_text = st.text_area("Local Area Highlights", value=local_area_highlights, key="local_area_highlights")

            additional_notes_text = st.text_area("Please add any additional features you wish to add to the description.", key="additional_notes")

            col_back, col_next = st.columns([1, 1])
            with col_back:
                back = st.button("Back")
            with col_next:
                submitted = st.button("Next")

            if submitted:
                next_step()
            if back:
                previous_step()

    elif st.session_state.step == 7:
            st.title("Your Property Listing Description.")
            st.write(st.session_state['address'])
            st.image("https://storage.googleapis.com/bucket-quickstart_maxs-first-project-408116/corum/OverleeRoad/P1311672-Medium.jpg",width=500)
            
            with open('/Users/maxmodlin/maxdev/Streamlit_UI_Template/templates/description.txt', 'r') as f:
                desc = f.read()

            st.markdown(desc)
if __name__ == "__main__":  
    template1_page_style()
    main()  