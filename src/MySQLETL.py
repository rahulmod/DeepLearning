import cursor as cursor
import pymysql
from Tools.scripts.make_ctype import method

pymysql.install_as_MySQLdb()
import MySQLdb

# Open database connection
db = MySQLdb.connect("localhost","hadoop1","welcome1","TEST")  #port 3306
# db = pymysql.connect(host='localhost',
#                        user='hadoop2',
#                        password='welcome2',
#                        db='test',
#                        charset='utf8mb4',
#                        cursorclass=pymysql.cursors.DictCursor)
# prepare a cursor object using
cursor()
method
cursor = db.cursor()

# Prepare SQL query to INSERT a record into the database.
sql = """INSERT INTO STUDENT(NAME,SUR_NAME, ROLL_NO) VALUES ('Rahul', 'Mod', 1)"""
try:
    # Execute the SQL command
    cursor.execute(sql)
    # Commit your changes in the database
    db.commit()
except:
    # Rollback in case there is any error
    db.rollback()
    # disconnect from server
    db.close()