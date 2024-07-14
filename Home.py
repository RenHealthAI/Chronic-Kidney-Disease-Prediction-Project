import streamlit as st
from dateutil.relativedelta import relativedelta
import datetime as dt
import pyodbc
import os
import pandas as pd
from azure.storage.blob import BlobServiceClient
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
import bcrypt
from datetime import datetime


# def sanitize_input(input_text):
#     """Sanitize input to ensure it's a single line of text."""
#     return input_text.replace('\n', ' ').replace('\r', ' ') if input_text else None

# # Function to upload image to Azure Blob Storage
# def upload_image_to_blob(file, participant_id):
#     # Azure Storage account connection string
#     connect_str = os.environ.get('conn_str')
#     # connect_str = st.secrets['conn_str']
    
#     # Create the BlobServiceClient object
#     blob_service_client = BlobServiceClient.from_connection_string(connect_str)
    
#     # Create a unique name for the blob
#     blob_name = f"participant_images/{participant_id}/{file.name}"
    
#     # Create a blob client
#     blob_client = blob_service_client.get_blob_client(container="scanimages", blob=blob_name)
    
#     # Upload the image
#     blob_client.upload_blob(file)
    
#     # Return the URL of the uploaded image
#     return blob_client.url

# def save_image(image_file, participant_id):
#     """Save uploaded image to a directory and return the file path."""
#     if image_file:
#         img_directory = 'uploaded_images'
#         if not os.path.exists(img_directory):
#             os.makedirs(img_directory)
#         # Use participant ID and timestamp to create a unique filename
#         timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
#         img_filename = f"{participant_id}_{timestamp}_{image_file.name}"
#         img_path = os.path.join(img_directory, img_filename)
#         with open(img_path, "wb") as f:
#             f.write(image_file.getbuffer())
#         return img_path
#     return None

# Function to get the next Participant ID
def get_next_participant_id(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT MAX(ParticipantID) FROM Participant_Data_Batch_live1")
    max_id = cursor.fetchone()[0]
    if max_id is None:
        next_id = 1
    else:
        num_id = int(max_id.split('REN')[1])
        next_id = num_id + 1

    participant_id = f"REN{next_id:05}"
    return participant_id
    
#set the page configuration
st.set_page_config(page_title= 'CKD Data Collection Portal',layout='wide', initial_sidebar_state='expanded')

# Load configuration from YAML file
with open('config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

# Hash passwords if not already hashed
for user in config['credentials']['usernames']:
    plain_password = config['credentials']['usernames'][user]['password']
    if not plain_password.startswith('$2b$'):
        hashed_password = bcrypt.hashpw(plain_password.encode('utf-8'), bcrypt.gensalt())
        config['credentials']['usernames'][user]['password'] = hashed_password.decode('utf-8')
 
# Instantiate the authenticator
authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days'],
    config.get('preauthorized', [])
)

# #define the connection for the DBs when working on the local environment
# conn = pyodbc.connect(
#         'DRIVER={ODBC Driver 17 for SQL Server};SERVER='
#         +st.secrets['server']
#         +';DATABASE='
#         +st.secrets['database']
#         +';UID='
#         +st.secrets['username']
#         +';PWD='
#         +st.secrets['password']
#         ) 

# define the connections for the DBs when deployed to cloud
# assign credentials for the avondw DB credentials
server = os.environ.get('server_name')
database = os.environ.get('db_name')
username = os.environ.get('db_username')
password = os.environ.get('password')
conn = pyodbc.connect(
        'DRIVER={ODBC Driver 17 for SQL Server};SERVER='
        + server
        +';DATABASE='
        + database
        +';UID='
        + username
        +';PWD='
        + password
        )

def get_data_from_sql():
    participant = pd.read_sql(query, conn)
    return participant


# Initialize session state variables if they don't exist
if 'authentication_status' not in st.session_state:
    st.session_state['authentication_status'] = None
if 'name' not in st.session_state:
    st.session_state['name'] = None
if 'username' not in st.session_state:
    st.session_state['username'] = None

if st.session_state['authentication_status']:
    st.title("Welcome to the RenHealth CKD Data Collection Portal'")
    st.write(f"You are currently logged in as {st.session_state['name']} ({st.session_state['username']})")

# st.header('Welcome to the CKD Data Collection Portal')
# st.sidebar.header('RenHealth CKD Data Collection')
# st.sidebar.subheader('This portal is designed to collect data from patients with Chronic Kidney Disease (CKD)')

    st.write("The data required has been categorised into different categories. Please fill in the form below to log in each participant's data accordingly")

    st.write("Please note that all fields are required")
    query = 'select * from Participant_Data_Batch_live1'


    participant = get_data_from_sql()
    # st.write(get_next_participant_id(conn))

    st.subheader('Participant Information')

    participant_id = get_next_participant_id(conn)
    case_id = st.text_input('Enter Case Number')
    dob = st.date_input('Date of Birth',min_value=dt.datetime.now().date()-relativedelta(years=100),max_value=dt.datetime.now().date())
    gender = st.selectbox(label='Gender', placeholder='Select an Option', index=None, options=['Male', 'Female', 'Other'],)
    ethnicity = st.selectbox(label = 'Select Ethnic Category',placeholder='Select an Option', index=None, options=['Yoruba', 'Hausa', 'Igbo', 'Others', 'Unknown'])
    nationality = st.selectbox(label = 'Select Nationality', placeholder='Select an Option', index=None, options = ['Nigerian', 'Other Africans', 'Non-African'])
    # contact_info = sanitize_input(st.text_input('Contact Information'))

    st.subheader('Clinical History')

    ckd_diagnosis = st.selectbox(label='Diagnosis of Chronic Kidney Disease',placeholder='Select Option', index=None, options=['Yes', 'No'])
    if ckd_diagnosis == 'Yes':
        primary_cause = st.text_input('Enter Primary Cause of CKD')
        ckd_stage =  st.selectbox(label='Stage of CKD', placeholder='Select Option', index=None, options=['Stage 1', 'Stage 2', 'Stage 3', 'Stage 4', 'Stage 5'])
    else:
        ckd_stage = None
    st.subheader('Comorbidities')

    hypertension = st.radio(label='Hypertension', options=['Yes', 'No'])
    diabetes = st.radio(label='Diabetes', options=['Yes', 'No'])
    cardiovascular_disease = st.radio(label='Cardiovascular Disease', options=['Yes', 'No'])
    other_comorbidities = st.text_input('Others, Please Specify', key='other_comorbidities')

    st.subheader('Medication History')

    ace_inhibitors = st.radio(label='ACE Inhibitors/ARBs', options=['Yes', 'No'])
    diuretics = st.radio(label='Diuretics', options=['Yes', 'No'])
    family_history = st.radio(label='Family History of CKD', options=['Yes', 'No'])
    other_medications = st.text_input('Others, Please Specify',key='other_medications')

    st.subheader('Demographic Information')
    # age = st.number_input('Age')
    marital_status = st.radio(label='Marital Status', options=['Single', 'Married', 'Divorced', 'Widowed'])
    education = st.radio(label='Education Level', options=['Primary', 'Secondary', 'Tertiary', 'None'])
    occupation = st.text_input('Occupation')
    monthly_income = st.number_input('Monthly Income')

    st.subheader('Clinical Measurements')
    bmi = st.number_input('Body Mass Index (kg/m2)')
    waist_circum = st.number_input('Waist Circumference (cm)')
    urine_protein = st.number_input('Urine Protein-to-Creatinine Ratio (mg/g)')
    tot_cholesterol = st.number_input('Lipid Profile - Total Cholesterol (mg/dL)')
    ldl_cholesterol = st.number_input('Lipid Profile - LDL Cholesterol (mg/dL)')
    hdl_cholesterol = st.number_input('Lipid Profile - HDL Cholesterol (mg/dL)')
    triglycerides = st.number_input('Lipid Profile - Triglycerides (mg/dL)')

    num_eucr_test = st.sidebar.number_input('Input the Number of E/U/Cr Tests Done',min_value=1, max_value=10, value=1, step=1, key='num_eucr_tests')
    num_fbc_test = st.sidebar.number_input('Input the Number of Full Blood Count Tests Done',min_value=1, max_value=10, value=1, key='num_fbc_tests')
    #based on the number of tests done, the user can input the data for each test

    eucr_tests = []
    for i in range(num_eucr_test):
        st.subheader('E/U/Cr Test {}'.format(i+1))
        test_data = {
            'DateOfTest': st.date_input('Date of Test', min_value=dt.datetime.now().date()-relativedelta(years=10), max_value=dt.datetime.now().date(), key='date_of_test{}'.format(i+1)),
            'sys_blood_press': st.number_input('Systolic Blood Pressure (mmHg)', key='sys{}'.format(i+1)),
            'diast_blood_press': st.number_input('Diastolic Blood Pressure (mmHg)', key='diast{}'.format(i+1)),
            'Potassium': st.number_input('Potassium (mmol/L)', key='potassium{}'.format(i+1)),
            'Sodium': st.number_input('Sodium (mmol/L)', key='sodium{}'.format(i+1)),
            'Chloride': st.number_input('Chloride (mmol/L)', key='chloride{}'.format(i+1)),
            'Bicarbonate': st.number_input('Bicarbonate (mmol/L)', key='bicarbonate{}'.format(i+1)),
            'Urea': st.number_input('Urea (mg/dL)', key='urea{}'.format(i+1)),
            'Creatinine': st.number_input('Creatinine (mg/dL)', key='creatinine{}'.format(i+1)),
            'eGFR': st.number_input('eGFR (mL/min/1.73m^2)', key='egfr{}'.format(i+1))
        }
        eucr_tests.append(test_data)

    fbc_tests = []
    for i in range(num_fbc_test):
        st.subheader('Full Blood Count Test {}'.format(i+1))
        fbc_data = {
            'DateOfTest': st.date_input('Date of Test', min_value=dt.datetime.now().date()-relativedelta(years=10), max_value=dt.datetime.now().date(), key='date_of_fbctest{}'.format(i+1)),
            'Hemoglobin': st.number_input('Hemoglobin (g/dL)',key='hemo{}'.format(i+1)),
            'RBC': st.number_input('Red Blood Cells (10^6/uL)',key='rbc{}'.format(i+1)),
            'Haematocrit': st.number_input('Haematocrit (%)',key='crit{}'.format(i+1)),
            'MCV': st.number_input('Mean Corpuscular Volume (fL)',key='mcv{}'.format(i+1)),
            'MCH': st.number_input('Mean Corpuscular Hemoglobin (pg)', key='mch{}'.format(i+1)),   
            'MCHC': st.number_input('Mean Corpuscular Hemoglobin Concentration (g/dL)', key='mchc{}'.format(i+1)),
            'RDW': st.number_input('Red Cell Distribution Width (%)', key='rdw{}'.format(i+1))
        }
        fbc_tests.append(fbc_data)
        
    st.subheader('Genetic Markers')
    rsid = st.text_input('Genetic Testing - rsID or Gene Name', key='rsid')
    allele_1 = st.text_input('Genetic Testing - Allele 1', key='allele_1')
    allele_2 = st.text_input('Genetic Testing - Allele 2', key='allele_2')
    fam_hist_genetic = st.radio(label='Family History of Genetic Disorders', options=['Yes', 'No'], key='fam_hist_genet')
    if fam_hist_genetic == 'Yes':
        fam_hist_genetic_details = st.text_input('If Yes, Please Specify', key='fam_hist_genetic_details')
    else:
        fam_hist_genetic_details = None

    st.subheader('Radiological or Imaging Data')
    imaging_type = st.selectbox(label='Type of Imaging', placeholder='Select Option', index=None, options=['Ultrasound', 'CT Scan', 'MRI', 'X-ray', 'Other'])
    imaging_scan = st.file_uploader('Upload Radiological or Imaging Scan',accept_multiple_files=True, type=['jpg', 'jpeg', 'png', 'pdf'])
    imaging_results = st.text_area('Findings of Imaging')

    # Initialize the BlobServiceClient
    # blob_service_client = BlobServiceClient.from_connection_string(st.secrets['conn_str'])
    blob_service_client = BlobServiceClient.from_connection_string(os.environ.get('conn_str'))
    # Create a single container for all uploaded images
    container_name = 'scanimages'
    container_client = blob_service_client.get_container_client(container_name)
    if imaging_scan is not None:
        # Get the provider name and create a folder for each provider
        enumerator = st.session_state['name'].replace(" ", "").lower()

        # Get the current year and create a subfolder for each year in each provider folder
        current_year = datetime.now().year
        year_folder = f"{enumerator}/{current_year}"

        # Create a unique folder for the member within the year folder
        patient_folder = f"{year_folder}/{case_id}"

        # List to hold the URLs of uploaded files
        uploaded_urls = []

        for file in imaging_scan:
            # Create a unique name for the file using the original file name
            unique_filename = f"{case_id}_{file.name}"

            # Full path to upload the file
            blob_path = os.path.join(patient_folder, unique_filename)

            # Get the blob client using the full path
            blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_path)
            
            # Upload the file
            blob_client.upload_blob(file, overwrite=True)

            # Get the URL of the uploaded file and add it to the list
            uploaded_urls.append(blob_client.url)

        # URL pointing to the member's folder (just for reference, not an actual browseable URL)
        member_folder_url = f"https://{blob_service_client.account_name}.blob.core.windows.net/{enumerator}/{patient_folder}"

    #writing the data to a csv file
    if st.button('Submit Data'):
        image_url = None
        if imaging_scan is not None:
            image_url = member_folder_url
        # Create a dictionary of the data
        participant_data = {
            'ParticipantID': participant_id,
            'CaseID': case_id,
            'DateOfBirth': dob,
            'Gender': gender or None,
            'Ethnicity': ethnicity or None,
            'Nationality': nationality or None,
            'CKDDiagnosis': ckd_diagnosis or None,
            'CKDPrimaryCause': primary_cause or None,
            'CKDStage': ckd_stage or None,
            'Hypertension': hypertension or None,
            'Diabetes': diabetes or None,
            'CardiovascularDisease': cardiovascular_disease or None,
            'OtherComorbidities': other_comorbidities or None,
            'ACEInhibitorsARBs': ace_inhibitors or None,
            'Diuretics': diuretics or None,
            'FamilyHistoryOfCKD': family_history or None,
            'OtherMedications': other_medications or None,
            'MaritalStatus': marital_status or None,
            'EducationLevel': education or None,
            'Occupation': occupation or None,
            'MonthlyIncome': monthly_income or None,
            'BodyMassIndex': bmi or None,
            'WaistCircumference': waist_circum or None,
            'UrineProteinToCreatinineRatio': urine_protein or None,
            'TotalCholesterol': tot_cholesterol or None,
            'LDLCholesterol': ldl_cholesterol or None,
            'HDLCholesterol': hdl_cholesterol or None,
            'Triglycerides': triglycerides or None,
            'NumFBCTests': num_fbc_test or None,
            'NumEUCRTests': num_eucr_test or None,
            'GeneticTestingRSID': rsid or None,
            'GeneticTestingAllele1': allele_1 or None,
            'GeneticTestingAllele2': allele_2 or None,
            'FamilyHistoryOfGeneticDisorders': fam_hist_genetic or None,
            'FamilyHistoryOfGeneticDisordersDetails': fam_hist_genetic_details or None,
            'TypeOfImaging': imaging_type or None,
            'ImagingScan': image_url,  # Placeholder for image path
            'ImagingResult': imaging_results or None,
            'Enumerator': st.session_state['name'] or None
        }

        def submit_data(participant_data, eucr_tests, fbc_tests):
            cursor = conn.cursor()
            
            try:
                # Start a transaction
                conn.autocommit = False

                # Insert participant data into the Participant_Data_Batch_live1 table
                insert_query = """
                INSERT INTO Participant_Data_Batch_live1 (ParticipantID, case_id, DateOfBirth, Gender, Ethnicity, Nationality, CKDDiagnosis, CKDPrimaryCause, CKDStage, 
                Hypertension, Diabetes, CardiovascularDisease, OtherComorbidities, ACEInhibitorsARBs, Diuretics, FamilyHistoryOfCKD, OtherMedications, MaritalStatus,
                EducationLevel, Occupation, MonthlyIncome, BodyMassIndex, WaistCircumference, UrineProteinToCreatinineRatio, TotalCholesterol, LDLCholesterol,
                HDLCholesterol, Triglycerides, NumFBCTest, NumEUCRTest, GeneticTestingRSID, GeneticTestingAllele1, 
                GeneticTestingAllele2, FamilyHistoryOfGeneticDisorders, FamilyHistoryOfGeneticDisordersDetails, TypeOfImaging, 
                ImagingScan, ImagingResult, enumerator)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                cursor.execute(insert_query, tuple(participant_data.values()))

                # Insert E/U/Cr test data into the tbl_EUCRTests table
                for test in eucr_tests:
                    test['ParticipantID'] = participant_data['ParticipantID']
                    insert_test_query = """
                    INSERT INTO tbl_EUCRTests (DateOfTest, SystolicBloodPressure, DiastolicBloodPressure, Potassium, Sodium, Chloride, Bicarbonate, Urea, Creatinine, eGFR, ParticipantID)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """
                    cursor.execute(insert_test_query, tuple(test.values()))

                # Insert fbc test data into the tbl_fbcTests table
                for test in fbc_tests:
                    test['ParticipantID'] = participant_data['ParticipantID']
                    insert_test_query = """
                    INSERT INTO tbl_fbcTests (testdate, fbc_hemoglobin, rbc, haematocrit, mcv, mch, mchc, rdw, ParticipantID)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """
                    cursor.execute(insert_test_query, tuple(test.values()))

                # Commit the transaction
                conn.commit()
                st.success('Data Submitted Successfully!')

            except Exception as e:
                # Rollback the transaction if there is any error
                conn.rollback()
                st.error(f'Error submitting data: {e}')

            finally:
                # Close the connection
                conn.close()
        submit_data(participant_data, eucr_tests, fbc_tests)

        #once the data has been successfully written to the database, the form is cleared
        st.experimental_rerun()       


     # Add the logout button in the sidebar
    with st.sidebar:
        if authenticator.logout('Logout', 'main'):
            st.session_state['name'] = None
            st.session_state['authentication_status'] = None
            st.session_state['username'] = None
            st.experimental_rerun()
else:
    # Display the login page
    st.title("Home Page")
    st.write("Login with your username and password to access the portal.")
    name, authentication_status, username = authenticator.login('Login', 'main')

    if authentication_status:
        st.session_state['name'] = name
        st.session_state['authentication_status'] = authentication_status
        st.session_state['username'] = username
        st.experimental_rerun()
    elif authentication_status is False:
        st.error("Username/password is incorrect")
    elif authentication_status is None:
        st.warning("Please enter your username and password")
