from flask import Flask, render_template, request, redirect
import uuid
import json
import os

BUCKET_NAME = 'doug-rehnstrom-pets'
PROJECT_NAME = 'doug-rehnstrom'

import pet_db
import pet_storage

app = Flask(__name__)


@app.route("/", methods=['GET', 'POST'])
def main():
    if request.method == 'GET':
        pets = pet_db.get_pets()
        model = {"title": "My Pet's Super-Great!!!", "header": "Some Pets", "pets": pets}
        print('Pets Home Page Requested!')

    if request.method == 'POST':
        data = request.form.to_dict(flat=True)
        pets = pet_db.search_pets(data['search'])
        model = {"title": "My Pet's Great", 
                 "header": "Some Pets!", "pets": pets}
        print('Search Requested: ' + data['search'])
    return render_template('index.html', model=model)


@app.route("/add", methods=['GET', 'POST'])
def add():
    if request.method == 'GET':
        model = {"title": "My Pet's Great", "header": "Add a Pet"}
        return render_template('add.html', model=model)

    if request.method == 'POST':
        try:
            data = request.form.to_dict(flat=True)
            image_file = request.files['image']
            image_name = str(uuid.uuid4())
            # Save the Pet Photo
            pic_url = pet_storage.save_pet_picture(image_file, image_name)
            print('Pet photo saved:{}'.format(pic_url))
            pet_db.save_pet(data, image_name)
            print('Pet info saved:{}'.format(data))
            return redirect('/')
        except Exception as ex:
            print('An error occurred while saving a pet'.format(str(ex)))
            return redirect('/error/{}'.format(str(ex)))


@app.route("/api/like/<pet_id>")
def like(pet_id):
    print('Like added for {}'.format(pet_id))
    pet = pet_db.add_like(pet_id)
    data = {}
    data['likes'] = pet['likes']
    data['pet_id'] = pet.key.name
    json_data = json.dumps(data)
    return json_data


@app.route("/error/<message>")
def error(message):
    model = {"title": "My Pet's Great", 
             "header": "An Error Occured!", "message": message}
    return render_template('error.html', model=model)


@app.route("/signin")
def signin():
    model = {"title": "My Pet's Great", "header": "Sign In"}
    return render_template('signin.html', model=model)


@app.route("/test")
def test():
    return render_template('test.html')


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
