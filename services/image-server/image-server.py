import logging
import os
import sys
from string import Template

import flask
from flask import Flask
from flask_cors import CORS
import mysql.connector

import requests

logging.basicConfig(stream=sys.stdout, level=logging.INFO)

##############
## Vars init #
##############
# Helper database
db_user = os.getenv('database-user', 'xraylab')
db_password = os.getenv('database-password', 'xraylab')
db_host = os.getenv('database-host', 'xraylabdb')
db_db = os.getenv('database-db', 'xraylabdb')
service_point = os.getenv('service_point', 'http://ceph-nano-0/')

# Bucket base name
bucket_base_name = os.getenv('bucket-base-name', 'images')

########
# Code #
########
def get_last_image(bucket_name):
    """Retrieves the last uploaded image in a bucket, according to helper database timestamp."""

    # Correspondance table between bucket names and table names. Yeah, I know...
    bucket_table = {bucket_base_name:'images_uploaded',bucket_base_name+'-processed':'images_processed',bucket_base_name+'-anonymized':'images_anonymized',}
    try:
        cnx = mysql.connector.connect(user=db_user, password=db_password,
                                      host=db_host,
                                      database=db_db)
        cursor = cnx.cursor()
        query = 'SELECT name FROM ' + bucket_table[bucket_name] + ' ORDER BY time DESC LIMIT 1;'
        cursor.execute(query)
        data = cursor.fetchone()
        if data is not None:
            result = data[0]
        else:
            result = ""
        cursor.close()
        cnx.close()

    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        raise

    return result

# Response templates 
LOCATION_TEMPLATE_SMALL = Template("""
    <img src="/download_image/${bucket_name}/${image_name}" style="width:260px;"></img>""")

LOCATION_TEMPLATE_BIG = Template("""
    <img src="/download_image/${bucket_name}/${image_name}" style="width:575px;"></img>""")

# Main Flask app
app = Flask(__name__)
CORS(app)

# Test route
@app.route('/')
def homepage():
    return "Hello world"

# Answers with last image from <bucketname>, formatted as small
@app.route('/last_image_small/<bucket_name>')
def last_image_small(bucket_name):
    image_name = get_last_image(bucket_name)
    if image_name != "":   
        html = LOCATION_TEMPLATE_SMALL.substitute(bucket_name=bucket_name, image_name=image_name)
    else:
        html = '<h2 style="font-family: Roboto,Helvetica Neue,Arial,sans-serif;text-align: center; color: white;font-size: 15px;font-weight: 400;">No image to show</h2>'
    return html

# Answers with last image from <bucketname>, formatted as big
@app.route('/last_image_big/<bucket_name>')
def last_image_big(bucket_name):
    image_name = get_last_image(bucket_name)   
    if image_name != "":   
        html = LOCATION_TEMPLATE_BIG.substitute(bucket_name=bucket_name, image_name=image_name)
    else:
        html = '<h2 style="font-family: Roboto,Helvetica Neue,Arial,sans-serif;text-align: center; color: white;font-size: 15px;font-weight: 400;">No image to show</h2>'
    return html

@app.route('/download_image/<bucket_name>/<image_name>')
def download_image(bucket_name, image_name):
    fp = requests.get('http://%s/%s/%s'% (service_point, bucket_name, image_name), stream=True)
    return flask.send_file(fp.raw, mimetype='image/jpeg')

# Launch Flask server
if __name__ == '__main__':
    app.run(host='0.0.0.0')

