import streamlit as st
import re
import webbrowser
from streamlit import download_button
import pyperclip
import json
from googletrans import Translator
import os
import pickle
import fitz  # PyMuPDF
from PIL import Image as PILImage
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_nvidia_ai_endpoints import NVIDIAEmbeddings, ChatNVIDIA
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains import create_retrieval_chain
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain.llms import CTransformers
from langchain.prompts import ChatPromptTemplate
import time
from dotenv import load_dotenv
from io import BytesIO
import base64
import speech_recognition as sr
import pyttsx3
import threading
import datetime
import sqlite3
import sendgrid
from sendgrid.helpers.mail import Mail, Email, To, Content
from twilio.rest import Client
from Health_Tip import create_health_tips_table, save_health_tip, get_all_health_tips,delete_health_tip
from functools import lru_cache
import random
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

# Load environment variables
load_dotenv()

# Ensure NVIDIA API key is set
os.environ['NVIDIA_API_KEY'] = os.getenv("NVIDIA_API_KEY")

# Access the environment variables
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")

# Initialize the translator
translator = Translator()


# Create the health_tips table in the database
create_health_tips_table()

# Function to convert image to base64 for display
def image_to_base64(image):
    from io import BytesIO
    import base64
    buffered = BytesIO()
    image.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode()

# Updated discussion forum (Baatcheet Bhavan) function that includes health tips
def discussion_forum():
    st.title("Doctor's Profile, Events & Health Tips")

    st.markdown(
        """
        <style>
            .stSidebar .stButton > button {
                background-color: #E83E8C;
                color: white;
            }
            .follow-button {
                background-color: #4CAF50;
                color: white;
                padding: 10px 20px;
                text-align: center;
                text-decoration: none;
                display: inline-block;
                font-size: 16px;
                margin: 4px 2px;
                cursor: pointer;
                border-radius: 5px;
            }
            .book-seat-button {
                background-color: #008CBA;
                color: white;
                padding: 10px 20px;
                text-align: center;
                text-decoration: none;
                display: inline-block;
                font-size: 16px;
                margin: 4px 2px;
                cursor: pointer;
                border-radius: 5px;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Back to chatbot button
    if st.sidebar.button("⏮ Back to Chatbot"):
        st.session_state.page = "main_chatbot"
        st.rerun()

    # Display the doctor's profile image
    doctor_image_path = "Doctor_Profile_Image.jpg"  # Replace with the actual path to the doctor's image
    st.image(doctor_image_path, use_column_width=True)

    # Display recommendations of doctors
    st.markdown("<h2 style='color: #008080;'>Recommended Doctors</h2>", unsafe_allow_html=True)

    # List of doctor names and images
    doctors = [
        {"name": "Dr. Smith", "image": "Dr-1.png"},
        {"name": "Dr. Johnson", "image": "Dr-2.png"},
    ]

    # Display each doctor with a follow button
    for doctor in doctors:
        col1, col2 = st.columns([1, 4])
        with col1:
            st.image(doctor["image"], width=100)
        with col2:
            st.write(doctor["name"])
            st.markdown(f"<button class='follow-button'>Follow {doctor['name']}</button>", unsafe_allow_html=True)

    # Create two columns for past and upcoming events
    col1, col2 = st.columns(2)

    # Past events in the first column
    with col1:
        st.markdown("<h3 style='color: #90EE90;'>Past Events</h3>", unsafe_allow_html=True)
        st.markdown("<p><b>Event Name:</b> Medical Conference</p>", unsafe_allow_html=True)
        st.markdown("<p><b>Venue:</b> City Hall</p>", unsafe_allow_html=True)
        st.markdown("<p><b>Timing:</b> Last Week</p>", unsafe_allow_html=True)
        st.markdown("<p><b>Discussion:</b> Latest Trends in Cardiology</p>", unsafe_allow_html=True)
        st.markdown("<button class='book-seat-button'>Book Your Seat</button>", unsafe_allow_html=True)

    # Upcoming events in the second column
    with col2:
        st.markdown("<h3 style='color: #90EE90;'>Upcoming Events</h3>", unsafe_allow_html=True)
        st.markdown("<p><b>Event Name:</b> Webinar on Diabetes</p>", unsafe_allow_html=True)
        st.markdown("<p><b>Venue:</b> Online</p>", unsafe_allow_html=True)
        st.markdown("<p><b>Timing:</b> Next Week</p>", unsafe_allow_html=True)
        st.markdown("<p><b>Discussion:</b> Managing Diabetes in the COVID-19 Era</p>", unsafe_allow_html=True)

    # Add a health tips section inside the discussion forum
    st.markdown("<h2 style='color: #FF6347;'>Health Tips</h2>", unsafe_allow_html=True)

    # Define a list of pre-uploaded articles
    pre_uploaded_articles = [
        {
            "title": "Can Your Tattoo Increase the Risk of Lymphoma? What You Need to Know",
            "content": "The number of adults in the US with at least one tattoo has risen dramatically in recent decades, so headlines about a study that found an association between having a tattoo and higher risk of lymphoma may have caused worry. However, understanding the study's limitations and methodology is crucial. The study's sample size and population demographics may have influenced the results.",
            "image_path": "./Pre-Uploaded Posts(Images)/Tatoo.jpg",
            "doctor_name": "Dr. Neha Sharma",
            "specialization": "Oncology",
            "date": "2023-07-25",
        },
        {
            "title": "Unlock the Secrets in Your Medical Records: Why You Should Start Reading Them Today",
            "content": "A balanced diet rich in fruits, vegetables, and whole grains can lead to better health outcomes and reduced risk of chronic diseases.",
            "image_path": "./Pre-Uploaded Posts(Images)/Medical_Records.jpg",
            "doctor_name": "Dr. Arvind Kumar",
            "specialization": "General Medicine",
            "date": "2022-04-12",
        },
        {
            "title": "Struggling with Curled Fingers? Understanding Dupuytren's Contracture",
            "content": "Dupuytren's contracture is where one or more fingers become curled, making everyday activities difficult. Treatment options range from observation to surgery, depending on severity.",
            "image_path": "./Pre-Uploaded Posts(Images)/Hand_Issue.jpg",
            "doctor_name": " Dr. Meenal Joshi",
            "specialization": "Orthopedics",
            "date": "2024-02-28",
        },
        {
            "title": "Is Your Child at Risk? Essential Tips on Identifying and Treating Concussions",
            "content": "Concussion care emphasizes rest, rehabilitation, and gradual return to activities. By being informed, parents and caregivers can help young athletes recover safely.",
            "image_path": "./Pre-Uploaded Posts(Images)/Teen_Health.jpg",
            "doctor_name": "Dr. Rakesh Mehta",
            "specialization": "Pediatrics",
            "date": "2023-10-19",
        },
    ]

    # Display pre-uploaded articles
    for i, article in enumerate(pre_uploaded_articles):
        container = st.container()
        container.markdown(
            f"""
            <div class="flex-container">
                <div class="image-container">
                    {f'<img src="data:image/jpeg;base64,{image_to_base64(PILImage.open(article["image_path"]))}" width="350">' if article["image_path"] else ''}
                    <div style="margin-top: 10px;">
                        <button style="margin-right: 5px;">Like</button>
                        <button style="margin-right: 5px;">Dislike</button>
                        <button>Comment</button>
                    </div>
                </div>
                <div class="content-container">
                    <h3>{article["title"]}</h3>
                    <p>By {article["doctor_name"]}, {article["specialization"]}</p>
                    <p>Posted: {article["date"]}</p>
                    <p>{article["content"]}</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Display likes, dislikes, and comments
        st.write(f"Likes: {article.get('likes', 250)}")
        st.write(f"Dislikes: {article.get('dislikes', 17)}")
        if "comments" in article:
            st.write("Comments:")
            for comment in article["comments"]:
                st.write(f"- {comment}")
    
        st.write("---")

    # Display doctor's posts from the database
    health_tips = get_all_health_tips()
    for i, health_tip in enumerate(health_tips):
        health_tip = {
            "id": health_tip[0],
            "doctor_name": health_tip[1],
            "specialization": health_tip[2],
            "content": health_tip[3],
            "image_path": health_tip[4],
            "date": health_tip[5],
        }

        container = st.container()
        container.markdown(
            f"""
            <div class="flex-container">
                <div class="image-container">
                    {f'<img src="data:image/jpeg;base64,{image_to_base64(PILImage.open(health_tip["image_path"]))}" width="350">' if health_tip["image_path"] else ''}
                    <div style="margin-top: 10px;">
                        <button style="margin-right: 5px;">Like</button>
                        <button style="margin-right: 5px;">Dislike</button>
                        <button>Comment</button>
                    </div>
                </div>
                <div class="content-container">
                    <p>By {health_tip["doctor_name"]}, {health_tip["specialization"]}</p>
                    <p>Posted: {health_tip["date"]}</p>
                    <p>{health_tip["content"]}</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button(f"🗑:{i+1}"):
            delete_health_tip(health_tip["id"])
            st.rerun()

    st.write("---")

    # Allow doctors to upload their own health tips
    with st.form("doctor_post_form"):
        doctor_name = st.text_input("Doctor Name")
        specialization = st.text_input("Specialization")
        content = st.text_area("Post Content", max_chars=100)
        image_file = st.file_uploader("Upload Image", type=["jpg", "jpeg", "png"])
        submit_button = st.form_submit_button("Upload Post")

        if submit_button:
            if doctor_name and specialization and content:
                image_path = None
                if image_file:
                    os.makedirs("uploads", exist_ok=True)
                    image_path = f"uploads/{image_file.name}"
                    with open(image_path, "wb") as f:
                        f.write(image_file.getbuffer())
                save_health_tip(doctor_name, specialization, content, image_path)
                st.success("Post saved successfully!")
                st.rerun()
            else:
                st.error("Please fill in all the required fields.")


from PIL import Image

def display_wellness_hunt():
    
    # Display the Wellness Hunt section title
    st.title("Wellness Hunt")

    st.markdown(
        """
        <style>
            .stSidebar .stButton > button {
                background-color: #E83E8C;
                color: white;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Back to chatbot button
    if st.sidebar.button("⏮ Back to Chatbot"):
        st.session_state.page = "main_chatbot"
        st.rerun()

    # Load the image
    image = PILImage.open("Gamify_changes.jpg")  # Replace "Gamify_changes.jpg" with the actual path to your image file

    # Display the image
    st.image(image, caption="Features of Wellness Hunt", use_column_width=True)

    # Load the images for the challenges
    quiz_image = Image.open("Quiz.jpg")
    crossword_image = Image.open("Crossword.jpg")
    fitness_diet_image = Image.open("Fitness & Diet.jpg")
    medical_memory_game_image = Image.open("Medical_Memory_Game.jpg")

    # Create a sidebar with buttons for the challenges
    st.sidebar.title("Challenges")
    challenge = st.sidebar.radio("Select a challenge", ("Quiz", "Crossword", "Fitness & Diet", "Medical Memory Game"))

    # Display the selected challenge and its description
    if challenge == "Quiz":
        st.image(quiz_image, caption="Quiz Challenge", use_column_width=True)
        st.write("Test your knowledge with a variety of medical trivia questions.")
    elif challenge == "Crossword":
        st.image(crossword_image, caption="Crossword Challenge", use_column_width=True)
        st.write("Exercise your brain with a medical-themed crossword puzzle.")
    elif challenge == "Fitness & Diet":
        st.image(fitness_diet_image, caption="Fitness & Diet Challenge", use_column_width=True)
        st.write("Improve your fitness and diet with a series of exercises and meal plans.")
    elif challenge == "Medical Memory Game":
        st.image(medical_memory_game_image, caption="Medical Memory Game Challenge", use_column_width=True)
        st.write("Test your memory with a game that matches medical terms with their definitions.")

def extract_citations(text):
    citations = re.findall(r'\[(.*?)\]', text)
    return ', '.join(citations)

def medical_records_section():
    st.header("Medical Records Upload")

    # Image/PDF Uploads
    st.subheader("Upload Medical Documents")

        # Add CSS for the back to chatbot button and other buttons
    st.markdown(
        """
        <style>
            .stSidebar .stButton > button {
                background-color: #E83E8C;
                color: white;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Back to chatbot button
    if st.sidebar.button("⏮ Back to Chatbot"):
        st.session_state.page = "main_chatbot"
        st.rerun()
    
    # Recent Lab Results
    lab_results = st.file_uploader("Upload Recent Lab Results (e.g., CBC, liver function test)", type=['pdf', 'jpg', 'png'], key="lab_results")
    
    # Medical Imaging
    medical_imaging = st.file_uploader("Upload Medical Imaging (X-rays, CT scans, MRIs, Ultrasound)", type=['pdf', 'jpg', 'png'], key="medical_imaging")
    
    # Vaccination History
    vaccination_history = st.file_uploader("Upload Vaccination History (official vaccination card or certificate)", type=['pdf', 'jpg', 'png'], key="vaccination_history")
    
    # ECG/Heart Rate Reports
    ecg_reports = st.file_uploader("Upload ECG/Heart Rate Reports", type=['pdf', 'jpg', 'png'], key="ecg_reports")
    
    # Prescription or Current Medications
    prescriptions = st.file_uploader("Upload Prescriptions or Current Medications", type=['pdf', 'jpg', 'png'], key="prescriptions")
    
    # Allergy Profile
    allergy_profile = st.file_uploader("Upload Documented Allergy Tests", type=['pdf', 'jpg', 'png'], key="allergy_profile")
    
    # Cholesterol Levels
    cholesterol_levels = st.file_uploader("Upload Cholesterol Levels Report", type=['pdf', 'jpg', 'png'], key="cholesterol_levels")

    # Text Input
    st.subheader("Enter Medical Information")
    
    # Blood Group
    blood_group = st.text_input("Blood Group", key="blood_group")
    
    # Blood Pressure
    blood_pressure = st.text_input("Blood Pressure (e.g., 120/80 mmHg)", key="blood_pressure")
    
    # Blood Sugar Levels
    blood_sugar = st.text_input("Blood Sugar Levels (mg/dL)", key="blood_sugar")
    
    # Body Mass Index (BMI)
    height = st.number_input("Height (cm)", key="height")
    weight = st.number_input("Weight (kg)", key="weight")
    if height and weight:
        bmi = round(weight / ((height / 100) ** 2), 2)
        st.write(f"Calculated BMI: {bmi}")
    
    # Hemoglobin Levels
    hemoglobin = st.text_input("Hemoglobin Levels (g/dL)", key="hemoglobin")
    
    # Allergies
    allergies = st.text_input("Allergies (e.g., peanuts, penicillin)", key="allergies")
    
    # Current Medications
    current_medications = st.text_area("Current Medications and Dosages", key="current_medications")
    
    # Organ Donor Status
    organ_donor = st.checkbox("Are you an organ donor?", key="organ_donor")

    # Display uploaded files and inputs (for debugging or further processing)
    st.subheader("Uploaded Files and Inputs Summary")
    if lab_results:
        st.write("Lab Results uploaded")
    if medical_imaging:
        st.write("Medical Imaging uploaded")
    if vaccination_history:
        st.write("Vaccination History uploaded")
    if ecg_reports:
        st.write("ECG/Heart Rate Reports uploaded")
    if prescriptions:
        st.write("Prescriptions uploaded")
    if allergy_profile:
        st.write("Allergy Profile uploaded")
    if cholesterol_levels:
        st.write("Cholesterol Levels uploaded")
    st.write(f"Blood Group: {blood_group}")
    st.write(f"Blood Pressure: {blood_pressure}")
    st.write(f"Blood Sugar Levels: {blood_sugar}")
    st.write(f"Height: {height} cm, Weight: {weight} kg, BMI: {bmi if height and weight else 'Not calculated'}")
    st.write(f"Hemoglobin Levels: {hemoglobin}")
    st.write(f"Allergies: {allergies}")
    st.write(f"Current Medications: {current_medications}")
    st.write(f"Organ Donor: {'Yes' if organ_donor else 'No'}")

def emergency_assist_section():
    st.title("Emergency Assist")

    # Back to chatbot button
    if st.sidebar.button("⏮ Back to Chatbot"):
        st.session_state.page = "main_chatbot"
        st.rerun()

    # Add CSS for the back to chatbot button and other buttons
    st.markdown(
        """
        <style>
            .stSidebar .stButton > button {
                background-color: #E83E8C;
                color: white;
            }
            .stButton > button {
                background-color: #008CBA;
                color: white;
                border: none;
                border-radius: 5px;
                text-align: center;
                text-decoration: none;
                display: inline-block;
                font-size: 18px;
                margin: 4px 2px;
                cursor: pointer;
            }
            .book-ambulance-button {
                background-color: #DC143C !important;
                color: white !important;
                border: none;
                border-radius: 5px;
                text-align: center;
                text-decoration: none;
                display: inline-block;
                font-size: 18px;
                margin: 4px 2px;
                cursor: pointer;
                padding: 0.5rem 1rem;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Create a database connection
    conn = sqlite3.connect('emergency_assist.db')
    c = conn.cursor()

    # Drop the table if it exists to recreate it with the correct schema
    c.execute('DROP TABLE IF EXISTS location_sharing')  # Add this line to drop the table

    # Create the tables if they do not exist
    c.execute('''CREATE TABLE IF NOT EXISTS emergency_contacts
                 (id INTEGER PRIMARY KEY,
                  name TEXT,
                  phone_number TEXT,
                  relationship TEXT)''')

    c.execute('''CREATE TABLE IF NOT EXISTS emergency_instructions
                 (id INTEGER PRIMARY KEY,
                  instructions TEXT)''')

    # Recreate the location_sharing table with the correct schema
    c.execute('''CREATE TABLE IF NOT EXISTS location_sharing
                 (id INTEGER PRIMARY KEY,
                  address TEXT)''')  # Ensure 'address' column exists

    # Emergency contacts form
    st.subheader("Emergency Contacts")
    name = st.text_input("Name")
    phone_number = st.text_input("Phone Number")
    relationship = st.text_input("Relationship")

    if st.button("Add Contact"):
        c.execute('''INSERT INTO emergency_contacts (name, phone_number, relationship)
                     VALUES (?, ?, ?)''', (name, phone_number, relationship))
        conn.commit()
        st.success("Contact added successfully!")

    # Emergency instructions form
    st.subheader("Emergency Instructions")
    instructions = st.text_area("Instructions")

    if st.button("Save Instructions"):
        c.execute('''DELETE FROM emergency_instructions''')
        c.execute('''INSERT INTO emergency_instructions (instructions)
                     VALUES (?)''', (instructions,))
        conn.commit()
        st.success("Instructions saved successfully!")

    # Location sharing form
    st.subheader("Location Sharing")
    address = st.text_area("Address (include landmarks)")

    if st.button("Share Location"):
        c.execute('''DELETE FROM location_sharing''')
        c.execute('''INSERT INTO location_sharing (address)
                     VALUES (?)''', (address,))
        conn.commit()
        st.success("Location shared successfully!")

    # Book ambulance button (using custom HTML)
    st.markdown(
        '<button class="book-ambulance-button" onclick="alert(\'Ambulance booked. It will arrive shortly.\')">Book Ambulance🏥</button>',
        unsafe_allow_html=True
    )

    # Close the database connection
    conn.close()

def generate_chat_history_text():
    chat_text = ""
    for sender, message in st.session_state["chat_history"]:
        chat_text += f"{sender}: {message}\n"
    return chat_text

def generate_chat_history_pdf():
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    
    # Create custom styles for user and bot messages
    styles.add(ParagraphStyle(name='User', 
                              parent=styles['Normal'],
                              textColor=colors.blue,
                              fontSize=12,
                              spaceAfter=6))
    styles.add(ParagraphStyle(name='Bot', 
                              parent=styles['Normal'],
                              textColor=colors.green,
                              fontSize=12,
                              spaceAfter=6))

    # Prepare the flowables
    flowables = []
    flowables.append(Paragraph("Dost Se Hui Charcha", styles['Title']))
    flowables.append(Spacer(1, 12))

    for sender, message in st.session_state["chat_history"]:
        if sender == "user":
            style = styles['User']
            prefix = "User: "
        else:
            style = styles['Bot']
            prefix = "Bot: "
        
        p = Paragraph(f"{prefix}{message}", style)
        flowables.append(p)

    # Build the PDF
    doc.build(flowables)
    buffer.seek(0)
    return buffer.getvalue()

@lru_cache(maxsize=100)
def generate_doctor_profile_html(student_tuple):
    # Unpack the tuple into individual variables
    name, specialization, education, experience, fee, availability, contact, languages, consultation_details, location, image_path, rating = student_tuple

    # Generate a random number for total reviews (e.g., between 50 and 500)
    total_reviews = random.randint(50, 500)

    # Generate a random number for total patients consulted (e.g., between 1000 and 5000)
    total_patients = random.randint(1000, 5000)

    # Create a flex container
    container = st.container()
    container.markdown(
        f"""
        <style>
            .flex-container {{
                display: flex;
                align-items: flex-start;
            }}
            .image-container {{
                flex: 1;
                padding-right: 10px;
                text-align: center;
            }}
            .content-container {{
                flex: 2;
            }}
            .heading {{
                color: #00FFFF;
                font-weight: bold;
            }}
            .star-rating {{
                color: #ddd;
                font-size: 24px;
            }}
            .star-rating .filled {{
                color: #ffd700;
            }}
        </style>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.3/css/all.min.css">
        <div class="flex-container">
            <div class="image-container">
                {f'<img src="data:image/jpg;base64,{image_to_base64(PILImage.open(image_path))}" width="350">' if image_path else ''}
            </div>
            <div class="content-container">
                {f'<h3>{name}</h3>'}
                <div class="star-rating">
                    {''.join(['<i class="fas fa-star filled"></i>' if i < rating else '<i class="fas fa-star"></i>' for i in range(5)])}
                    <span>({total_reviews} reviews, {total_patients} patients consulted)</span>
                </div>
                {f'<p><span class="heading">Specialization:</span> {specialization}</p>'}
                {f'<p><span class="heading">Education:</span> {education}</p>'}
                {f'<p><span class="heading">Experience:</span> {experience}</p>'}
                {f'<p><span class="heading">Consultation Fee:</span> {fee}</p>'}
                {f'<p><span class="heading">Availability:</span> {availability}</p>'}
                {f'<p><span class="heading">Contact:</span> {contact}</p>'}
                {f'<p><span class="heading">Languages Spoken:</span> {languages}</p>'}
                {f'<p><span class="heading">Consultation Details:</span> {consultation_details}</p>'}
                {f'<p><span class="heading">Location:</span> {location}</p>'}
                <button style="background-color: #4CAF50; color: white; padding: 14px 20px; text-align: center; text-decoration: none; display: inline-block; font-size: 16px; margin: 4px 2px; cursor: pointer;">Book Consultation</button>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
def consult_experts_section():
    st.title("MedMate")

    # Add a back button to the sidebar to come back to the main chatbot
    if st.sidebar.button("⏮ Back to Chatbot"):
        st.session_state.page = "main_chatbot"
        st.rerun()

    # Add CSS style block to set the background color for the back to chatbot button inside the sidebar
    st.markdown(
        """
        <style>
            .stSidebar .stButton > button {
                background-color: #E83E8C; /* Change this color to your desired color for the back to chatbot button */
                color: white;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

        # Add CSS style block with updated styles for equal spacing, disclaimer boundary, and bold block letter
    st.markdown(
        """
        <style>
            .disclaimer-heading {
                font-weight: bold;
                color: #FF0000;
                font-size: 20px;
                margin-top: 20px;
            }
            .disclaimer-content {
                border: 2px solid #FF0000;
                padding: 10px;
                border-radius: 5px;
                margin-top: 10px;
            }
            .disclaimer-content strong {
                font-weight: bold;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )
    # Add the disclaimer heading and text with a boundary and bold block letter
    st.sidebar.markdown('<p class="disclaimer-heading">Disclaimer</p>', unsafe_allow_html=True)
    st.sidebar.markdown('<div class="disclaimer-content"><p><strong>Our medical chatbot is designed to provide helpful information based on general knowledge and available data.</strong> However, please note that we are <strong>NOT CERTIFIED MEDICAL PROFESSIONALS</strong>, and the advice or information provided by this bot may not always be accurate or applicable to your specific health situation. Always consult with a qualified healthcare provider or physician for any medical concerns or before making decisions related to your health. Use this chatbot as a supplemental tool, but take the responses with a grain of salt—we can be wrong!</p></div>', unsafe_allow_html=True)

    # Add a "Register as Consultant" button to the sidebar with custom CSS
    st.sidebar.markdown(
        """
        <style>
            .register-button {
                background-color: #008CBA;
                color: white;
                padding: 14px 20px;
                border: none;
                border-radius: 5px;
                text-align: center
                cursor: pointer;
                font-size: 18px;
            }
        </style>
        <button class="register-button">Register as Consultant</button>
        """,
        unsafe_allow_html=True,
    )

    # Define a list of medical students with their details
    medical_students = [
        {
            "name": "Emily Carter",
            "specialization": "Neurology",
            "education": "4th-year medical student, specializing in Neurology",
            "experience": "Volunteered at a neurological research lab",
            "fee": "$35 per consultation",
            "availability": "Monday to Friday, 10 AM to 4 PM",
            "contact": "emily.carter@example.com",
            "languages": "English, German",
            "consultation_details": "30-minute video consultation. Provides general advice and guidance. Limitations: Cannot diagnose or treat serious medical conditions.",
            "location": "456 Oak Avenue, City, State, ZIP Code",
            "image_path": "./Consult_Experts/Doctor 1.jpg",
             "rating":3.5,
        },
        {
            "name": "Rahul Mehta",
            "specialization": "Cardiology",
            "education": "3rd-year medical student, specializing in Cardiology",
            "experience": "Internship at a cardiac care unit",
            "fee": "₹1500 per consultation",
            "availability": "Monday to Saturday, 9 AM to 5 PM",
            "contact": "rahul.mehta@example.com",
            "languages": "English, Hindi",
            "consultation_details": "45-minute video consultation. Provides general cardiac advice and lifestyle changes. Limitations: Cannot prescribe medication or perform procedures.",
            "location": "789 Park Lane, City, State, ZIP Code",
            "image_path": "./Consult_Experts/Doctor 2.jpg", 
             "rating": 4,
        },
        {
            "name": "Anjali Sharma",
            "specialization": "Gynecology",
            "education": "3rd-year medical student, specializing in Gynecology",
            "experience": "Assisted in a maternity ward during clinical rotations",
            "fee": "₹1200 per consultation",
            "availability": "Monday to Friday, 10 AM to 4 PM",
            "contact": "anjali.sharma@example.com",
            "languages": "English, Hindi",
            "consultation_details": "30-minute video consultation. Provides general advice on reproductive health. Limitations: Cannot prescribe medication or perform any medical procedures.",
            "location": "123 Green Street, City, State, ZIP Code",
            "image_path": "./Consult_Experts/Doctor 3.jpg",
             "rating": 4.3,
        },
        {
            "name": "Dr. Arjun Nair",
            "specialization": "Orthopedics",
            "education": "MBBS, MS in Orthopedics",
            "experience": "3 years working in a leading orthopedic hospital",
            "fee": "₹2000 per consultation",
            "availability": "Monday to Friday, 11 AM to 6 PM",
            "contact": "arjun.nair@example.com",
            "languages": "English, Malayalam, Hindi",
            "consultation_details": "30-minute consultation. Specializes in bone health and orthopedic injuries. Provides treatment plans and second opinions. Limitations: Does not perform surgery via consultation.",
            "location": "456 Elm Road, City, State, ZIP Code",
            "image_path": "./Consult_Experts/Doctor_Older 1.jpg",
             "rating": 3.9,
        },
        {
            "name": "Dr. Priya Desai",
            "specialization": "Dermatology",
            "education": "MBBS, MD in Dermatology",
            "experience": "4 years working at a private dermatology clinic",
            "fee": "₹2500 per consultation",
            "availability": "Tuesday to Saturday, 12 PM to 6 PM",
            "contact": "priya.desai@example.com",
            "languages": "English, Marathi, Hindi",
            "consultation_details": "45-minute consultation. Specializes in skin treatments, acne, and cosmetic dermatology. Limitations: Does not perform invasive procedures online.",
            "location": "789 Palm Avenue, City, State, ZIP Code",
            "image_path": "./Consult_Experts/Doctor_Older 2.jpg",
             "rating": 3.7,
        },
        {
            "name": "Dr. Michael Brown",
            "specialization": "Pulmonology",
            "education": "MBBS, MD in Pulmonology",
            "experience": "5 years working in respiratory health",
            "fee": "$40 per consultation",
            "availability": "Monday to Friday, 9 AM to 5 PM",
            "contact": "michael.brown@example.com",
            "languages": "English, French",
            "consultation_details": "60-minute consultation. Specializes in respiratory diseases, asthma, and chronic obstructive pulmonary disease (COPD). Provides treatment options and lifestyle changes.",
            "location": "123 Maple Boulevard, City, State, ZIP Code",
            "image_path": "./Consult_Experts/Doctor_Older 3.jpg",
             "rating": 4.8,
        },
    ]

    # Display medical student's details
    st.subheader("Medical Interns")
    for i, student in enumerate(medical_students[:3]):
        # Convert the student dictionary into a tuple
        student_tuple = (
            student["name"],
            student["specialization"],
            student["education"],
            student["experience"],
            student["fee"],
            student["availability"],
            student["contact"],
            student["languages"],
            student["consultation_details"],
            student["location"],
            student["image_path"],
            student["rating"],
        )

        # Generate the HTML content for the doctor's profile using the cached function
        generate_doctor_profile_html(student_tuple)

        # Add a feedback form for each doctor
        with st.form(f"feedback_form_{i}"):
            feedback = st.text_area("Feedback (Optional)", help="Share your thoughts or suggestions here.")
            submit_button = st.form_submit_button("Submit Feedback")

            if submit_button:
                # Process the feedback (you can save it to a database or send it to an email)
                st.success("Feedback submitted successfully!")

        st.write("---")

    # Display experts' details
    st.subheader("Experts")
    for i, student in enumerate(medical_students[3:]):
        # Convert the student dictionary into a tuple
        student_tuple = (
            student["name"],
            student["specialization"],
            student["education"],
            student["experience"],
            student["fee"],
            student["availability"],
            student["contact"],
            student["languages"],
            student["consultation_details"],
            student["location"],
            student["image_path"],
            student["rating"],
        )

        # Generate the HTML content for the doctor's profile using the cached function
        generate_doctor_profile_html(student_tuple)

        # Add a feedback form for each doctor
        with st.form(f"feedback_form_{i+3}"):
            feedback = st.text_area("Feedback (Optional)", help="Share your thoughts or suggestions here.")
            submit_button = st.form_submit_button("Submit Feedback")

            if submit_button:
                # Process the feedback (you can save it to a database or send it to an email)
                st.success("Feedback submitted successfully!")

        st.write("---")

# Updated categories and file names
CATEGORIES = [
    "Veterinary Medicine",
    "Cardiology",
    "Dermatology",
    "Pulmonology",
    "Infectious Diseases",
    "Emergency Medicine",
    "Oncology",
    "Rheumatology",
    "Neurology",
    "Endocrinology",
    "Pediatrics",
    "Orthopedics",
    "Gastroenterology",
    "General Medicine",
    "Psychiatry",
    "Obstetrics and Gynecology"
]

# Example help texts (these can be dynamically populated from functions)
CATEGORY_HELP = {
    "Veterinary Medicine": "Veterinary Medicine focuses on animal health and diseases.",
    "Cardiology": "Cardiology deals with disorders of the heart and blood vessels.",
    "Dermatology": "Dermatology is the branch of medicine focused on skin issues.",
    "Pulmonology": "Pulmonology is concerned with diseases of the respiratory system.",
    "Infectious Diseases": "Infectious Diseases deals with infections caused by bacteria, viruses, fungi, and parasites.",
    "Emergency Medicine": "Emergency Medicine involves immediate decision-making and action to prevent death or further disability.",
    "Oncology": "Oncology is the study and treatment of cancer.",
    "Rheumatology": "Rheumatology deals with the diagnosis and therapy of rheumatic diseases.",
    "Neurology": "Neurology is concerned with disorders of the nervous system.",
    "Endocrinology": "Endocrinology focuses on hormones and the endocrine system.",
    "Pediatrics": "Pediatrics focuses on the health and medical care of infants, children, and adolescents.",
    "Orthopedics": "Orthopedics deals with conditions involving the musculoskeletal system.",
    "Gastroenterology": "Gastroenterology is focused on the digestive system and its disorders.",
    "General Medicine": "General Medicine involves the diagnosis and treatment of adult diseases.",
    "Psychiatry": "Psychiatry is devoted to the diagnosis, prevention, study, and treatment of mental disorders.",
    "Obstetrics and Gynecology": "Obstetrics and Gynecology focus on female reproductive health, pregnancy, and childbirth."
}

# Paths
VECTOR_STORE_PATH = {category: f"{category.lower().replace(' ', '_')}_vector_store.pkl" for category in CATEGORIES}
DATA_DIR = {
    "Veterinary Medicine": "./data/veterinary_medicine_book.pdf",
    "Cardiology": "./data/Cardiology.pdf",
    "Dermatology": "./data/Dermatology.pdf",
    "Pulmonology": "./data/Pulmonology.pdf",
    "Infectious Diseases": "./data/Infectious Diseases.pdf",
    "Emergency Medicine": "./data/Emergency Medicine.pdf",
    "Oncology": "./data/Oncology.pdf",
    "Rheumatology": "./data/Rheumatology.pdf",
    "Neurology": "./data/Neurology.pdf",
    "Endocrinology": "./data/Endocrinology.pdf",
    "Pediatrics": "./data/Pediatrics.pdf",
    "Orthopedics": "./data/Orthopedics.pdf",
    "Gastroenterology": "./data/Gastroenterology.pdf",
    "General Medicine": "./data/General Medicine.pdf",
    "Psychiatry": "./data/Psychiatry.pdf",
    "Obstetrics and Gynecology": "./data/Obstetrics and Gynecology.pdf"
}
TEMP_UPLOAD_DIR = "temp_uploads"
MEDICINE_IMAGES_DIR = "medicine_images"

# Initialize text-to-speech engine
engine = pyttsx3.init()

# Create a Function to Set Up the Database:(For Medication Reminder)
def create_database():
    conn = sqlite3.connect('reminders.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS reminders
                 (id INTEGER PRIMARY KEY,
                  medicine_name TEXT,
                  dosage TEXT,
                  frequency TEXT,
                  start_date DATE,
                  reminder_times TEXT,
                  end_date DATE,
                  reminder_message TEXT,
                  reminder_type TEXT,
                  snooze_option BOOLEAN,
                  snooze_duration INTEGER,
                  notes TEXT,
                  uploaded_file_name TEXT,
                  uploaded_file_type TEXT)''')
    conn.commit()
    conn.close()

# Save the User Input to the Database:(For Medication Reminder)
def save_reminder(reminder_data):
    conn = sqlite3.connect('reminders.db')
    c = conn.cursor()

    # Convert reminder_times from datetime.time to a string format before saving
    reminder_times_str = reminder_data["Reminder Time(s)"].strftime('%H:%M')

    # Save the uploaded file details to the database
    uploaded_file_name = reminder_data["Uploaded File"]["Filename"] if reminder_data["Uploaded File"] else None
    uploaded_file_type = reminder_data["Uploaded File"]["FileType"] if reminder_data["Uploaded File"] else None

    # Insert the reminder data into the database
    c.execute('''INSERT INTO reminders (medicine_name, dosage, frequency, start_date, reminder_times,
                                         end_date, reminder_message, reminder_type, snooze_option,
                                         snooze_duration, notes, uploaded_file_name, uploaded_file_type)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
              (reminder_data["Medicine Name"], reminder_data["Dosage"], reminder_data["Frequency"],
               reminder_data["Start Date"], reminder_times_str,
               reminder_data["End Date"], reminder_data["Reminder Message"],
               reminder_data["Type of Reminder"], reminder_data["Snooze Option"],
               reminder_data["Snooze Duration"], reminder_data["Notes/Instructions"],
               uploaded_file_name, uploaded_file_type))

    conn.commit()
    conn.close()

# Retrieve and Display Saved Medication Reminders:
def get_all_reminders():
    conn = sqlite3.connect('reminders.db')
    c = conn.cursor()
    c.execute('SELECT * FROM reminders')
    reminders = c.fetchall()
    conn.close()
    return reminders

def display_saved_reminders():
    reminders = get_all_reminders()
    st.subheader("Saved Reminders")
    for reminder in reminders:
        st.write(f"Medicine Name: {reminder[1]}")
        st.write(f"Dosage: {reminder[2]}")
        st.write(f"Frequency: {reminder[3]}")
        st.write(f"Start Date: {reminder[4]}")
        st.write(f"Reminder Times: {reminder[5]}")
        st.write(f"End Date: {reminder[6]}")
        st.write(f"Reminder Message: {reminder[7]}")
        st.write(f"Reminder Type: {reminder[8]}")
        st.write(f"Snooze Option: {'Yes' if reminder[9] else 'No'}")
        st.write(f"Snooze Duration: {reminder[10]} minutes" if reminder[9] else "")
        st.write(f"Notes/Instructions: {reminder[11]}")
        if reminder[12]:
            if reminder[13] == "application/pdf":
                st.write("Uploaded File: PDF file uploaded")
            else:
                try:
                    st.image(f"{reminder[12]}", caption="Uploaded Image", use_column_width=True)
                except Exception as e:
                    st.error(f"Error displaying image: {e}")
        st.write("---")

# For Medication Reminder Type-->Email
def send_email_notification(to_email, subject, body):
    sg = sendgrid.SendGridAPIClient(api_key=os.getenv("SENDGRID_API_KEY"))
    from_email = Email("your-email@example.com")  # Change to your verified sender email
    to_email = To(to_email)
    content = Content("text/plain", body)
    mail = Mail(from_email, to_email, subject, content)

    try:
        response = sg.send(mail)
        print(f"Email sent with status code {response.status_code}")
    except Exception as e:
        print(f"Error sending email: {e}")

def send_voice_notification(to_phone, message):
    client = Client(os.getenv("TWILIO_ACCOUNT_SID"), os.getenv("TWILIO_AUTH_TOKEN"))

    call = client.calls.create(
        twiml=f'<Response><Say>{message}</Say></Response>',
        to=to_phone,
        from_='+13215045273'  # Replace with your Twilio phone number
    )

    print(f"Call initiated with SID {call.sid}")

def speak_text(text):
    """Speak the given text."""
    engine.say(text)
    engine.runAndWait()

def listen_for_speech():
    """Listen for speech and return the recognized text."""
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        st.write("Listening... Speak now.")
        audio = recognizer.listen(source)
    try:
        text = recognizer.recognize_google(audio)
        return text
    except sr.UnknownValueError:
        st.error("Sorry, I couldn't understand that.")
        return ""
    except sr.RequestError:
        st.error("Sorry, there was an error with the speech recognition service.")
        return ""

def image_to_base64(img):
    """Convert a PIL Image to base64 string."""
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()

def load_pdf(file_path):
    """Extract text from a PDF file using PyMuPDF."""
    doc = fitz.open(file_path)
    text = ""
    for page in doc:
        text += page.get_text()
    return text

def load_pdfs_from_path(path):
    """Load and process PDFs from a directory or a single PDF file."""
    documents = []
    if os.path.isfile(path) and path.endswith('.pdf'):
        text = load_pdf(path)
        documents.append(Document(page_content=text, metadata={"source": os.path.basename(path)}))
    else:
        raise ValueError(f"Invalid path: {path}. It should be a PDF file.")
    return documents

def process_uploaded_file(uploaded_file, category):
    """Process and add an uploaded PDF to the vector store."""
    if uploaded_file is not None:
        with st.spinner('Processing uploaded document...'):
            os.makedirs(TEMP_UPLOAD_DIR, exist_ok=True)
            file_path = os.path.join(TEMP_UPLOAD_DIR, uploaded_file.name)
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            new_text = load_pdf(file_path)
            new_doc = Document(page_content=new_text, metadata={"source": uploaded_file.name})

            if f"{category}_vectors" not in st.session_state or st.session_state[f"{category}_vectors"] is None:
                initialize_vector_store(category)

            if f"{category}_vectors" in st.session_state and st.session_state[f"{category}_vectors"] is not None:
                text_splitter = RecursiveCharacterTextSplitter(
                    chunk_size=300,
                    chunk_overlap=50,
                    length_function=len,
                    separators=["\n\n", "\n", " ", ""]
                )
                new_splits = text_splitter.split_documents([new_doc])
                st.session_state[f"{category}_vectors"].add_documents(new_splits)

                num_docs = len(st.session_state[f"{category}_vectors"].docstore._dict)
                st.write(f"Total documents in vector store: {num_docs}")

                with open(VECTOR_STORE_PATH[category], "wb") as f:
                    pickle.dump(st.session_state[f"{category}_vectors"], f)

                st.success(f"File '{uploaded_file.name}' processed and added to the {category} knowledge base.")
            else:
                st.error(f"Failed to initialize {category} vector store. Please check your data directory.")

def initialize_vector_store(category):
    """Load or create the vector store for the specified category."""
    if f"{category}_vectors" not in st.session_state or st.session_state[f"{category}_vectors"] is None:
        if os.path.exists(VECTOR_STORE_PATH[category]):
            with open(VECTOR_STORE_PATH[category], "rb") as f:
                st.session_state[f"{category}_vectors"] = pickle.load(f)
            st.write(f"Your Very Own Health Companion is ready to help 🫂.")
        else:
            st.write(f"Creating new {category} vector store from existing books. This may take a while...")
            documents = load_pdfs_from_path(DATA_DIR[category])
            if documents:
                embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
                text_splitter = RecursiveCharacterTextSplitter(
                    chunk_size=300,
                    chunk_overlap=50,
                    length_function=len,
                    separators=["\n\n", "\n", " ", ""]
                )
                splits = text_splitter.split_documents(documents)
                st.session_state[f"{category}_vectors"] = FAISS.from_documents(splits, embeddings)

                with open(VECTOR_STORE_PATH[category], "wb") as f:
                    pickle.dump(st.session_state[f"{category}_vectors"], f)
                st.write(f"Created and saved new {category} vector store.")
            else:
                st.write(f"No documents found in {category} book path.")

def process_medicine_image(uploaded_file):
    """Process and save the uploaded medicine image."""
    if uploaded_file is not None:
        with st.spinner('Processing uploaded image...'):
            os.makedirs(MEDICINE_IMAGES_DIR, exist_ok=True)
            file_path = os.path.join(MEDICINE_IMAGES_DIR, uploaded_file.name)
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            st.success(f"File '{uploaded_file.name}' processed and saved.")
            return file_path

def setup_medication_reminder():
    st.title("Medication Reminder⏰")

    # Add CSS style block to set the background color for the back to chatbot button inside the sidebar
    st.markdown(
        """
        <style>
            .stSidebar .stButton > button {
                background-color: #E83E8C; /* Change this color to your desired color for the back to chatbot button */
                color: white;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Add a button to navigate back to the main chatbot interface
    if st.sidebar.button("⏮Back to chatbot"):
        st.session_state.page = "main_chatbot"
        st.rerun()
    
    # Display the two images above the upload medicine feature
    col1, col2 = st.columns(2)
    col1.image("Health_Status.png", use_column_width=True,width=50)
    col2.image("Medication_Tracker.png", use_column_width=True,width=50)

    # Create the database if it doesn't exist
    create_database()

    # Medicine Image Upload
    st.subheader("Upload Medicine Image")
    uploaded_file = st.file_uploader("Upload an image (JPG) or a PDF file", type=['jpg', 'pdf'], key="med_image_upload_reminder")

    if uploaded_file:
        file_details = {"Filename": uploaded_file.name, "FileType": uploaded_file.type}
        st.write(file_details)
        uploaded_file_path = process_medicine_image(uploaded_file)  # Use process_medicine_image function

    # Medicine Name
    medicine_name = st.text_input("Medicine Name", key="med_name")

    # Dosage
    dosage = st.text_input("Dosage", key="dosage")

    # Frequency
    frequency_options = ["Once a day", "Twice a day", "Other"]
    frequency = st.selectbox("Frequency", frequency_options, key="frequency")

    # If "Other" is selected, allow the user to input their own frequency
    if frequency == "Other":
        custom_frequency = st.text_input("Please specify the frequency", key="custom_frequency")
    else:
        custom_frequency = frequency

    # Start Date
    start_date = st.date_input("Start Date", datetime.date.today(), key="start_date")

    # Reminder Time(s)
    reminder_times = st.time_input("Reminder Time(s)", value=datetime.time(8, 0), key="reminder_time")

    # End Date
    end_date = st.date_input("End Date", key="end_date")

    # Reminder Message
    reminder_message = st.text_input("Reminder Message", "Take your medication", key="reminder_message")

    # Type of Reminder
    reminder_type = st.selectbox("Type of Reminder", ["Notification", "Email", "Voice Reminder"], key="reminder_type")

    # Snooze Option
    snooze_option = st.checkbox("Snooze Option", key="snooze_option")
    if snooze_option:
        snooze_duration = st.number_input("Snooze Duration (minutes)", min_value=1, value=5, key="snooze_duration")

    # Notes/Instructions
    notes = st.text_area("Notes/Instructions", key="notes")

    # Save the reminder setup
    if st.button("Save Reminder", key="save_reminder"):
        # Save the reminder setup to the database
        reminder_data = {
            "Medicine Name": medicine_name,
            "Dosage": dosage,
            "Frequency": custom_frequency,
            "Start Date": start_date,
            "Reminder Time(s)": reminder_times,
            "End Date": end_date,
            "Reminder Message": reminder_message,
            "Type of Reminder": reminder_type,
            "Snooze Option": snooze_option,
            "Snooze Duration": snooze_duration if snooze_option else None,
            "Notes/Instructions": notes,
            "Uploaded File": {"Filename": uploaded_file_path, "FileType": uploaded_file.type} if uploaded_file else None,
        }
        save_reminder(reminder_data)
        st.success("Reminder setup saved successfully!")

        # Display the saved reminders
        display_saved_reminders()

        # Send notification based on the selected type
        if reminder_type == "Email":
            email = st.text_input("Enter your email address for notification")
            if email:
                send_email_notification(email, "Medication Reminder", reminder_message)
                st.success("Email notification sent!")
        elif reminder_type == "Voice Reminder":
            phone_number = st.text_input("Enter your phone number for voice reminder")
            if phone_number:
                send_voice_notification(phone_number, reminder_message)
                st.success("Voice reminder call initiated!")

def get_image_path(category):
    image_paths = {
        "Cardiology": "./Bot_Avatars/Cardiology_avatar-modified.png",
        "Dermatology": "./Bot_Avatars/Dermatology_avatar-modified.png",
        "Emergency Medicine": "./Bot_Avatars/Emergency Medicine_avatar-modified.png",
        "Endocrinology": "./Bot_Avatars/Endocrinology_avatar-modified.png",
        "Gastroenterology": "./Bot_Avatars/Gastroenterology_avatar.png",
        "General Medicine": "./Bot_Avatars/General Medicine_avatar-modified.png",
        "Infectious Diseases": "./Bot_Avatars/Infectious Diseases_avatar.png",
        "Neurology": "./Bot_Avatars/Neurology_avatar-modified.png",
        "Obstetrics and Gynecology": "./Bot_Avatars/onstetrics and gynecology_avatar-modified.png",
        "Oncology": "./Bot_Avatars/Oncology_avatar-modified.png",
        "Orthopedics": "./Bot_Avatars/Orthopedics_avatar-modified.png",
        "Pediatrics": "./Bot_Avatars/Pediatrics_avatar-modified.png",
        "Psychiatry": "./Bot_Avatars/Psychiatry_avatar-modified.png",
        "Pulmonology": "./Bot_Avatars/Pulmonology_avatar-modified.png",
        "Rheumatology": "./Bot_Avatars/Rheumatology_avatar-modified.png",
        "Veterinary Medicine": "./Bot_Avatars/veterinary_avatar-modified.png",
        
    }
    return image_paths.get(category, "")

def main_chatbot_interface():
    st.title("DoctorKaDost🫂")

    # Add a dropdown menu for language selection
    languages = ["English", "Hindi", "Spanish", "French", "German"]
    selected_language = st.selectbox("Select Language", languages)

    # Display the selected language
    st.write(f"Selected Language: {selected_language}")

    # Add CSS style block for chat interface and buttons
    st.markdown(
        """
        <style>
            .stSidebar .stButton > button {
                background-color: #008000; /* Green color for other sidebar buttons */
                color: white;
            }
            .stTextInput > div > div > button {
                background-color:#4B0082; /* Send button */
                color: white;
            }
            .stButton > button {
                background-color:#4B0082; /* Mic button */
                color: white;
            }
            .chat-message {
                padding: 10px 15px;
                border-radius: 18px;
                margin-bottom: 10px;
                display: inline-block;
                max-width: 70%;
                word-wrap: break-word;
                font-weight: bold; /* Make the font bold */
            }
            .bot-message {
                background-color: #d3d3d3; /* Light blue for bot messages */
                color: black;
                float: left;
                clear: both;
            }
            .user-message {
                background-color: #00E5FF; /* Light green for user messages */
                color: black;
                float: right;
                clear: both;
            }
            /* Clear float after messages */
            .chat-container::after {
                content: "";
                display: table;
                clear: both;
            }
            .response-buttons {
                display: flex;
                justify-content: flex-start;
                gap: 5px;  /* Reduced gap between buttons */
                margin-top: 2px;
            }
            .response-button {
                border: none;
                background: none;
                cursor: pointer;
                font-size: 18px;
                padding: 2px;
                opacity: 0.7;
                transition: opacity 0.3s;
            }
            .response-button:hover {
                opacity: 1;
            }
        </style>
        """,
        unsafe_allow_html=True
    )

    # Function to handle button clicks
    def handle_button_click(action, message):
        if action == 'like':
            st.toast("Response liked!", icon="👍")
        elif action == 'dislike':
            st.toast("Response disliked!", icon="👎")
        elif action == 'copy':
            pyperclip.copy(message)
            st.toast("Response copied to clipboard!", icon="📋")
    
    #Made with 💙
    st.sidebar.markdown("<h6 style='text-align: left; font-size: 22px;'>By Team GRM💙</h6>", unsafe_allow_html=True)
        
    #Health Dashboard
    st.sidebar.markdown(
        """
        <style>
            .health-dashboard {
                border: 4px solid #007BFF; /* Adjust the border color as needed */
                padding: 10px;
                border-radius: 5px;
                margin-bottom: 15px;
                display: flex;
                align-items: center;
                justify-content: center;
                text-align:center;
                height: 50px; /* Adjust height to ensure it fits the text properly */
                width: 100%; /* Ensures it uses all available space */
                box-sizing: border-box; /* Ensures padding is included in width/height */
            }
        </style>
        <div class="health-dashboard">
            <h6 style='text-align: center; font-size: 22px; margin: 0;    padding-top: 15px;'>Health Dashboard</h6>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Add a button to navigate to the "Consult Experts" section
    if st.sidebar.button("Consult Experts 👨‍⚕"):
        st.session_state.page = "consult_experts"
        st.rerun()
    
    # Add a button for the symptom checker in the sidebar
    if st.sidebar.button("Symptom Checker"):
        # Open the symptom checker in a new tab or window
        webbrowser.open_new_tab("http://localhost:3000")

    # Add a Discussion Forum button to the sidebar
    if st.sidebar.button("Baatcheet Bhavan💬"):
        st.session_state.page = "discussion_forum"
        st.rerun()

    # Add a button for the Wellness Hunt section in the sidebar
    if st.sidebar.button("Wellness Hunt 🏆"):
        st.session_state.page = "wellness_hunt"
        st.rerun()

    # Add a medical recors button to the sidebar    
    if st.sidebar.button("Medical Records 📁"):
       st.session_state.page = "medical_records"
       st.rerun()

    # Add an emergency assist button to the sidebar    
    if st.sidebar.button("Emergency Assist 🚑"):
        st.session_state.page = "emergency_assist"
        st.rerun()

    # Add a button to navigate to the medication reminder interface
    if st.sidebar.button("Medication Reminder 🔔"):
        st.session_state.page = "medication_reminder"
    
    # Load and display the logo at the center
    logo_path = "./Talaash.png"
    logo_base64 = None
    if os.path.exists(logo_path):
        logo_image = PILImage.open(logo_path)
        logo_base64 = image_to_base64(logo_image)

    if logo_base64:
        st.markdown(
            f"""
            <div style="display: flex; justify-content: center; align-items: center; background-color: transparent; padding: 10px 0;">
                <img src="data:image/png;base64,{logo_base64}" style="height: 180px; width: auto;">
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("<h3 style='text-align: center; font-weight: bold;'>AI Ka Haath, Aapki Sehat Se Saath</h3>", unsafe_allow_html=True)

    # Sort the categories alphabetically
    sorted_categories = sorted(CATEGORIES)

    # Display the dropdown menu
    category = st.selectbox("Select Medical Specialization", sorted_categories)
    
    # Display the help text for the selected category as an info box
    st.info(CATEGORY_HELP[category])

    initialize_vector_store(category)

    with st.sidebar:
        uploaded_file = st.file_uploader(f"Upload additional document for {category} questions", type=['pdf'], key=f"additional_doc_{category}")

        if uploaded_file:
            if st.button("Process Documents"):
                process_uploaded_file(uploaded_file, category)

    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = []

    if not st.session_state["chat_history"]:
        st.session_state["chat_history"].append(("bot", "Hi, I am Medical Bot. What is your Query?"))

    # Display chat history with buttons and image
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    for i, item in enumerate(st.session_state["chat_history"]):
        if isinstance(item, tuple) and len(item) == 2:
            sender, message = item
            if sender == "user":
                st.markdown(f"<div class='chat-message user-message'>{message}</div>", unsafe_allow_html=True)
            else:
                # Display the image and the response text side by side
                image_path = get_image_path(category)
                if image_path:
                    image_base64 = image_to_base64(PILImage.open(image_path))
                    st.markdown(
                        f"""
                        <div class='chat-message bot-message'>
                            <img src='data:image/png;base64,{image_base64}' width='50' height='50' style='float: left; margin-right: 10px;'>
                            {message}
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                else:
                    st.markdown(f"<div class='chat-message bot-message'>{message}</div>", unsafe_allow_html=True)
                
                # Add buttons based on the message type and Only add buttons if it's not the first (greeting) message
                if i != 0 and message != "Here are some follow-up questions you might find helpful:": 
                    st.markdown('<div class="response-buttons">', unsafe_allow_html=True)
                    if message.startswith(('1.', '2.')):
                        # Only copy button for follow-up message and questions
                        if st.button("📋", key=f"copy_{i}"):
                            handle_button_click('copy', message)
                    else:
                        # All buttons for other messages
                        col1, col2, col3 = st.columns([1, 1, 1])
                        with col1:
                            if st.button("👍", key=f"like_{i}"):
                                handle_button_click('like', message)
                        with col2:
                            if st.button("👎", key=f"dislike_{i}"):
                                handle_button_click('dislike', message)
                        with col3:
                            if st.button("📋", key=f"copy_{i}"):
                                handle_button_click('copy', message)
                    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Load the user image
    user_image_path = "./patient.png"  # Replace with the path to your image
    user_image = PILImage.open(user_image_path)
    user_image_base64 = image_to_base64(user_image)


    # Initialize prompt1 in session state if it doesn't exist
    if "prompt1" not in st.session_state:
        st.session_state.prompt1 = ""

    # Add custom CSS to control input width and alignment
    st.markdown(
        """
        <style>
        .stTextInput {
            position: relative;
            top: -20px;  /* Adjusted for better vertical alignment */
            left: -10px;  /* Move the text input slightly to the left */
            max-width: 70%;  /* Limit the width of the text input */
        }
        .stImage {
            margin-right: -20px;  /* Reduce space to the right of the image */
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    # Create a container for the input field and image
    input_container = st.container()

    # Use columns to align the image and text input with less space between them
    col1, col2, col3 = input_container.columns([0.3, 3.7, 0.8])  # Adjusted ratio for tighter spacing and limited width

    # Display the user image in the first column
    col1.image(user_image, width=47)  # Slightly reduced image size

    # Text input for the question in the second column
    prompt1 = col2.text_input("Enter Your Query", key="user_input")

    # Add custom CSS to align the image and input field with less space
    st.markdown(
        """
        <style>
        .stTextInput {
            position: relative;
            top: -20px;  /* Adjusted for better vertical alignment */
            left: -10px;  /* Move the text input slightly to the left */
        }
        .stImage {
            margin-right: -20px;  /* Reduce space to the right of the image */
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    # Voice input button
    if st.button("🎙"):
        voice_input = listen_for_speech()
        if voice_input:
            st.session_state.prompt1 = voice_input
            st.rerun()

    if st.button("▶"):
        if prompt1:
            st.session_state["chat_history"].append(("user", prompt1))

            # Translate the user's input to English
            user_input_translated = translator.translate(prompt1, dest='en').text

            if prompt1.lower() in ["hi", "hello", "what's up", "how are you", "hii"]:
                response = "I'm here to assist you with medical queries. What can I help you with?"

             # Translate the response to the selected language
                response_translated = translator.translate(response, dest=selected_language.lower()).text
                st.session_state["chat_history"].append(("bot", response_translated))

            else:
                if f"{category}_vectors" in st.session_state and st.session_state[f"{category}_vectors"] is not None:
                    llm = ChatNVIDIA(model="meta/llama3-70b-instruct")
                
                    # Modify the prompt template to include a placeholder for citations
                    prompt = ChatPromptTemplate.from_template("""
                        Answer the questions based on the provided context only. Please provide the most accurate response based on the question ideally under 300-400 words. Include citations in the response.
                        <context>
                        {context}
                        </context>
                        Question: {input}
                    """)
                    document_chain = create_stuff_documents_chain(llm, prompt)
                    retriever = st.session_state[f"{category}_vectors"].as_retriever()
                    retrieval_chain = create_retrieval_chain(retriever, document_chain)
                
                    with st.spinner("Checking with Dr. Google... just kidding, I'm smarter than that!"):
                        response = retrieval_chain.invoke({'input': prompt1})
                                    
                    # Extract the answer and citations from the response
                    answer = response['answer']
                    citations = extract_citations(answer)
                    
                    # Debugging statements
                    print("Answer:", answer)
                    print("Citations:", citations)
                    
                    # Translate the chatbot's response to the selected language
                    response_translated = translator.translate(answer, dest=selected_language.lower()).text
                    
                    # Handle citations translation
                    if citations:
                        citations_translated = translator.translate(citations, dest=selected_language.lower()).text
                    else:
                        citations_translated = "No citations available."
                    
                    # Add the answer and citations to the chat history
                    st.session_state["chat_history"].append((
    "bot", 
    f"{response_translated}\n\nCitations: {citations_translated}\n\nPlease consult the required doctor before implementing any guidance provided."
))

                    # Generate follow-up questions
                    follow_up_prompt = ChatPromptTemplate.from_template("""
                        Based on the following conversation and answer, generate two relevant follow-up questions:
                        User question: {user_question}
                        Bot answer: {bot_answer}
                        
                        Follow-up questions:
                        1.
                        2.
                
                        {context}
                    """)
                    
                    follow_up_response = llm.invoke(follow_up_prompt.format(
                        user_question=prompt1,
                        bot_answer=response['answer'],
                        context=""
                    ))
                    
                    follow_up_questions = follow_up_response.content.strip().split('\n')
                    
                    translated_follow_up = translator.translate("Here are some follow-up questions you might find helpful:", dest=selected_language.lower()).text
                    st.session_state["chat_history"].append(("bot", translated_follow_up))
                    for question in follow_up_questions:
                        if question.startswith(('1.', '2.')):
                            translated_question = translator.translate(question, dest=selected_language.lower()).text
                            st.session_state["chat_history"].append(("bot", translated_question))
                else:
                    response = "Vector store not initialized. Please check your data directory and try again."
                    response_translated = translator.translate(response, dest=selected_language.lower()).text
                    st.session_state["chat_history"].append(("bot", response_translated))
    
            #Add a button to read the response
            if st.button("Read Answer"):
                threading.Thread(target=speak_text, args=(response,)).start()
    
            # Clear the input after submission
            st.session_state.prompt1 = ""
            st.rerun()

        # Display updated chat history
        for message in st.session_state["chat_history"]:
            st.write(message)

    if st.button("Download Chat "):
        pdf = generate_chat_history_pdf()
        st.download_button(
            label="Download PDF",
            data=pdf,
            file_name="chat_history.pdf",
            mime="application/pdf"
        )

# Modify the main function to display the "Health Tips" section when the user clicks on the link
def main():
    # Check the current page and display the corresponding interface
    if st.session_state.get("page") == "medication_reminder":
        setup_medication_reminder()
    elif st.session_state.get("page") == "consult_experts":
        consult_experts_section()
    elif st.session_state.get("page") == "emergency_assist":
        emergency_assist_section()
    elif st.session_state.get("page") == "medical_records":
        medical_records_section()
    elif st.session_state.page == "wellness_hunt":
        display_wellness_hunt()
    elif st.session_state.get("page") == "discussion_forum":
        discussion_forum()
    else:
        main_chatbot_interface()

if __name__ == "__main__":
    # Initialize the page state
    if "page" not in st.session_state:
        st.session_state.page = "main_chatbot"

    main()





