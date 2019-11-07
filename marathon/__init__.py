

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_required
from flask_migrate import Migrate

app = Flask(__name__)
app.config.from_object('marathon.config')

login_manager = LoginManager()
login_manager.init_app(app)

db = SQLAlchemy(app)
db.session.configure(autoflush=False)
db_connection = db.engine.connect()


######### Required in Case of firing complex queries without ORM #########
import cx_Oracle
conn = cx_Oracle.connect('G1_team02/ceG1_team02@144.214.177.102/xe')
cur = conn.cursor()
######### Required in Case of firing complex queries without ORM #########



from marathon import models
from marathon import routes


from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

migrate = Migrate(app, db)
'''
some_engine = create_engine('oracle://G1_team02:ceG1_team02@144.214.177.102:1521/xe')
Session = sessionmaker(bind=some_engine)
session = Session()
'''