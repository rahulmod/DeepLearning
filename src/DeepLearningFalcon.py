import falcon
from falcon_cors import CORS
import json

from numpy import unicode
from sqlalchemy import *
from sqlalchemy.orm import sessionmaker
import pygeoip
from pymongo import MongoClient
import json
import datetime as dt
import ipaddress
import math
from concurrent.futures import *
from sqlalchemy.engine import Engine
from sqlalchemy import event
import sqlite3

@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA cache_size=100000")
    cursor.close()

class Predictor(object):

    def __init__(self,domain):
        db1 = create_engine('sqlite:///score_' + domain + '0test.db')
        db2 = create_engine('sqlite:///probability_' + domain +'0test.db')
        db3 = create_engine('sqlite:///ctr_'+ domain + 'test.db')

        metadata1 = MetaData(db1)
        metadata2 = MetaData(db2)
        metadata3 = MetaData(db3)
        self.scores = Table('scores', metadata1, autoload=True)
        self.probabilities = Table('probabilities', metadata2,
                                   autoload=True)
        self.ctr = Table('ctr', metadata3, autoload=True)
        client = MongoClient(connect=False,maxPoolSize=1)
        self.db = client.frequency
        self.gi = pygeoip.GeoIP('GeoIP.dat')
        self.high = 1.2
        self.low = .8

    def get_hour(self,timestamp):
        return dt.datetime.utcfromtimestamp(timestamp / 1e3).hour

    def get_score(self, featurename, featurevalue):
        prob = 0
        pred = 0
        s = self.scores.select((self.scores.c.feature_name == featurename) & (self.scores.c.feature_value == featurevalue))

        rs = s.execute()
        row = rs.fetchone()
        if row is not None:
            pred = pred + float(row['score'])
            s = self.probabilities.select((self.probabilities.c.feature_name == featurename) & (self.probabilities.c.feature_value == featurevalue))
            rs = s.execute()
            row = rs.fetchone()

        if row is not None:
            prob = prob + float(row['Probability'])
            return pred, prob

    def get_value(self, f, value):
        if f == 'ip':
            ip = str(ipaddress.IPv4Address(ipaddress.ip_address(value)))
            geo = self.gi.country_name_by_addr(ip)
            pred1, prob1 = self.get_score('geo', geo)
            res = self.db.frequency.find_one({"ip" : ip})
            freq = 1

            if res is not None:
                freq = res['frequency']
                pred2, prob2 = self.get_score('frequency', str(freq))
                return (pred1 + pred2), (prob1 + prob2)
            if f == 'root':
                s = self.ctr.select(self.ctr.c.root == value)
                rs = s.execute()
                row = rs.fetchone()
            if row is not None:
                ctr = row['ctr']
                avv = row['avt']
                avt = row['avv']
                (pred1,prob1) = self.get_score('ctr', ctr)
                (pred2,prob2) = self.get_score('avt', avt)
                (pred3,prob3) = self.get_score('avv', avv)

                (pred4,prob4) = self.get_score(f, value)
                return (pred1 + pred2 + pred3 + pred4), (prob1 + prob2 + prob3 + prob4)

            if f == 'client_time':
                value = str(self.get_hour(int(value)))
            if f == 'domain':
                conn = sqlite3.connect('multiplier.db')
                cursor = conn.execute("SELECT high,low from multiplier where domain='" + value + "'")
                row = cursor.fetchone()

            if row is not None:
                self.high = row[0]
                self.low = row[1]
                return self.get_score(f, value)

    def on_post(self, req, resp):
        input_json = json.loads(req.stream. read(),encoding='utf-8')
        input_json['ip'] = unicode(req.remote_addr)
        pred = 1
        prob = 1

        with ThreadPoolExecutor(max_workers=8) as pool:
            future_array = { pool.submit(self.get_value,f,input_json[f]) : f for f in input_json}
            for future in as_completed(future_array):
                pred1, prob1 = future.result()
                pred = pred + pred1
                prob = prob - prob1

        resp.status = falcon.HTTP_200

        res = math.exp(pred)-1
        if res < 0:
            res = 0
        prob = math.exp(prob)
        if(prob <= .1):
            prob = .1
        if(prob >= .9):
            prob = .9
        multiplier = self.low + (self.high -self.low)*prob
        pred = multiplier*pred
        resp.body = str(pred)

cors = CORS(allow_all_origins=True,allow_all_methods=True,allow_all_headers=True)
wsgi_app = api = falcon.API(middleware=[cors.middleware])
f = open('publishers1.list')
for domain in f:
    domain = domain.strip()
    p = Predictor(domain)
    url = '/predict/' + domain
    api.add_route(url, p)
