from flask import Flask , render_template,  flash, redirect, url_for, session, request, logging
from data import Articles
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps
app = Flask(__name__)

#config MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'THEGREAT'
app.config['MYSQL_DB'] = 'myflaskapp'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
#init MYSQL
mysql = MySQL(app)

Articles = Articles()


#check if user logout in
def is_logged_in(f):
	@wraps(f)
	def wrap(*args, **kwargs):
		if 'logged_in' in session:
			return f(*args, **kwargs)
		else:
			flash('Unauthorised, Please login', 'danger')
			return redirect(url_for('login'))
	return wrap


@app.route('/')
def index():
	return render_template('home.html')

@app.route('/home')
def home():
	return render_template('home.html')

@app.route('/about')
def about():
	return render_template('about.html')

@app.route('/articles')
def articles():
	return render_template('articles.html', articles = Articles)

		#create cursor
	cur = mysql.connection.cursor()

	#get articles
	result = cur.execute("SELECT * FROM articles")

	articles1 = cur.fetchall()

	if result > 0:
		return render_template('articles.html', articles1=articles1)
	else:
		msg = 'No Articles Found'
		return render_template('articles.html', msg=msg)

	#close connection
	cur.close()


@app.route('/article/<string:id>/')
def article(id):
	cur = mysql.connection.cursor()

	#get articles
	result = cur.execute("SELECT * FROM articles1 WHERE id = %s", [id])

	article = cur.fetchone()

	return render_template('article.html', article=article)



class RegisterForm(Form):
	name = StringField('Name', [validators.Length(min=1, max=50)])
	username = StringField('Username', [validators.Length(min=4, max=25)])
	email = StringField('Email', [validators.Length(min=6, max=50)])
	password = PasswordField('Password', [
		validators.DataRequired(),
		validators.EqualTo('confirm', message='Passwords do not match')
		])
	confirm = PasswordField('Confirm Password')


@app.route('/register', methods=['GET', 'POST'])
def register():
	form = RegisterForm(request.form)
	if request.method == 'POST' and form.validate():
		name = form.name.data
		email = form.email.data
		username = form.username.data
		password = sha256_crypt.encrypt(str(form.password.data))

		#create cursor
		cur = mysql.connection.cursor()

		cur.execute("INSERT INTO users(name, email, username, password) VALUES(%s, %s, %s, %s)", (name, email, username, password))

		#commit to db
		mysql.connection.commit()

		#close connection
		cur.close()

		flash('You are now registered', 'Success')

		return redirect(url_for('login'))
        return render_template('register.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
	if request.method == 'POST':

		#GET FORM
		username = request.form['username']
		password_candidate = request.form['password']

		#create cursor 
		cur = mysql.connection.cursor()

		# get user by username
		result = cur.execute("SELECT * FROM users WHERE username = %s", [username])

		if result > 0:

			data = cur.fetchone()
			password = data['password']

			if sha256_crypt.verify(password_candidate, password):
			   #passed
			   session['logged_in'] = True
			   session['username'] = username

			   flash('You are now logged in','success')
			   return redirect(url_for('dashboard'))

			else:
				error = 'Invalid login'
	    	return render_template('login.html', error=error)
            #close conection
                cur.close()

	       # else:
                error = 'Username not found'
	    	return render_template('login.html', error=error)

        return render_template('login.html')


@app.route('/logout')
def logout():
	session.clear()
	flash('You are now logged out', 'success')
	return redirect(url_for('login'))
	

@app.route('/dashboard')
@is_logged_in
def dashboard():
	#create cursor
	cur = mysql.connection.cursor()

	#get articles
	result = cur.execute("SELECT * FROM articles1")

	articles1 = cur.fetchall()

	if result > 0:
			return render_template('dashboard.html', articles1=articles1)
	else:
		msg = 'No Articles Found'
		return render_template('dashboard.html', msg=msg)

	#close connection
	cur.close()

 	return render_template('dashboard.html')

#Add Article
class ArticleForm(Form):
	title = StringField('Title', [validators.Length(min=1, max=200)])
	body = TextAreaField('Body', [validators.Length(min=30)])

#Add Article
@app.route('/add_article', methods=['GET', 'POST'])
@is_logged_in
def add_article():
	form = ArticleForm(request.form)
	if request.method == 'POST' and form.validate():
		title = form.title.data
		body = form.body.data
		#Create Cursor
		cur = mysql.connection.cursor()
		#execute
		cur.execute("INSERT INTO articles1(title, body, author) VALUES(%s, %s, %s)", (title, body, session['username']))
		#Commit to Db
		mysql.connection.commit()

		#Close connection
		#cursor.close()

		flash('Article Update', 'success')

		return redirect(url_for('dashboard'))
	return render_template('edit_article.html', form=form)


#EditArticle
@app.route('/edit_article/<string:id>', methods=['GET', 'POST'])
@is_logged_in
def edit_article(id):
	#create cursor
	cur = mysql.connection.cursor()
	#get article by id
	result = cur.execute("SELECT * FROM articles1 WHERE id = %s", [id])

	article = cur.fetchone()

	#get form
	form = ArticleForm(request.form)

	#populate articles from fields
	form.title.data = article['title']
	form.body.data = article['body']

	#form = ArticleForm(request.form)
	if request.method == 'POST' and form.validate():
		title = request.form['title']
		body =  request.form['body']

		#Create Cursor
		cur = mysql.connection.cursor()
		#execute
		cur.execute("UPDATE articles1 SET title=%s, body=%s WHERE id = %s", (title, body, id))
		#Commit to Db
		mysql.connection.commit()

		#Close connection
		#cursor.close()

		flash('Article Edited', 'success')

		return redirect(url_for('dashboard'))
	return render_template('edit_article.html', form=form)

@app.route('/delete_article/<string:id>', methods=['POST'])
@is_logged_in
def delete_article(id):


	#create cursor
    cur = mysql.connection.cursor()

	#execute
    cur.execute("DELETE FROM articles1  WHERE id = %s", [id]) 

	#Commit to Db
    mysql.connection.commit()

	#Close connection
	#cursor.close()

    flash('Article Deleted', 'success')

    return redirect(url_for('dashboard'))
    


if __name__ == '__main__':
	app.secret_key='secret123'
	app.run(debug=True)
