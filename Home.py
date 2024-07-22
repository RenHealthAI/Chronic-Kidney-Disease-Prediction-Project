import streamlit as st
from dateutil.relativedelta import relativedelta
import datetime as dt
import pyodbc
import os
from PIL import Image
import pandas as pd
from azure.storage.blob import BlobServiceClient
from datetime import datetime


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

image = Image.open('RenHealth_Logo.jpg')
image1 = Image.open('RenHealth_Portal.png')

def login_user(username,password):
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tbl_users WHERE UserName = ?", username)
    user = cursor.fetchone()
    if user:
        if password:
            return user[1], user[2], user[3], user[4]
        else:
            return None, None, None, None
    else:
        return None, None, None, None

#define the connection for the DBs when working on the local environment
conn = pyodbc.connect(
        'DRIVER={ODBC Driver 17 for SQL Server};SERVER='
        +st.secrets['server']
        +';DATABASE='
        +st.secrets['database']
        +';UID='
        +st.secrets['username']
        +';PWD='
        +st.secrets['password']
        ) 

# # define the connections for the DBs when deployed to cloud
# # assign credentials for the avondw DB credentials
# server = os.environ.get('server_name')
# database = os.environ.get('db_name')
# username = os.environ.get('db_username')
# password = os.environ.get('password')
# conn = pyodbc.connect(
#         'DRIVER={ODBC Driver 17 for SQL Server};SERVER='
#         + server
#         +';DATABASE='
#         + database
#         +';UID='
#         + username
#         +';PWD='
#         + password
#         )

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
if 'password' not in st.session_state:
    st.session_state['password'] = None
if 'role' not in st.session_state:
    st.session_state['role'] = None
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

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

if not st.session_state.logged_in:
    st.sidebar.subheader('Kindly Log in to Access the Portal')
    st.sidebar.title('Login Page')
    st.image(image, use_column_width=True)
    username = st.sidebar.text_input('UserName')
    password = st.sidebar.text_input('Password', type='password')

if st.sidebar.button('LOGIN'):
    user_name, enumerator, login_password, role = login_user(username, password)
    if user_name == username and login_password == password:
        st.session_state['authentication_status'] = True
        st.session_state['username'] = username
        st.session_state['name'] = enumerator
        st.session_state['role'] = role
        st.session_state['password'] = password
        st.session_state['logged_in'] = True
        st.experimental_rerun()
    else:
        st.error('Username/Password is Incorrect')

else:
    if st.sidebar.button('LOGOUT', help='Click to Logout'):
        st.session_state.logged_in = False
        st.experimental_rerun()


if st.session_state['logged_in']:
    st.image(image1, use_column_width=True)
    st.title("Welcome to the RenHealth CKD Data Collection Portal'")
    st.write(f"You are currently logged in as {st.session_state['name']} ({st.session_state['username']})")
    # st.write(get_next_participant_id(conn))

    if st.session_state['role'] == 'Enumerator':
        st.write("The data required has been categorised into different categories. Please fill in the form below to log in each participant's data accordingly")
        query = 'select * from Participant_Data_Batch_live1'
        participant = get_data_from_sql()

        st.subheader('Participant Information')
        participant_id = get_next_participant_id(conn)
        with st.form(key='my_form', clear_on_submit=True):
            case_id = st.text_input('Enter Case Number', value=None)
            dob = st.empty().date_input('Date of Birth', value=None, min_value=dt.datetime.now().date()-relativedelta(years=100), max_value=dt.datetime.now().date())
            gender = st.selectbox(label='Gender', placeholder='Select an Option', index=None, options=['Male', 'Female', 'Other'])
            ethnicity = st.selectbox(label='Select Ethnic Category', placeholder='Select an Option', index=None, options=['Yoruba', 'Hausa', 'Igbo', 'Others', 'Unknown'])
            nationality = st.selectbox(label='Select Nationality', placeholder='Select an Option', index=None, options=['Nigerian', 'Other Africans', 'Non-African', 'Unknown'])

            st.subheader('Clinical History')
            ckd_diagnosis = st.selectbox(label='Diagnosis of Chronic Kidney Disease', placeholder='Select Option', index=None if st.session_state.get('ckd_diagnosis', '') == '' else st.session_state['ckd_diagnosis'], options=['Yes', 'No'])
            primary_cause = st.text_input('If Yes, Enter Primary Cause of CKD', value=None, help='Enter if CKD Diagnosis is Yes')
            ckd_stage = st.selectbox(label='If Yes, Select Stage of CKD', placeholder='Select Option', index=None, options=['Stage 1', 'Stage 2', 'Stage 3', 'Stage 4', 'Stage 5', 'Unknown'], help='Enter if CKD Diagnosis is Yes')

            st.subheader('Comorbidities')
            hypertension = st.radio(label='Hypertension', options=['Yes', 'No'], index=0)
            diabetes = st.radio(label='Diabetes', options=['Yes', 'No'], index=0)
            cardiovascular_disease = st.radio(label='Cardiovascular Disease', options=['Yes', 'No'], index=0)
            other_comorbidities = st.text_input('Others, Please Specify', value=None, key='other_comorbidities')

            st.subheader('Medication History')
            ace_inhibitors = st.radio(label='ACE Inhibitors/ARBs', options=['Yes', 'No'], index=0)
            diuretics = st.radio(label='Diuretics', options=['Yes', 'No'], index=0)
            family_history = st.radio(label='Family History of CKD', options=['Yes', 'No'], index=0)
            other_medications = st.text_input('Others, Please Specify', value=st.session_state.get('other_medications', ''), key='other_medications')

            st.subheader('Socioeconomic Factors')
            marital_status = st.selectbox(label='Marital Status', placeholder='Select Option', index=None, options=['Single', 'Married', 'Widowed', 'Divorced', 'Others', 'Not Specified'])
            education = st.selectbox(label='Highest Level of Education', placeholder='Select Option', index=None, options=['No Formal Education', 'Primary', 'Secondary', 'Tertiary', 'Not Specified'])
            occupation = st.selectbox(label='Occupation', placeholder='Select Option', index=None, options=['Unemployed', 'Student', 'Employed', 'Retired','Artisan/Informal', 'Others', 'Not Specified'])
            monthly_income = st.number_input(label='Monthly Income (in Naira)', value=None)

            st.subheader('Laboratory Findings')
            bmi = st.number_input('Body Mass Index (BMI)', value=None)
            waist_circum = st.number_input('Waist Circumference (cm)', value=None)
            urine_protein = st.number_input('Urine Protein to Creatinine Ratio', value=None)
            tot_cholesterol = st.number_input('Total Cholesterol (mg/dL)', value=None)
            ldl_cholesterol = st.number_input('LDL Cholesterol (mg/dL)', value=None)
            hdl_cholesterol = st.number_input('HDL Cholesterol (mg/dL)', value=None)
            triglycerides = st.number_input('Triglycerides (mg/dL)', value=None)

            num_eucr_tests = st.sidebar.number_input('Number of E/U/Cr Tests to Add', value=0)
            eucr_tests = []
            for i in range(num_eucr_tests):
                st.subheader(f'E/U/Cr Test {i + 1}')
                test_date = st.date_input(f'Date of Test {i + 1}', value=None, min_value=dt.datetime.now().date()-relativedelta(years=30), max_value=dt.datetime.now().date(), key=f'eucr_test_date_{i}')
                systolic_bp = st.number_input(f'Systolic Blood Pressure {i + 1} (mmHg)', value=None, key=f'eucr_systolic_bp_{i}')
                diastolic_bp = st.number_input(f'Diastolic Blood Pressure {i + 1} (mmHg)', value=None, key=f'eucr_diastolic_bp_{i}')
                potassium = st.number_input(f'Potassium {i + 1} (mg/dL)', value=None, key=f'eucr_potassium_{i}')
                sodium = st.number_input(f'Sodium {i + 1} (mg/dL)', value=None, key=f'eucr_sodium_{i}')
                chloride = st.number_input(f'Chloride {i + 1} (mg/dL)', value=None, key=f'eucr_chloride_{i}')
                bicarbonate = st.number_input(f'Bicarbonate {i + 1} (mg/dL)', value=None, key=f'eucr_bicarbonate_{i}')
                urea = st.number_input(f'Urea {i + 1} (mg/dL)', value=None, key=f'eucr_urea_{i}')
                creatinine = st.number_input(f'Creatinine {i + 1} (mg/dL)', value=None, key=f'eucr_creatinine_{i}')
                egfr = st.number_input(f'eGFR {i + 1} (mL/min/1.73m²)', value=None, key=f'eucr_egfr_{i}')
                eucr_tests.append({
                    'DateOfTest': test_date,
                    'SystolicBloodPressure': systolic_bp,
                    'DiastolicBloodPressure': diastolic_bp,
                    'Potassium': potassium,
                    'Sodium': sodium,
                    'Chloride': chloride,
                    'Bicarbonate': bicarbonate,
                    'Urea': urea,
                    'Creatinine': creatinine,
                    'eGFR': egfr
                })

            num_fbc_tests = st.sidebar.number_input('Number of FBC Tests to Add', value=0)
            fbc_tests = []
            for i in range(num_fbc_tests):
                st.subheader(f'FBC Test {i + 1}')
                test_date = st.date_input(f'Date of Test {i + 1}', value=None, min_value=dt.datetime.now().date()-relativedelta(years=30), max_value=dt.datetime.now().date(), key=f'fbc_test_date_{i}')
                hemoglobin = st.number_input(f'Hemoglobin {i + 1} (g/dL)', value=None, key=f'fbc_hemoglobin_{i}')
                rbc = st.number_input(f'Red Blood Cell Count {i + 1} (million cells/µL)', value=None, key=f'fbc_rbc_{i}')
                hematocrit = st.number_input(f'Hematocrit {i + 1} (%)', value=None, key=f'fbc_hematocrit_{i}')
                mcv = st.number_input(f'Mean Corpuscular Volume {i + 1} (fL)', value=None, key=f'fbc_mcv_{i}')
                mch = st.number_input(f'Mean Corpuscular Hemoglobin {i + 1} (pg)', value=None, key=f'fbc_mch_{i}')
                mchc = st.number_input(f'Mean Corpuscular Hemoglobin Concentration {i + 1} (g/dL)', value=None, key=f'fbc_mchc_{i}')
                rdw = st.number_input(f'Red Cell Distribution Width {i + 1} (%)', value=None, key=f'fbc_rdw_{i}')
                fbc_tests.append({
                    'testdate': test_date,
                    'fbc_hemoglobin': hemoglobin,
                    'rbc': rbc,
                    'haematocrit': hematocrit,
                    'mcv': mcv,
                    'mch': mch,
                    'mchc': mchc,
                    'rdw': rdw
                })

            st.subheader('Genetic Testing')
            rsid = st.text_input('Enter RSID', value=None)
            allele_1 = st.text_input('Enter Allele 1', value=None)
            allele_2 = st.text_input('Enter Allele 2', value=None)

            st.subheader('Family History of Genetic Disorders')
            fam_hist_genetic = st.radio(label='Is there a Family History of Genetic Disorders?', options=['Yes', 'No'], index=0)
            fam_hist_genetic_details = st.text_input('If Yes, Please Specify', value=None)

            st.subheader('Imaging')
            imaging_type = st.text_input('Enter Type of Imaging', value=None,help='e.g. MRI, CT Scan, X-ray, etc.')
            imaging_scan = st.file_uploader('Upload Imaging Scan', type=['jpg', 'jpeg', 'png', 'pdf'],accept_multiple_files=True)
            imaging_results = st.text_area('Enter Imaging Result', value=None)
            submit = st.form_submit_button('Submit Record')

        # Initialize the BlobServiceClient
        blob_service_client = BlobServiceClient.from_connection_string(st.secrets['conn_str'])
        # blob_service_client = BlobServiceClient.from_connection_string(os.environ.get('conn_str'))
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
        if submit:
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
                'NumFBCTests': num_fbc_tests or None,
                'NumEUCRTests': num_eucr_tests or None,
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
            
            submitted = submit_data(participant_data, eucr_tests, fbc_tests)  
            
    else:
        query = 'select * from vw_combined_patient_record'
        patient_df = pd.read_sql(query, conn)

        enumerator_counts = patient_df.groupby('Enumerator')['ParticipantID'].nunique().reset_index()
        enumerator_counts.columns = ['Enumerator', 'Number of Cases Recorded']
        enumerator_counts = enumerator_counts.sort_values('Number of Cases Recorded', ascending=False).reset_index(drop=True)

        st.subheader('Summary Table')
        st.dataframe(enumerator_counts)
        #display a selectbox on the sidebar to display individual records by each enumerator
        enumerator_list = patient_df['Enumerator'].unique().tolist()
        selected_enumerator = st.sidebar.selectbox('Select Enumerator', enumerator_list)
        filtered_df = patient_df[patient_df['Enumerator'] == selected_enumerator].reset_index(drop=True)
        st.title(f"Records for Enumerator: {selected_enumerator}")
        st.dataframe(filtered_df)
        st.markdown(
                """
                <style>
                [data-testid="stElementToolbar"] {
                    display: none;
                }
                </style>
                """,
                unsafe_allow_html=True
            )

       
