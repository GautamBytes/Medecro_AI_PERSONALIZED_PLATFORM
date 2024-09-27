

# Medical Chatbot Project

Welcome to the **Medical Chatbot** project! This chatbot is designed to assist users with medical queries and provide relevant information based on the selected medical specialization. The chatbot is built using **Streamlit** and various Python libraries, with an integrated **Node.js** server for the symptom checker feature.

## Table of Contents

1. [Overview](#overview)
2. [Features](#features)
3. [Prerequisites](#prerequisites)
4. [Installation](#installation)
5. [Running the Application](#running-the-application)
6. [File Structure](#file-structure)
7. [Usage](#usage)
8. [Contributing](#contributing)
9. [License](#license)

---

## Overview

The Medical Chatbot is built to answer medical queries based on a selected medical specialization, assist users with medication reminders, and provide features like symptom checking, expert consultations, emergency assist, and much more.

Key technologies used:
- **Streamlit** for the main interface.
- **Node.js** for symptom checker.
- **Google Translate API** for multilingual support.
- **SQLite** for database integration.
  
## Features

- **Multiple Medical Specializations**: Get tailored responses based on the chosen category (e.g., Cardiologist, Dermatologist, etc.).
- **Multilingual Support**: Supports English, Hindi, Spanish, French, and German.
- **Voice Input & Text-to-Speech**: Interact via speech and hear responses from the chatbot.
- **Symptom Checker**: A separate symptom-checking tool.
- **Medication Reminders**: Set reminders for medications via notification, email, or voice.
- **Consult Experts**: Connect with medical professionals for consultations.
- **Emergency Assist**: Quick access to emergency contacts and ambulance services.
- **Document Uploads**: Upload medical records and related documents.
- **Follow-up Questions**: Dynamically generated questions based on the previous query.
- **Download Chat History**: Save your entire chat as a PDF.

---

## Prerequisites

Before cloning and running this project, ensure you have the following installed:

- **Python 3.6 or higher**: [Download Python](https://www.python.org/downloads/)
- **Node.js (for Symptom Checker)**: [Download Node.js](https://nodejs.org/en/)


Install required Python libraries using the provided `requirements.txt`.

```bash
pip install -r requirements.txt
```

Install Node.js dependencies for the Symptom Checker:

```bash
cd chat
npm install
```

---

## Installation

### Step 1: Clone the Repository

Start by cloning the repository to your local machine using the following command:

```bash
git clone https://github.com/GautamBytes/Medecro_AI_PERSONALIZED_PLATFORM.git
```

Replace `<repository-url>` with the actual GitHub repository URL.

### Step 2: Navigate to the Project Directory

Once the repository is cloned, navigate into the project directory:

```bash
cd med_chatbot
```

### Step 3: Install Python Dependencies

Install all the required Python packages by running:

```bash
pip install -r requirements.txt
```

### Step 4: Install Node.js Dependencies (For Symptom Checker)

Navigate to the `chat` directory and install the required Node.js packages:

```bash
cd chat
npm install
```

This will install all the dependencies listed in the `package.json` file.

---

## Running the Application

The application requires two terminals to run: one for the main chatbot interface and another for the symptom checker feature.

### Step 1: Running the Main Chatbot

In the first terminal, navigate to the project root and run the following command to start the chatbot interface using Streamlit:

```bash
streamlit run model.py
```

This will start the chatbot at `http://localhost:8501`.

### Step 2: Running the Symptom Checker

In a second terminal, navigate to the `chat` directory and start the symptom checker server:

```bash
cd chat
node server.js
```

The symptom checker will be available at `http://localhost:3000`.

---

## File Structure

Below is a detailed explanation of the file structure for better understanding:

```
med_chatbot/
│
├── model.py                 # Main Python file for running the chatbot with Streamlit
├── health_tips/             # Health tips resources and files
├── *.pkl                    # Preprocessed book files for medical knowledge
├── Team_Members/            # Team member images
├── Pre-Uploaded Posts/      # Images for pre-uploaded posts
├── Bot_Avatars/             # Custom avatars for the chatbot based on medical specialization
├── chat/                    # Symptom checker functionality
│   ├── server.js            # Node.js server file
│   ├── package.json         # Node.js dependencies
│   ├── package-lock.json    # Locked versions of Node.js dependencies
│   ├── views/               # EJS files (views) for the symptom checker interface
│   ├── public/              # Static assets like CSS files
│   ├── images/              # Images used for symptom checker UI
│   └── javascripts/         # Symptom checker logic in `symptom2.js`
├── patient_image/           # Patient-related images
├── requirements.txt         # Python dependencies
├── Consult_Experts/         # Files related to the expert consultation feature
├── medicine_images/         # Images related to medicines for medication reminders
├── data/                    # Medical data used by the chatbot
├── Talaash/                 # Project-specific resources
├── app.py                   # Main app logic file
└── llama_2_model/           # Llama 2 model integration (video for reference)
```

---

## Usage

1. **Navigate to the chatbot interface** at `http://localhost:8501` after starting the Streamlit server.
   
2. **Interact with the chatbot** by selecting a medical specialization, asking queries via text or voice input, and exploring follow-up questions.
   
3. **Check symptoms** using the symptom checker, available at `http://localhost:3000` after starting the Node.js server.
   
4. **Set medication reminders**, **consult experts**, **upload medical records**, or use the **emergency assist** feature to assist with medical emergencies.

5. **Download chat history** as a PDF for future reference.





