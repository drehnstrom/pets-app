from flask import Flask, render_template, request, redirect
import uuid
import json
import os
import random
import googlecloudprofiler
import googleclouddebugger
from google.cloud import error_reporting
from opencensus.ext.stackdriver import trace_exporter as stackdriver_exporter
import opencensus.trace.tracer


BUCKET_NAME = 'doug-rehnstrom-pets'
PROJECT_NAME = 'doug-rehnstrom'

import pet_db
import pet_storage

app = Flask(__name__)


@app.route("/", methods=['GET', 'POST'])
def main():
    if request.method == 'GET':
        pets = pet_db.get_pets()
        model = {"title": "Pets App", "header": "Some Pets", "pets": pets}
        print('Pets Home Page Requested!')

    if request.method == 'POST':
        data = request.form.to_dict(flat=True)
        pets = pet_db.search_pets(data['search'])
        model = {"title": "My Pet's Great", 
                 "header": "Some Pets!", "pets": pets}
        print('Search Requested: ' + data['search'])

    # Throm Randoms Errors approx 2% of the time
    # Raise unhandled exception 2% of the time
    num = random.randrange(49)
    if num == 0:
        client = error_reporting.Client()
        client.report("Threw 500 error randomly.")
        return json.dumps({"error": 'Error thrown randomly'}), 500
    elif num == 1:
        raise Exception("This was an unhandled exception")
    else:
        return render_template('index.html', model=model)


@app.route("/add", methods=['GET', 'POST'])
def add():
    if request.method == 'GET':
        model = {"title": "Pets App", "header": "Add a Pet"}
        print('Pets Add Page Requested!')
        return render_template('add.html', model=model)

    if request.method == 'POST':
        try:
            data = request.form.to_dict(flat=True)
            image_file = request.files['image']
            image_name = str(uuid.uuid4())
            # Save the Pet Photo
            if os.getenv('GAE_ENV', '').startswith('standard'):
                tracer.start_span(name='save_pet')
            pic_url = pet_storage.save_pet_picture(image_file, image_name)
            print('Pet photo saved:{}'.format(pic_url))
            pet_db.save_pet(data, image_name)
            print('Pet info saved:{}'.format(data))
            if os.getenv('GAE_ENV', '').startswith('standard'):
                tracer.end_span()
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
    model = {"title": "Pets App",
             "header": "An Error Occured!", "message": message}
    print(message)
    return render_template('error.html', model=model)


@app.route("/signin")
def signin():
    model = {"title": "Pets App", "header": "Sign In"}
    print('Pets Signin Page Requested!')
    return render_template('signin.html', model=model)


@app.route("/test")
def test():
    print('Pets test route Requested!')
    return render_template('test.html')


@app.route("/randomerror")
def randomError():
    print('Random Error Occurred')
    client = error_reporting.Client()
    client.report("randomerror route called")
    return json.dumps({"error": 'Server Error'}), 500


@app.route("/throw")
def throw():
    print('Threw an exception on purpose.')
    client = error_reporting.Client()
    client.report("throw route called")
    raise Exception('Threw this exception on purpose.')


# Profiler initialization. It starts a daemon thread which continuously
# collects and uploads profiles. Best done as early as possible.
try:
    googlecloudprofiler.start(verbose=3)
except (ValueError, NotImplementedError) as exc:
    print(exc)  # Handle errors here
except Exception:
    pass

# Enable's the Debugger.
try:
    googleclouddebugger.enable()
except (ImportError, RuntimeError, RuntimeError, Exception) as ext:
    pass

# Initialize tracer - Only do this in GCP
if os.getenv('GAE_ENV', '').startswith('standard'):
    exporter = stackdriver_exporter.StackdriverExporter(project_id=PROJECT_NAME)
    tracer = opencensus.trace.tracer.Tracer(exporter=exporter,
                                        sampler=opencensus.trace.tracer.samplers.AlwaysOnSampler())


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
