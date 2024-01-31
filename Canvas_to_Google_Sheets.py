import requests
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from datetime import datetime
import pytz
from pytz import timezone

# Canvas API setup
canvas_domain = 'canvas.school.edu' # replace with your actual Canvas domain
access_token = 'YOUR_ACCESS_TOKEN'  # replace with your actual access token
course_ids = ['COURSE_ID_1', 'COURSE_ID_2', 'COURSE_ID_3']  # Add your course IDs here
headers = {'Authorization': f'Bearer {access_token}'}

# Define the MST timezone
mst = pytz.timezone('America/Denver')

def convert_utc_to_mt(utc_dt_str):
    if utc_dt_str is None or utc_dt_str == 'No due date':
        return 'No due date'
    # Parse the UTC date string to a datetime object
    utc_dt = datetime.strptime(utc_dt_str, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=pytz.utc)
    # Define the Mountain Time zone with daylight saving consideration
    mt_tz = timezone('America/Denver')
    # Convert the UTC datetime to Mountain Time
    mt_dt = utc_dt.astimezone(mt_tz)
    # Format the datetime in a more reader-friendly format
    return mt_dt.strftime('%b %d, %Y, %I:%M %p')

# Function to handle pagination
def fetch_all_pages(endpoint):
    all_data = []
    while endpoint:
        response = requests.get(endpoint, headers=headers, params={'per_page': 100})
        data = response.json()
        all_data.extend(data)
        # Canvas uses the 'Link' header for pagination
        links = requests.utils.parse_header_links(response.headers['Link'])
        endpoint = next((link['url'] for link in links if link['rel'] == 'next'), None)
    return all_data

def process_course(course_id):
    assignments_endpoint = f'https://{canvas_domain}/api/v1/courses/{course_id}/assignments'
    print(f"Headers before request: {headers}")
    assignments_response = requests.get(assignments_endpoint, headers=headers)
    assignments = {assignment['id']: assignment for assignment in assignments_response.json()}

    submissions_endpoint = f'https://{canvas_domain}/api/v1/courses/{course_id}/students/submissions?include[]=assignment'
    submissions = fetch_all_pages(submissions_endpoint)

    flat_data = []
    for submission in submissions:
        # Get the corresponding assignment object
        assignment = assignments.get(submission['assignment_id'], {'name': 'Unknown Assignment', 'points_possible': 0})
        
        # If the assignment name is 'Unknown Assignment', it means we did not fetch this assignment earlier
        if assignment['name'] == 'Unknown Assignment':
            # Fetch the individual assignment data
            individual_assignment_endpoint = f'https://{canvas_domain}/api/v1/courses/{course_id}/assignments/{submission["assignment_id"]}'
            individual_assignment_response = requests.get(individual_assignment_endpoint, headers=headers)
            if individual_assignment_response.status_code == 200:
                assignment = individual_assignment_response.json()
                assignments[submission['assignment_id']] = assignment  # Cache it for future reference
            else:
                print(f"Error fetching assignment {submission['assignment_id']}: {individual_assignment_response.status_code}")

        # Determine the status for the 'Workflow State' column
        if submission.get('graded_at') is not None:
            workflow_state = 'Graded'
        elif submission.get('submitted_at') is not None:
            workflow_state = 'Submitted'
        else:
            workflow_state = 'Unsubmitted'

        due_date = convert_utc_to_mt(assignment.get('due_at'))

        # Get the score and points possible
        score = submission.get('score')
        points_possible = assignment.get('points_possible', 0)

        # Decide what to display for the grade
        if score is not None:
            grade_fraction = f"{score}/{points_possible}"
        elif points_possible == 0:
            grade_fraction = 'Not graded'
        else:
            grade_fraction = f"0/{points_possible}"

        # Calculate the grade as a fraction
        score = submission.get('score')
        points_possible = assignment.get('points_possible', 0)
        grade_fraction = f"{score}/{points_possible}" if score is not None else 'No grade'

        # Calculate the percentage if score is not None and points_possible is not 0 to avoid division by zero
        points_possible = assignment.get('points_possible', 0)
        score = submission.get('score')
        if score is not None and points_possible != 0:
            percentage = (score / points_possible) * 100
        else:
            percentage = 'No score'
        
        flat_data.append({
            'Assignment Name': assignment['name'],
            'Assignment ID': submission['assignment_id'],
            'Due Date': due_date,
            'Grade': grade_fraction,
            'Percentage': percentage,
            'Score': submission.get('score', 'No score'),
            'Workflow State': workflow_state,
        })

    df = pd.DataFrame(flat_data)
    df['Due Date'] = pd.to_datetime(df['Due Date'], format='%b %d, %Y, %I:%M %p', errors='coerce')
    df = df.sort_values(by='Due Date')
   
    return df

# Function to get or create a sheet for a course
def get_or_create_sheet(client, course_id):
    try:
        return client.open('YOUR_SPREADSHEET_NAME').worksheet(course_id) # replace with your actual spreadsheet name
    except gspread.exceptions.WorksheetNotFound:
        return client.open('YOUR_SPREADSHEET_NAME').add_worksheet(title=course_id, rows="100", cols="20")  # replace with your actual spreadsheet name

# Google Sheets API setup
scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('PATH_TO_YOUR_SERVICE_ACCOUNT_FILE', scope) # replace with your actual service account file path
client = gspread.authorize(creds)
sheet = client.open('YOUR_SPREADSHEET_NAME').sheet1 # replace with your actual spreadsheet name

# Loop through each course and process it
for course_id in course_ids:
    df = process_course(course_id)
    course_sheet = get_or_create_sheet(client, course_id)

    # Clear existing content
    course_sheet.clear()

    sheet_headers = ['Assignment Name', 'Assignment ID', 'Due Date', 'Grade', 'Score', 'Workflow State']
    course_sheet.append_row(sheet_headers)

    # Write the sorted rows to the Google Sheet
    for index, row in df.iterrows():
        row_list = [
            row['Assignment Name'],
            row['Assignment ID'],
            row['Due Date'].strftime('%Y-%m-%d %H:%M:%S') if pd.notnull(row['Due Date']) else 'No due date',
            row['Grade'],
            f"{row['Percentage']:.2f}%" if isinstance(row['Percentage'], float) else row['Percentage'],
            row['Workflow State'],
        ]
        try:
            course_sheet.append_row(row_list)
        except Exception as e: 
            print(f"An error occurred: {e}")


