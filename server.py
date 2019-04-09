from db import DB
from requests import get, post, delete
from flask import Flask, jsonify, redirect, render_template, request
from news_model import NewsModel
from flask_restful import reqparse, abort, Api, Resource
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField
from wtforms.validators import DataRequired

USERNAME = 'Sign in'
TITLE = None
CONTENT = None


class LoginForm(FlaskForm):
    username = StringField('Login', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Join')


class AddNewsForm(FlaskForm):
    title = StringField('Title Notes', validators=[DataRequired()])
    content = TextAreaField('Content Notes', validators=[DataRequired()])
    submit = SubmitField('Add')


app = Flask(__name__)
api = Api(app)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
db = DB()
NewsModel(db.get_connection()).init_table()

parser = reqparse.RequestParser()
parser.add_argument('title', required=True)
parser.add_argument('content', required=True)
parser.add_argument('user_id', required=True, type=int)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if request.method == 'GET':
        return render_template('login.html', title='Sign in', form=form)
    elif request.method == 'POST':
        global USERNAME
        USERNAME = request.form['username']
        if form.validate_on_submit():
            return redirect('/home')


@app.route('/add_news', methods=['GET', 'POST'])
def add_news():
    form = AddNewsForm()
    if request.method == 'GET':
        return render_template('add_notes.html', title='Add Notes', form=form)
    elif request.method == 'POST':
        global TITLE, CONTENT
        TITLE = request.form['title']
        CONTENT = request.form['content']
        if form.validate_on_submit():
            post('http://localhost:8080/news',
                 json={'title': request.form['title'], 'content': request.form['content'], 'user_id': 1}).json()
            return redirect('/home')


@app.route('/delete_news/<int:news_id>', methods=['GET'])
def delete_news(news_id):
    nm = NewsModel(db.get_connection())
    nm.delete(news_id)
    return redirect("/home")


@app.route('/profile', methods=['GET'])
def profile():
    return render_template('profile.html', title='Profile', name=USERNAME,
                           n=len(get('http://localhost:8080/news').json()['news']))


@app.route('/')
@app.route('/home')
def home():
    return render_template('home.html', title='Home', username=USERNAME,
                           news=get('http://localhost:8080/news').json()['news'])


@app.route('/logout')
def logout():
    if USERNAME == 'Sign in':
        return redirect('/login')
    else:
        return redirect('/profile')


def abort_if_news_not_found(news_id):
    if not NewsModel(db.get_connection()).get(news_id):
        abort(404, message="News {} not found".format(news_id))


class News(Resource):
    def get(self, news_id):
        abort_if_news_not_found(news_id)
        news = NewsModel(db.get_connection()).get(news_id)
        return jsonify({'news': news})

    def delete(self, news_id):
        abort_if_news_not_found(news_id)
        NewsModel(db.get_connection()).delete(news_id)
        return jsonify({'success': 'OK'})


class NewsList(Resource):
    def get(self):
        news = NewsModel(db.get_connection()).get_all()
        return jsonify({'news': news})

    def post(self):
        args = parser.parse_args()
        news = NewsModel(db.get_connection())
        news.insert(args['title'], args['content'], args['user_id'])
        return jsonify({'success': 'OK'})


api.add_resource(NewsList, '/news')
api.add_resource(News, '/news/<int:news_id>')

if __name__ == '__main__':
    app.run(port=8080, host='127.0.0.1', debug=True)
