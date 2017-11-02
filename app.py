from flask import Flask, session, redirect, url_for, escape, request, render_template, jsonify
import random
from flask.ext.pymongo import PyMongo
from flask.ext.login import LoginManager, UserMixin, login_required, login_user, logout_user 
from flask_wtf import FlaskForm, RecaptchaField
from wtforms import StringField, PasswordField, RadioField, SubmitField, SelectField
from wtforms.validators import DataRequired, Length, EqualTo

app = Flask(__name__)


#DB Credentials
#hidden
mongo = PyMongo(app)

# secret key:
#Hidden

#global
user_details = {}
colors = ['#4DB6AC','#B39DDB','#FF9800','#81C784','#FFC107','#42A5F5','#CE93D8','#00BCD4']

# flask-login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

#app configurations for RECAPTCHA Generation.
app.config['RECAPTCHA_USE_SSL'] = False
app.config['RECAPTCHA_OPTIONS'] = {'theme': 'white'}

#classes for wtforms, Registration form
class RegisterForm(FlaskForm):
	rusername = StringField('Username', validators=[DataRequired()])
	rpassword = PasswordField('Password',validators=[DataRequired()])
	recaptcha = RecaptchaField()
	
#login form
class LoginForm(FlaskForm):
	lusername = StringField('Email', validators=[DataRequired()])
	lpassword = PasswordField('Password',validators=[DataRequired()])

#for flask login, User class
#user class for flask-loginytho
class User(UserMixin):

	def __init__(self, username):
		global user_details
		user_details = mongo.db.users.find_one({"username":username})
		self.username = username
		
	def is_authenticated(self):
		return True

	def is_active(self):
		return True

	def is_anonymous(self):
		return False

	def get_id(self):
		return self.username   

#user defined functions:
def getrandomcolor():
	global colors
	return colors[random.randint(0,7)]

#Routes
@app.route('/')
@login_required
def home():
	global user_details

	analysis = mongo.db.analysis

	num = analysis.find_one({"index":"0"})
	analysis.find_one_and_update({"index":"0"},{"$set":{'hits':str(int(num['hits']) + 1)}})


	return redirect(user_details['pollid'])


@app.route('/login',methods=['GET','POST'])
def login():
	global colors

	db = mongo.db.users
	analysis = mongo.db.analysis

	num = analysis.find_one({"index":"0"})
	analysis.find_one_and_update({"index":"0"},{"$set":{'hits':str(int(num['hits']) + 1)}})

	lform = LoginForm()
	rform = RegisterForm(request.form)

	if request.method == "POST":
		if request.form['btn'] == 'login':
			if lform.validate_on_submit():
				if db.find_one({"username":lform.lusername.data,"password":lform.lpassword.data}):
					data = db.find_one({"username":lform.lusername.data})
					user = User(data['username'])
					login_user(user)
					return redirect("/")
				else:
					return render_template("login.html",lform = lform, rform = rform, color = getrandomcolor(), errors = "Wrong Password or User not Registered.")
			else:
				return render_template("login.html",lform = lform, rform = rform, color = getrandomcolor(), errors = "Please fill all the fields in the form and try again.")

		else:
			if rform.validate():
				if db.find_one({"username":rform.rusername.data}):
					return render_template("login.html",lform = lform, rform = rform, color = getrandomcolor(), errors = "Username already exists, Please try again.")
				else:
					if len(rform.rusername.data) <= 2 or len(rform.rpassword.data) <= 2:
						return render_template("login.html",lform = lform, rform = rform, color = getrandomcolor(), errors = "The Username and Password have to be atleast 3 characters long. Please try again.")
					else:
						db.insert({"username":rform.rusername.data,"password":rform.rpassword.data,"voted":[],"posted":[], "pollid":"0"})
						user = User(rform.rusername.data)
						num = analysis.find_one({'index':"0"})
						analysis.find_one_and_update({'index':"0"},{"$set":{'users':str(int(num['users']) + 1)}})
						login_user(user)
						return redirect("/")
			else:
				return render_template("login.html",lform = lform, rform = rform, color = getrandomcolor(), errors = "Please fill all the fields in the form and try again")
	else:
		return render_template("login.html",lform = lform,rform = rform,color = getrandomcolor(), errors = "")

@app.route('/addpoll',methods=['GET','POST'])
@login_required
def addpoll():
	global colors

	analysis = mongo.db.analysis

	num = analysis.find_one({"index":"0"})
	analysis.find_one_and_update({"index":"0"},{"$set":{'hits':str(int(num['hits']) + 1)}})

	db = mongo.db.pollquestions
	analysis = mongo.db.analysis
	pending = mongo.db.pending
	dbusers = mongo.db.users

	if request.method == 'POST':
		choices = {}
		question = request.form['pollquestion']
		
		choice1 = request.form['choice1']
		if choice1 != "":
			choices[choice1.strip()]= {"votes":"0"}

		choice2 = request.form['choice2']
		if choice2 != "":
			choices[choice2.strip()]= {"votes":"0"}
		
		choice4 = ""
		choice3 = ""
		
		if "choice3" in request.form:
			choice3 = request.form['choice3']
			if choice3 != "":
				choices[choice3.strip()]= {"votes":"0"}

		if "choice4" in request.form:
			choice4 = request.form['choice4']
			if choice4 != "":
				choices[choice4.strip()]= {"votes":"0"}

		num = len(list(db.find())) + len(list(pending.find()))

		if question != "":

			if len(choices.keys()) >= 2:
				# choiceid = []
				for i in choices.keys():
					_id = []
					for j in i:
						if ord(j) >= 32 and ord(j) <= 47 or ord(j) >= 58 and ord(j) <= 64 or ord(j) >= 91 and ord(j) <= 96 or ord(j) >= 123 and ord(j) <= 127:
							pass
						else:
							_id.append(j)
					
					choices[i]['id'] = "".join(_id)

				pending.insert({'question':question, 'pollid':str(num), 'choices':choices, 'totalvotes':"0"})
				
				user_details['posted'].append(str(num))
				dbusers.find_one_and_update({'username':user_details['username']},{"$set":{'posted':user_details['posted']}})


				num = analysis.find_one({"index":"0"})
				analysis.find_one_and_update({'index':"0"},{"$set":{'questions':str(int(num['questions']) + 1)}})

				return redirect("/")
			else:
				return render_template("addpoll.html",color = getrandomcolor(), error = "You did'nt provide enough choices. Please try again")
		else:
			return render_template("addpoll.html",color = getrandomcolor(), error = "You did'nt provide a Question. Please try again")

	else:
		return render_template("addpoll.html",color = getrandomcolor(), error = "")

@app.route('/<qid>')
@login_required
def question(qid):
	global user_details
	global colors

	analysis = mongo.db.analysis

	num = analysis.find_one({"index":"0"})
	analysis.find_one_and_update({"index":"0"},{"$set":{'hits':str(int(num['hits']) + 1)}})


	db = mongo.db.pollquestions
	dbusers = mongo.db.users
	
	i = db.find_one({'pollid':qid})

	if i != None:	
		if qid in user_details['voted']:
			return render_template("visited.html",data = i,color = getrandomcolor())
		else:
			return render_template("index.html",data = i,color = getrandomcolor())
	else:
		return render_template("noquestions.html", color = getrandomcolor())


@app.route('/next')
@login_required
def next():
	#Err 
	global user_details

	analysis = mongo.db.analysis
	num = analysis.find_one({"index":"0"})
	analysis.find_one_and_update({"index":"0"},{"$set":{'hits':str(int(num['hits']) + 1)}})

	dbques = mongo.db.pollquestions
	maxquestions = len(list(dbques.find())) - 1

	db = mongo.db.users
	if int(user_details['pollid']) <= maxquestions:
		user_details['pollid'] = str(int(user_details['pollid']) + 1)
		db.find_one_and_update({'username':user_details['username']},{'$set':{'pollid':user_details['pollid']}})

	return redirect("/" + user_details['pollid'])


@app.route('/<qid>/<option>', methods = ['GET','POST'])
@login_required
def answerRouting(qid,option):
	global user_details

	dbusers = mongo.db.users
	db = mongo.db.pollquestions

	data = db.find_one({'pollid':qid})
	choices = data['choices']


	if qid in user_details['voted']:
		pass
	else:
		choices[option]['votes'] = str(int(choices[option]['votes']) + 1)
		totalvotes = str(int(data['totalvotes']) + 1)

		db.find_one_and_update({'pollid':qid},{'$set':{'choices':choices,'totalvotes':totalvotes}})

		user_details['voted'].append(qid)
		dbusers.find_one_and_update({'username':user_details['username']},{"$set":{'voted':user_details['voted']}})

	return jsonify(d = totalvotes)


@app.route('/answeredpolls')
def answered():
	global user_details

	dbusers = mongo.db.users
	db = mongo.db.pollquestions

	data = []
	udata = []
	user = dbusers.find_one({'username':user_details['username']})
	

	for i in user['voted']:
		if db.find_one({'pollid':str(i)}) != None:
			poll = db.find_one({'pollid':str(i)})
			data.append(poll)

	return render_template("listingpolls.html", color=getrandomcolor(), data = data, udata = udata, msg = "You haven't taken any Polls yet.")



@app.route('/yourpolls')
def yourpolls():
	global user_details

	dbusers = mongo.db.users
	pending = mongo.db.pending
	db = mongo.db.pollquestions

	data = []
	udata = []

	# return user_details['username']
	user = dbusers.find_one({'username':user_details['username']})
	
	ids = user['posted']

	for i in ids:
		if db.find_one({'pollid':str(i)}) != None:
			poll = db.find_one({'pollid':str(i)})
			data.append(poll)
			ids.remove(i)

	for i in ids:
		if pending.find_one({'pollid':str(i)}) != None:
			poll = pending.find_one({'pollid':str(i)})
			udata.append(poll)

	return render_template("listingpolls.html", color=getrandomcolor(), data = data, udata = udata, msg = "You haven't added any Question yet")

@app.route('/ref/')
def refresh():
	global user_details

	#Refresh pollid to 0 so that all the questions can be visited on clicking the next button
	db = mongo.db.users

	user_details['pollid'] = "0"
	db.find_one_and_update({'username':user_details['username']},{"$set":{'pollid':"0"}})

	return redirect("/0")


@login_manager.user_loader
def load_user(username):
	return User(username)


@app.route("/logout")
@login_required
def logout():
	logout_user()
	global user_details
	user_details = {}
	return redirect("/login")


@app.errorhandler(404)
def page_not_found(e):
	return render_template("pagenotfound.html", color = getrandomcolor()),404


@app.errorhandler(500)
def page_not_found(e):
	return render_template("pagenotfound.html", color = getrandomcolor()),500


if __name__ == "__main__":
	app.run()
