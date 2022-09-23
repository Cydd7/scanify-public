Readme file for testFlask 
-----------------------------------------------------------------------

To activate virtualenv and run application
->source bin/activate          
->python3.10 app.py
-----------------------------------------------------------------------

To test the application 
http://127.0.0.1:8000/detect_container?row=row_no&id=drive_file_id
http://127.0.0.1:8000/detect_vehicle_plate?row=row_no&id=drive_file_id
-----------------------------------------------------------------------

client_sectrets_gs.json -> To authenticate gspread and vision
client_secrets.json -> To authenticate pydrive 
Credentials.json and mycreds.txt -> To regenerate token for pydrive
-----------------------------------------------------------------------

cn1.jpeg -> Container image file downloads here
vn1.jpeg -> Vehicle plate image file downloads here

