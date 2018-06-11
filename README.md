# Sheet Clean

`What is this?`  
This is a python script to get all the following from a xlsx file
- country code, country name, and phone number from numbers
- city, country from address

## What you need
- This script
- The Excel file to verify
- Max data 10,000 fields

## How

- open terminal
- Get the script
```
git clone https://github.com/Faisal-Manzer/sheet-clean.git
```
- Go into folder
```
cd sheet-clean
```
- install all requirements
```
pip install -r requirements.txt
```
- Run the script
```
python3 app.py
```

- Go to the URL `http://127.0.0.1:5000`
- Set options
- Drag and drop the xlsx file
- Wait, the cleaned file will be automatically downloaded. For 10,000 data it will take 5-7 min approx

## Take Care
- Remove all formatting from excel file `Home > Clear > All Format` in Excel Ribbon
- Should contain a `Name` filed (case sensitive)
- Max size is 10,000
