from flask import Flask, render_template, request, jsonify, Response
import pyexcel as pe
import phonenumbers
from phonenumbers import geocoder
import re
import os
from werkzeug.utils import secure_filename


app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'xlsx'
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['ALLOWED_EXTENSIONS'] = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'xlsx'])

main_file_path = ''
main_save_path = ''

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in app.config['ALLOWED_EXTENSIONS']

@app.route('/')
def hello_world():
    return render_template("home.html")


@app.route('/upload', methods=['POST'])
def upload():
    if request.method == 'POST':
        f = request.files['ex']
        filename = secure_filename(f.filename)
        up_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        f.save(up_path)
        return 'file uploaded successfully'
    else:
        return False


@app.route('/ajax', methods=['POST'])
def ajax():
    email = request.form['email']
    name = request.form['name']

    if email and name:
        newName = name[::-1]

        return jsonify({'name': newName})
    return jsonify({'error': 'Missing Data'})


@app.route('/getfile/<name>')
def get_output_file(name):
    file_name = os.path.join('clean/', name)
    if not os.path.isfile(file_name):
        return jsonify({"message": "still processing"})
    # read without gzip.open to keep it compressed
    with open(file_name, 'rb') as f:
        resp = Response(f.read())
    # set headers to tell encoding and to send as an attachment
    resp.headers["Content-Disposition"] = "attachment; filename={0}".format(name)
    resp.headers["Content-type"] = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    return resp


@app.route('/uploadajax', methods=['POST'])
def upldfile():
    global main_save_path
    global main_file_path
    if request.method == 'POST':
        files = request.files['file']
        if files and allowed_file(files.filename):
            filename = secure_filename(files.filename)
            app.logger.info('FileName: ' + filename)
            updir = os.path.join(basedir, 'xlsx/')
            file_path = os.path.join(updir, filename)
            main_file_path = file_path
            main_save_path = os.path.join(basedir, 'clean/', "clean_"+filename)
            files.save(file_path)
            file_size = os.path.getsize(file_path)
            process_file()
            return jsonify(url="/getfile/clean_"+filename, size=file_size)


def process_file():
    split_it = re.compile('[0-9+\- ]+')
    is_plus = re.compile('^\+.+')

    sheet = pe.get_sheet(file_name=main_file_path, name_columns_by_row=0)
    major_col = sheet.column

    new_col = [['Country Code', 'National Number', 'Number Country']]

    print("Strarting")
    for i in range(0, len(major_col['Name'])):
        numbers = str(major_col['Mobile'][i])

        col = []

        number_country_code = 'N/A'
        number_num = ''
        number_country_name = 'N/A'

        splited_number = re.findall(split_it, numbers)

        number_country_code_arr = []
        number_num_arr = []
        number_country_name_arr = []

        for number in splited_number:
            match_plus = is_plus.match(number)
            try:
                if match_plus:
                    num = phonenumbers.parse(number, None)

                else:
                    num = phonenumbers.parse(number, 'IN')
                number_country_code_arr += [str(num.country_code)]
                number_num_arr += [str(num.national_number)]
                number_country_name_arr = [str(geocoder.country_name_for_number(num, 'en'))]
            except:
                pass

            number_country_code = ", ".join(number_country_code_arr)
            number_num = ", ".join(number_num_arr)
            number_country_name = ", ".join(number_country_name_arr)

            if len(number_num_arr) == 1:
                number_country_code = int(number_country_code)
                number_num = int(number_num)

            # if len(number_num_arr) > 1:
            #     number_country_code = ", ".join(number_country_code_arr)
            #     number_num = ", ".join(number_num_arr)
            #     number_country_name = ", ".join(number_country_name_arr)
            # else:
            #     try:
            #         number_country_code = int(number_country_code_arr)
            #         number_num = int(number_num_arr)
            #     except:
            #         pass

        col = [
            number_country_code,
            number_num,
            number_country_name
        ]

        new_col += [col]

    new_sheet = pe.Sheet(new_col)
    sheet.column += new_sheet

    sheet.save_as(main_save_path)
