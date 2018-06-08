from flask import Flask, render_template, jsonify, request, Response
from werkzeug.utils import secure_filename
import os

import pyexcel as pe
from geo import GeoText
import phonenumbers
from phonenumbers import geocoder
import re
import pycountry

app = Flask(__name__)

app.config['UPLOAD_FOLDER'] = 'xlsx'
basedir = os.path.abspath(os.path.dirname(__file__))

name_fields = {
    'number': 'Number',
    'address': 'Address'
}

filename = ''

main_file_path = ''
main_save_path = ''

check_fields = {
    'country_code': False,
    'number': False,
    'number_country': False,

    'city': False,
    'add_country': False
}

app.config['ALLOWED_EXTENSIONS'] = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'xlsx'])
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in app.config['ALLOWED_EXTENSIONS']

def reset():
    global name_fields
    global filename
    global main_save_path
    global main_file_path
    global check_fields

    name_fields = {
        'number': 'Number',
        'address': 'Address'
    }

    filename = ''

    main_file_path = ''
    main_save_path = ''

    check_fields = {
        'country_code': False,
        'number': False,
        'number_country': False,

        'city': False,
        'add_country': False
    }

@app.route('/')
def hello_world():
    return render_template("index.html")


@app.route('/uploadfile', methods=['POST'])
def upload():
    if request.method == 'POST':
        reset()
        files = request.files['file']
        if files and allowed_file(files.filename):
            filename = secure_filename(files.filename)
            app.logger.info('FileName: ' + filename)
            updir = os.path.join(basedir, 'xlsx/')
            file_path = os.path.join(updir, filename)
            files.save(file_path)
            return jsonify(status='ok', mess=filename)
        else:
            return jsonify(status='err', mess='File Type not Allowed')

@app.route('/getfile/<name>')
def get_output_file(name):
    file_name = os.path.join('clean/', name)
    if not os.path.isfile(file_name):
        return jsonify({"message": "still processing"})
    # read without gzip.open to keep it compressed
    with open(file_name, 'rb') as f:
        resp = Response(f.read())
    os.remove(file_name)
    # set headers to tell encoding and to send as an attachment
    resp.headers["Content-Disposition"] = "attachment; filename={0}".format(name)
    resp.headers["Content-type"] = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    return resp

@app.route('/processfile', methods=['POST'])
def process():
    global name_fields
    global check_fields
    global filename
    global main_file_path
    global main_save_path

    reset()

    if request.method == 'POST':
        try:
            f = request.form

            if not f['number'] == '':
                name_fields['number'] = f['number']
            if not f['address'] == '':
                name_fields['address'] = f['address']

            if 'numCountryCode' in f:
                check_fields['country_code'] = True
            if 'numNumber' in f:
                check_fields['number'] = True
            if 'countryName' in f:
                check_fields['number_country'] = True

            if 'city' in f:
                check_fields['city'] = True
            if 'addressCountry' in f:
                check_fields['add_country'] = True

            filename = f['filename']

            main_save_path = os.path.join(basedir, 'clean/', "clean_" + filename)
            main_file_path = os.path.join(basedir, 'xlsx/', filename)

            try:
                clean()
                return jsonify(status='ok', mess="/getfile/clean_"+filename,
                               mainpath=main_file_path,
                               main_save_path=main_save_path,
                               numberf=name_fields['number'],
                               address=name_fields['address'],
                               checkcc=check_fields['country_code'],
                               checknum=check_fields['number'],
                               checknumcon=check_fields['number_country'],
                               city=check_fields['city'],
                               addcon=check_fields['add_country']
                               )
            except Exception as err:
                app.logger.info(err)

                return jsonify(
                    status='err',
                    mess='Plz Remove Formatting From File !',
                    mainpath=main_file_path,
                    main_save_path=main_save_path,
                    numberf=name_fields['number'],
                    address=name_fields['address'],
                    checkcc=check_fields['country_code'],
                    checknum=check_fields['number'],
                    checknumcon=check_fields['number_country'],
                    city=check_fields['city'],
                    addcon=check_fields['add_country']
                )
        except Exception as err:
            app.logger.info(err)
            return jsonify(status='err', mess='Unknown Error',
                           mainpath=main_file_path,
                           main_save_path=main_save_path,
                           numberf=name_fields['number'],
                           address=name_fields['address'],
                           checkcc=check_fields['country_code'],
                           checknum=check_fields['number'],
                           checknumcon=check_fields['number_country'],
                           city=check_fields['city'],
                           addcon=check_fields['add_country']
                           )


def clean():
    global name_fields
    global check_fields
    global filename
    global main_save_path
    global main_file_path

    split_it = re.compile('[0-9+\- ]+')
    is_plus = re.compile('^\+.+')

    sheet = pe.get_sheet(file_name=main_file_path, name_columns_by_row=0)
    major_col = sheet.column

    app.logger.info('Sheet: ' + main_save_path)

    new_col = []

    columns = []

    if check_fields['city']:
        columns += ['City']
    if check_fields['add_country']:
        columns += ['Country']

    if check_fields['country_code']:
        columns += ['Country Code']
    if check_fields['number']:
        columns += ['Number']
    if check_fields['number_country']:
        columns += ['Country Name']

    new_col += [columns]

    app.logger.info("this  h")
    app.logger.info(new_col)

    for i in range(0, len(major_col['Name'])):

        col = []

        if check_fields['add_country'] or check_fields['city']:
            try:
                city_added = False
                add_country_added = False
                address = str(major_col[name_fields['address']][i])
                geox = GeoText(address.title())
                cities = geox.cities
                app.logger.info(cities)
                if check_fields['city']:
                    if len(cities) > 0:
                        if not str(cities[0]) == '':
                            col += [str(cities[0])]
                        else:
                            col += ['N/A']
                    else:
                        col += ['N/A']
                if check_fields['add_country']:
                    country_str = ''
                    for c in geox.country_mentions:
                        country_str += pycountry.countries.get(alpha_2=c).name + ", "
                    temp_kuch_str = country_str[0:-2]
                    if not temp_kuch_str == '':
                        col += [temp_kuch_str]
                    else:
                        col += ['N/A']
            except Exception as err:
                app.logger.info(err)

        if check_fields['country_code'] or check_fields['number'] or check_fields['number_country']:
            try:
                numbers = str(major_col[name_fields['number']][i])

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
                    except Exception as err:
                        app.logger.info(err)

                    for j in range(0, len(number_num_arr)):
                        if check_fields['country_code']:
                            col += [int(number_country_code_arr[j])]
                        if check_fields['number']:
                            col += [int(number_num_arr[j])]
                        if check_fields['number_country']:
                            col += [str(number_country_name_arr[j])]
                    if len(number_num_arr) == 0:
                        if check_fields['country_code']:
                            col += ['N/A']
                        if check_fields['number']:
                            col += ['N/A']
                        if check_fields['number_country']:
                            col += ['N/A']

                    # if len(number_num_arr) > 1:
                    #     number_country_code = ", ".join(number_country_code_arr)
                    #     number_num = ", ".join(number_num_arr)
                    #     number_country_name = ", ".join(number_country_name_arr)
                    # if len(number_num_arr) == 1:
                    #     number_country_code = int(number_country_code_arr[0])
                    #     number_num = int(number_num_arr[0])
                    #     number_country_name = str(number_country_name_arr[0])
                    # if check_fields['country_code']:
                    #     col += [number_country_code]
                    # if check_fields['number']:
                    #     col += [number_num]
                    # if check_fields['number_country']:
                    #     col += [number_country_name]
            except Exception as err:
                app.logger.info(err)

        new_col += [col]

    new_sheet = pe.Sheet(new_col)
    sheet.column += new_sheet

    sheet.save_as(main_save_path)

if __name__ == '__main__':
    app.run(debug=True)