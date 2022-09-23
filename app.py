from flask import Flask, request
from google.cloud import vision
from oauth2client.service_account import ServiceAccountCredentials
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
import gspread
import io
import re
import os
import json
from stdnum import iso6346
from dotenv import load_dotenv

load_dotenv() 

#URL to use the code
#http://127.0.0.1:8000/detect_container?row=260&id=1XTLS4VqXGCQdD4QiI64lPTbb9wr82O4Z
#http://127.0.0.1:8000/detect_vehicle_plate?row=260&id=1ntDSHEisu-tHWW7kOp3FVA3lLNZJcvaF

#______________________________________________________________________________

cs = {
  "web": {
    "client_id": os.environ.get("CS_CLIENT_ID"),
    "project_id": os.environ.get("CS_PROJECT_ID"),
    "auth_uri": os.environ.get("CS_AUTH_URI"),
    "token_uri": os.environ.get("CS_TOKEN_URI"),
    "auth_provider_x509_cert_url": os.environ.get("CS_AUTH_PROVIDER_CERT"),
    "client_secret": os.environ.get("CS_CLIENT_SECRET"),
    "redirect_uris": [os.environ.get("CS_REDIRECT_URIS")],
    "javascript_origins": [os.environ.get("CS_JAVASCRIPT_ORIGINS")]
  }
}
csgs = {
  "type": os.environ.get("CSGS_TYPE"),
  "project_id": os.environ.get("CS_PROJECT_ID"),
  "private_key_id": os.environ.get("CSGS_PRIVATE_KEY_ID"),
  "private_key": os.environ.get("CSGS_PRIVATE_KEY"),
  "client_email": os.environ.get("CSGS_CLIENT_EMAIL"),
  "client_id": os.environ.get("CSGS_CLIENT_ID"),
  "auth_uri": os.environ.get("CSGS_AUTH_URI"),
  "token_uri": os.environ.get("CSGS_TOKEN_URI"),
  "auth_provider_x509_cert_url": os.environ.get("CSGS_AUTH_PROVIDER_CERT"),
  "client_x509_cert_url": os.environ.get("CSGS_CLIENT_CERT")
}
cred = {
  "access_token": os.environ.get("CRED_ACCESS_TOKEN"),
  "client_id": os.environ.get("CRED_CLIENT_ID"),
  "client_secret": os.environ.get("CRED_CLIENT_SECRET"),
  "refresh_token": os.environ.get("CRED_REFRESH_TOKEN"),
  "token_expiry": os.environ.get("CRED_TOKEN_EXPIRY"),
  "token_uri": os.environ.get("CRED_TOKEN_URI"),
  "user_agent": os.environ.get("CRED_USER_AGENT"),
  "revoke_uri": os.environ.get("CRED_REVOKE_URI"),
  "id_token": os.environ.get("CRED_ID_TOKEN"),
  "id_token_jwt": os.environ.get("CRED_ID_TOKEN_JWT"),
  "token_response": {
    "access_token": os.environ.get("CRED_TR_ACCESS_TOKEN"),
    "expires_in": os.environ.get("CRED_TR_EXPIRES_IN"),
    "scope": os.environ.get("CRED_TR_SCOPE"),
    "token_type": os.environ.get("CRED_TR_TOKEN_TYPE")
  },
  "scopes": [
    os.environ.get("CRED_SCOPES1"),
    os.environ.get("CRED_SCOPES2")
  ],
  "token_info_uri": os.environ.get("CRED_TOKEN_INFO_URI"),
  "invalid": os.environ.get("CRED_INVALID"),
  "_class": os.environ.get("CRED_CLASS"),
  "_module": os.environ.get("CRED_MODULE")
}

jsonString1 = json.dumps(cs)
jsonString2 = json.dumps(csgs)
jsonString3 = json.dumps(cred)
jsonString2 = jsonString2.replace('\\\\', '\\')
jsonFile1 = open("client_secrets.json", "w")
jsonFile2 = open("client_secrets_gs.json", "w")
jsonFile3 = open("credentials.json", "w")
jsonFile1.write(jsonString1)
jsonFile2.write(jsonString2)
jsonFile3.write(jsonString3)
jsonFile1.close()
jsonFile2.close()
jsonFile3.close()

#______________________________________________________________________________

# Using client_secrets_gs.json to establish credentials for gspread to work on Sheets
scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('client_secrets_gs.json', scope)
client = gspread.authorize(creds)

# Automating pydrive authentication process to download images from drive
gauth = GoogleAuth()
# Try to load saved client credentials
gauth.LoadCredentialsFile("mycreds.txt")
if gauth.credentials is None:
    # Authenticate if they're not there
    gauth.GetFlow()
    gauth.flow.params.update({'access_type': 'offline'})
    gauth.flow.params.update({'approval_prompt': 'force'})
    gauth.LocalWebserverAuth()
elif gauth.access_token_expired:
    # Refresh them if expired
    gauth.Refresh()
else:
    # Initialize the saved creds
    gauth.Authorize()
# Save the current credentials to a file
gauth.SaveCredentialsFile("mycreds.txt")

# Opening google drive in drive
drive = GoogleDrive(gauth)

#______________________________________________________________________________

def detect_container_vision():

    """
    Creating GOOGLE_APPLICATION_CREDENTIALS enviroment from "client_secrets_gs.json" file.
    These creds are associated with gcp of account 17uec122@lnmiit.ac.in
    """
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"]="client_secrets_gs.json"

    #Downloading the image in cn1.jpeg and running vision api
    client = vision.ImageAnnotatorClient()
    fn=os.path.join(os.path.dirname(__file__),'cn1.jpeg')
    with io.open(fn, 'rb') as image_file:
        content = image_file.read()
    image = vision.Image(content=content)
    response = client.text_detection(image=image)

    # Responses from vision collected in texts list
    texts = response.text_annotations

    # # New alogorithm using RegEx
    # Compiling RegEx patterns for all possibilities
    cnr1 = re.compile(r'[A-Z]{4}')
    cnr2 = re.compile(r'(\d{7})')
    cnr3 = re.compile(r'(\d{6})')
    cnr4 = re.compile(r'(\d{3})')
    cnr5 = re.compile(r'(\d{1})')
    cnr6 = re.compile(r'([A-Z]{4}\s{0,1}\d{3}\s{0,1}\d{3}\s{0,1}\d{1})')

    """
    Here,
    tSize -> Length of texts list to maintain iterator
    a -> iterator
    conNo -> Initializing empty string for container no.
    conType -> Initializing empty string for container no. type -> (4l 7d,4l 6d 1d,4l 3d 3d 1d,4l7d)

    The algorithm :-
    if a string in list has only 4 letters ->
        if next string in the list has only 7d -> (4l 7d)
        else if next string in the list has only 6 digits ->
            if next string in the list has only 1 digits -> (4l 6d 1d)
            else -> continue
        else if next string in the list has only 3 digits ->
            if next string in the list has only 3 digits ->
                if next string in the list has only 1 digits -> (4l 3d 3d 1d)
                else -> continue
            else -> continue
        else -> continue
    else if a string is in following configuration: MRKU9595198, MRKU 9595198, MRKU 959519 8,MRKU 959 519 8 -> (4l7d)
    else -> continue
    """
    tSize = len(texts)
    a=-1
    conNo=""
    conType=""
    for text in texts:
        # Increaing iterator
        a=a+1
        # print(a)
        if((a<tSize-1) and cnr1.search(text.description) and len(text.description)==4):
            if(cnr2.search(texts[a+1].description) and len(texts[a+1].description)==7):
                conType = "4l 7d"
                conNo = text.description+" "+texts[a+1].description
                break
            elif((a<tSize-2) and cnr3.search(texts[a+1].description) and len(texts[a+1].description)==6):
                if(cnr5.search(texts[a+2].description) and len(texts[a+2].description)==1):
                    conType = "4l 6d 1d"
                    conNo = text.description+" "+texts[a+1].description+texts[a+2].description
                    break
                else:
                    continue
            elif((a<tSize-3) and cnr4.search(texts[a+1].description) and len(texts[a+1].description)==3):
                if(cnr4.search(texts[a+2].description) and len(texts[a+2].description)==3):
                    if(cnr5.search(texts[a+3].description) and len(texts[a+3].description)==1):
                        conType = "4l 3d 3d 1d"
                        conNo = text.description+" "+texts[a+1].description+texts[a+2].description+texts[a+3].description
                        break
                    else:
                        continue
                else:
                    continue
            else:
                continue
        elif(cnr6.search(text.description) and len(text.description)==11):
            conType = "4l7d"
            conNo = text.description[:4]+" "+text.description[4:]
            print(conNo)
            break
        else:
            continue

    # Validating the extracted container number according to the ISO 6346 standards
    validCheck = iso6346.is_valid(conNo)
    print(validCheck)

    if(validCheck):
        return conNo,conType
    else:
        conNo = "Try again"

    return conNo,conType

#______________________________________________________________________________

def detect_vehicle_plate_vision():
    """
    Creating GOOGLE_APPLICATION_CREDENTIALS enviroment from "client_secrets_gs.json" file.
    These creds are associated with gcp of account 17uec122@lnmiit.ac.in
    """
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"]="client_secrets_gs.json"

    #Downloading the image in vn1.jpeg and running vision api
    client = vision.ImageAnnotatorClient()
    fn=os.path.join(os.path.dirname(__file__),'vn1.jpeg')
    with io.open(fn, 'rb') as image_file:
        content = image_file.read()
    image = vision.Image(content=content)
    response = client.text_detection(image=image)

    # Responses from vision collected in texts list
    texts = response.text_annotations

    # Taking all content recognised and making it one consecutive string
    ans = texts[0].description
    ans = ''.join(ans.split())

    # Using compiled RegEx to search for Vehicle number
    vehicleNoRegex = re.compile(r'[A-Z]{2}[ -_.]{0,1}\d{1,2}[ -_.]{0,1}[A-Z]{1,3}\d{4}')
    mo = vehicleNoRegex.search(ans)
    vehNo = mo.group()

    return vehNo

#______________________________________________________________________________

#Starting the flask app
app = Flask(__name__)

# Home
@app.route('/')
def hello_world():
    return 'Welcome to Scanify\'s back-end server'

# Creating an endpoint to detect container image by taking in arguments:
# id -> Drive id of the uploaded image
# row -> Row number of the updated cell
@app.route('/detect_container')

def detectcn():

    # Find a workbook by name and open the first sheet
    # Make sure you use the right name here.
    sheet = client.open("TestApp").sheet1

    # getting row of updated cell and id of the image from the URL
    row = request.args.get('row')
    id = request.args.get('id')

    # Using pyDrive to fectch the container image from the google drive with
    # the help of it's id and downloading the file as 'cn1.jpeg'.
    file6 = drive.CreateFile({'id': id})
    file6.GetContentFile('cn1.jpeg')

    # Returning container number from function detect_container_vision in textr
    textr,textType=detect_container_vision()
    # Updating the text in cell with triggered row and 3rd column in the sheet from here only
    sheet.update_cell(row, 3, textr)

    return textType+" Done"

# Creating an endpoint to detect vehicle plate image by taking in arguments:
# id -> Drive id of the uploaded image
# row -> Row number of the updated cell
@app.route('/detect_vehicle_plate')

def detectvp():

    # Find a workbook by name and open the first sheet
    # Make sure you use the right name here.
    sheet = client.open("TestApp").sheet1

    # getting row of updated cell and id of the image from the URL
    row = request.args.get('row')
    id = request.args.get('id')

    # Using pyDrive to fectch the vehicle plate image from the google drive with
    # the help of it's id and downloading the file as 'vn1.jpeg'.
    file6 = drive.CreateFile({'id': id})
    file6.GetContentFile('vn1.jpeg')

    # Returning container number from function detect_vehicle_plate_vision in textr
    textr=detect_vehicle_plate_vision()
    # Updating the text in cell with triggered row and 4th column in the sheet from here only
    sheet.update_cell(row, 4, textr)

    return "Done Vehicle Plate"

if __name__ == '__main__':
    app.run(debug=True,port=8000)
