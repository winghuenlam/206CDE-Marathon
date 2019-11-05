'''

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_mysqldb import MySQL
import yaml
from flask_migrate import Migrate

######### Enable this for debugging #########
# import logging
# logging.basicConfig()
# logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
# SQLALCHEMY_TRACK_MODIFICATIONS = True
######## Enable this for debugging #########

app = Flask(__name__)
app.config['SECRET_KEY'] = '5791628bb0b13ce0c676dfde280ba245'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://206cde:206cde@localhost/206cde'
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
app.secret_key = 'random string'
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = set(['jpeg', 'jpg', 'png', 'gif'])
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

migrate = Migrate(app, db)

######### Required in Case of firing complex queries without ORM #########
db2 = yaml.load(open('config.yaml'))
app.config['MYSQL_HOST'] = db2['mysql_host']
app.config['MYSQL_USER'] = db2['mysql_user']
app.config['MYSQL_PASSWORD'] = db2['mysql_password']
app.config['MYSQL_DB'] = db2['mysql_db']
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
mysql = MySQL(app)
######### Required in Case of firing complex queries without ORM #########


# login_manager = LoginManager(app)
# login_manager.login_view = 'login'
# login_manager.login_message_category = 'info'
#
from marathon import models
from marathon import routes

models.db.create_all()
'''

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_required

app = Flask(__name__)
app.config.from_object('marathon.config')

login_manager = LoginManager()
login_manager.init_app(app)

db = SQLAlchemy(app)
db_connection = db.engine.connect()


######### Required in Case of firing complex queries without ORM #########
import cx_Oracle
conn = cx_Oracle.connect('G1_team02/ceG1_team02@144.214.177.102/xe')
cur = conn.cursor()
######### Required in Case of firing complex queries without ORM #########

'''
cur.execute('SELECT * FROM "user"')

for row in cur.fetchall():
	print("email[{0}], pw[{1}]".format(row[0], row[1]))
'''

from marathon import models
from marathon import routes




