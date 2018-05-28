from bson.json_util import dumps
from bson.json_util import loads
from pymongo import MongoClient

from flask import Flask, request, g
from flask_cors import CORS
import tensorflow as tf
from numpy import unicode
from sqlalchemy import *
from sqlalchemy.orm import sessionmaker
import pygeoip
import datetime as dt
import ipaddress
import math

app = Flask(__name__)
CORS(app)

@app.before_request
def before():
    db = create_engine('sqlite:///score.db')
    metadata = MetaData(db)

    g.scores = Table('scores', metadata, autoload=True)
    Session = sessionmaker(bind=db)
    g.session = Session()
    client = MongoClient()
    g.db = client.frequency
    g.gi = pygeoip.GeoIP('GeoIP.dat')
    sess = tf.Session()
    new_saver = tf.train.import_meta_graph('model.obj.meta')
    new_saver.restore(sess, tf.train.latest_checkpoint('./'))
    all_vars = tf.get_collection('vars')
    g.dropped_features = str(sess.run(all_vars[0]))
    g.b = sess.run(all_vars[1])[0]
    return

def get_hour(timestamp):
    return dt.datetime.utcfromtimestamp(timestamp / 1e3).hour

def get_value(session, scores, feature_name, feature_value):
    s = scores.select((scores.c.feature_name == feature_name) & (scores.c.feature_value == feature_value))
    rs = s.execute()
    row = rs.fetchone()
    if row is not None:
        return float(row['score'])
    else:
        return 0.0

@app.route('/predict', methods=['POST'])
def predict():
    input_json = request.get_json(force=True)
    features = ['size','domain','client_time','device', 'ad_position','client_size', 'ip','root']
    predicted = 0
    feature_value = ''
    for f in features:
        if f not in g.dropped_features:
            if f == 'ip':
                feature_value = str(ipaddress.IPv4Address(ipaddress.ip_address(unicode(request.remote_addr))))
            else:
                feature_value = input_json.get(f)

            if f == 'ip':
                if 'geo' not in g.dropped_features:
                    geo = g.gi.country_name_by_addr(feature_value)
                    predicted = predicted + get_value(g.session, g.scores, 'geo', geo)
                if 'frequency' not in g.dropped_features:
                    res = g.db.frequency.find_one({"ip" : feature_value})
                    freq = 1
                    if res is not None:
                        freq = res['frequency']
                    predicted = predicted + get_value(g.session, g.scores,'frequency', str(freq))

            if f == 'client_time':
                feature_value = get_hour(int(feature_value))

            predicted = predicted + get_value(g.session, g.scores, f, feature_value)
    return str(math.exp(predicted + g.b)-1)
    app.run(debug = True, host ='0.0.0.0')
