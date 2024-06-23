import streamlit as st
from dateutil.relativedelta import relativedelta
import datetime as dt
import pyodbc
from PIL import Image
import os
import pandas as pd
from datetime import datetime
from azure.storage.blob import BlobServiceClient


def sanitize_input(input_text):
    """Sanitize input to ensure it's a single line of text."""
    return input_text.replace('\n', ' ').replace('\r', ' ') if input_text else None

# Function to upload image to Azure Blob Storage
def upload_image_to_blob(file, participant_id):
    # Azure Storage account connection string
    connect_str = os.environ.get('conn_str')
    
    # Create the BlobServiceClient object
    blob_service_client = BlobServiceClient.from_connection_string(connect_str)
    
    # Create a unique name for the blob
    blob_name = f"participant_images/{participant_id}/{file.name}"
    
    # Create a blob client
    blob_client = blob_service_client.get_blob_client(container="scanimages", blob=blob_name)
    
    # Upload the image
    blob_client.upload_blob(file)
    
    # Return the URL of the uploaded image
    return blob_client.url

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
    cursor.execute("SELECT MAX(ParticipantID) FROM Participant_Data_Batch1")
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

#define the connection for the DBs when working on the local environment
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

#define the connections for the DBs when deployed to cloud
#assign credentials for the avondw DB credentials
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



st.header('Welcome to the CKD Data Collection Portal')
st.sidebar.header('RenHealth CKD Data Collection')
st.sidebar.subheader('This portal is designed to collect data from patients with Chronic Kidney Disease (CKD)')

st.write("The data required has been categorised into different categories. Please fill in the form below to log in each participant's data accordingly")

st.write("Please note that all fields are required")
query = 'select * from Participant_Data_Batch1'

def get_data_from_sql():
    participant = pd.read_sql(query, conn)
    return participant



participant = get_data_from_sql()
# st.write(get_next_participant_id(conn))

st.subheader('Participant Information')

participant_id = get_next_participant_id(conn)
dob = st.date_input('Date of Birth',min_value=dt.datetime.now().date()-relativedelta(years=100),max_value=dt.datetime.now().date())
gender = st.selectbox(label='Gender', placeholder='Select an Option', index=None, options=['Male', 'Female', 'Other'],)
ethnicity = sanitize_input(st.text_input('Ethnicity'))
nationality = sanitize_input(st.text_input('Nationality'))
# contact_info = sanitize_input(st.text_input('Contact Information'))

st.subheader('Clinical History')

ckd_diagnosis = st.selectbox(label='Diagnosis of Chronic Kidney Disease',placeholder='Select Option', index=None, options=['Yes', 'No'])
if ckd_diagnosis == 'Yes':
    ckd_stage =  st.selectbox(label='Stage of CKD', placeholder='Select Option', index=None, options=['Stage 1', 'Stage 2', 'Stage 3', 'Stage 4', 'Stage 5'])
else:
    ckd_stage = None
st.subheader('Comorbidities')

hypertension = st.radio(label='Hypertension', options=['Yes', 'No'])
diabetes = st.radio(label='Diabetes', options=['Yes', 'No'])
cardiovascular_disease = st.radio(label='Cardiovascular Disease', options=['Yes', 'No'])
other_comorbidities = sanitize_input(st.text_input('Others, Please Specify', key='other_comorbidities'))

st.subheader('Medication History')

ace_inhibitors = st.radio(label='ACE Inhibitors/ARBs', options=['Yes', 'No'])
diuretics = st.radio(label='Diuretics', options=['Yes', 'No'])
family_history = st.radio(label='Family History of CKD', options=['Yes', 'No'])
other_medications = sanitize_input(st.text_input('Others, Please Specify',key='other_medications'))

st.subheader('Demographic Information')
# age = st.number_input('Age')
marital_status = st.radio(label='Marital Status', options=['Single', 'Married', 'Divorced', 'Widowed'])
education = st.radio(label='Education Level', options=['Primary', 'Secondary', 'Tertiary', 'None'])
occupation = sanitize_input(st.text_input('Occupation'))
monthly_income = st.number_input('Monthly Income')

st.subheader('Clinical Measurements')
sys_blood_press = st.number_input('Systolic Blood Pressure (mmHg)')
diast_blood_press = st.number_input('Diastolic Blood Pressure (mmHg)')
bmi = st.number_input('Body Mass Index (kg/m2)')
waist_circum = st.number_input('Waist Circumference (cm)')
urine_protein = st.number_input('Urine Protein-to-Creatinine Ratio (mg/g)')
tot_cholesterol = st.number_input('Lipid Profile - Total Cholesterol (mg/dL)')
ldl_cholesterol = st.number_input('Lipid Profile - LDL Cholesterol (mg/dL)')
hdl_cholesterol = st.number_input('Lipid Profile - HDL Cholesterol (mg/dL)')
triglycerides = st.number_input('Lipid Profile - Triglycerides (mg/dL)')

num_eucr_test = st.sidebar.number_input('Input the Number of E/U/Cr Tests Done',min_value=1, max_value=10, value=1, step=1, key='num_eucr_tests')

#based on the number of tests done, the user can input the data for each test

eucr_tests = []
for i in range(num_eucr_test):
    st.subheader('E/U/Cr Test {}'.format(i+1))
    test_data = {
        'DateOfTest': st.date_input('Date of Test', min_value=dt.datetime.now().date()-relativedelta(years=10), max_value=dt.datetime.now().date(), key='date_of_test{}'.format(i+1)),
        'Potassium': st.number_input('Potassium (mmol/L)', key='potassium{}'.format(i+1)),
        'Sodium': st.number_input('Sodium (mmol/L)', key='sodium{}'.format(i+1)),
        'Chloride': st.number_input('Chloride (mmol/L)', key='chloride{}'.format(i+1)),
        'Bicarbonate': st.number_input('Bicarbonate (mmol/L)', key='bicarbonate{}'.format(i+1)),
        'Urea': st.number_input('Urea (mg/dL)', key='urea{}'.format(i+1)),
        'Creatinine': st.number_input('Creatinine (mg/dL)', key='creatinine{}'.format(i+1)),
        'eGFR': st.number_input('eGFR (mL/min/1.73m^2)', key='egfr{}'.format(i+1))
    }
    eucr_tests.append(test_data)

st.subheader('Full Blood Count')
fbc_data = {
    'Hemoglobin': st.number_input('Hemoglobin (g/dL)'),
    'RBC': st.number_input('Red Blood Cells (10^6/uL)'),
    'Haematocrit': st.number_input('Haematocrit (%)'),
    'MCV': st.number_input('Mean Corpuscular Volume (fL)'),
    'MCH': st.number_input('Mean Corpuscular Hemoglobin (pg)'),   
    'MCHC': st.number_input('Mean Corpuscular Hemoglobin Concentration (g/dL)'),
    'RDW': st.number_input('Red Cell Distribution Width (%)')
}
    
st.subheader('Genetic Markers')
rsid = sanitize_input(st.text_input('Genetic Testing - rsID or Gene Name', key='rsid'))
allele_1 = sanitize_input(st.text_input('Genetic Testing - Allele 1', key='allele_1'))
allele_2 = sanitize_input(st.text_input('Genetic Testing - Allele 2', key='allele_2'))
fam_hist_genetic = st.radio(label='Family History of Genetic Disorders', options=['Yes', 'No'], key='fam_hist_genetic')
if fam_hist_genetic == 'Yes':
    fam_hist_genetic_details = sanitize_input(st.text_input('If Yes, Please Specify', key='fam_hist_genetic_details'))
else:
    fam_hist_genetic_details = None

st.subheader('Radiological or Imaging Data')
imaging_type = st.selectbox(label='Type of Imaging', placeholder='Select Option', index=None, options=['Ultrasound', 'CT Scan', 'MRI', 'X-ray', 'Other'])
imaging_scan = st.file_uploader('Upload Radiological or Imaging Scan', type=['jpg', 'jpeg', 'png', 'pdf'])
imaging_results = sanitize_input(st.text_area('Findings of Imaging'))

#writing the data to a csv file
if st.button('Submit Data'):
    if imaging_scan is not None:
        image_url = upload_image_to_blob(imaging_scan, participant_id)
    # Create a dictionary of the data
    participant_data = {
        'ParticipantID': participant_id,
        'DateOfBirth': dob,
        'Gender': gender or None,
        'Ethnicity': ethnicity or None,
        'Nationality': nationality or None,
        'CKDDiagnosis': ckd_diagnosis or None,
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
        'SystolicBloodPressure': sys_blood_press or None,
        'DiastolicBloodPressure': diast_blood_press or None,
        'BodyMassIndex': bmi or None,
        'WaistCircumference': waist_circum or None,
        'UrineProteinToCreatinineRatio': urine_protein or None,
        'TotalCholesterol': tot_cholesterol or None,
        'LDLCholesterol': ldl_cholesterol or None,
        'HDLCholesterol': hdl_cholesterol or None,
        'Triglycerides': triglycerides or None,
        'fbc_hemoglobin': fbc_data['Hemoglobin'] or None,
        'rbc': fbc_data['RBC'] or None,
        'haematocrit': fbc_data['Haematocrit'] or None,
        'mcv': fbc_data['MCV'] or None,
        'mch': fbc_data['MCH'] or None,
        'mchc': fbc_data['MCHC'] or None,
        'rdw': fbc_data['RDW'] or None,
        'NumEUCRTests': num_eucr_test or None,
        'GeneticTestingRSID': rsid or None,
        'GeneticTestingAllele1': allele_1 or None,
        'GeneticTestingAllele2': allele_2 or None,
        'FamilyHistoryOfGeneticDisorders': fam_hist_genetic or None,
        'FamilyHistoryOfGeneticDisordersDetails': fam_hist_genetic_details or None,
        'TypeOfImaging': imaging_type or None,
        'ImagingScan': image_url or None,  # Placeholder for image path
        'ImagingResult': imaging_results or None
    }

    # Insert participant data into the ParticipantData table
    cursor = conn.cursor()
    insert_query = """
    INSERT INTO Participant_Data_Batch1 (ParticipantID, DateOfBirth, Gender, Ethnicity, Nationality, CKDDiagnosis, CKDStage, 
    Hypertension, Diabetes, CardiovascularDisease, OtherComorbidities, ACEInhibitorsARBs, Diuretics, FamilyHistoryOfCKD, 
    OtherMedications, MaritalStatus, EducationLevel, Occupation, MonthlyIncome, SystolicBloodPressure, 
    DiastolicBloodPressure, BodyMassIndex, WaistCircumference, UrineProteinToCreatinineRatio, TotalCholesterol, 
    LDLCholesterol, HDLCholesterol, Triglycerides, fbc_hemoglobin, rbc, haematocrit, 
    mcv, mch, mchc, rdw, NumEUCRTest, GeneticTestingRSID, GeneticTestingAllele1, 
    GeneticTestingAllele2, FamilyHistoryOfGeneticDisorders, FamilyHistoryOfGeneticDisordersDetails, TypeOfImaging, 
    ImagingScan, ImagingResult)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    cursor.execute(insert_query, tuple(participant_data.values()))
    conn.commit()

    # Insert E/U/Cr test data into the EUCRTests table
    for test in eucr_tests:
        test['ParticipantID'] = participant_id
        insert_test_query = """
        INSERT INTO EUCRTests (DateOfTest, Potassium, Sodium, Chloride, Bicarbonate, Urea, Creatinine, eGFR, ParticipantID)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        cursor.execute(insert_test_query, tuple(test.values()))
        conn.commit()

    st.success('Data Submitted Successfully!')

# Close the connection
conn.close()


