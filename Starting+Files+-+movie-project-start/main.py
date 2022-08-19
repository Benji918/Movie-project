from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import requests

MOVIE_IMAGE_URl = 'https://image.tmdb.org/t/p/w500/'
app = Flask(__name__)
app.secret_key = '8BYkEfBA6O6donzWlSihBXox7Cffhjhhb'
Bootstrap(app)

# create db
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///movie.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


# create edit form
class Editform(FlaskForm):
    rating = StringField(label='Your Rating out of 10 e.g 8.4', validators=[DataRequired('Please enter a value!')],
                         render_kw={"autofocus": True})
    review = StringField(label='Your review', validators=[DataRequired('Please enter a value!')])
    submit = SubmitField(label='Submit')


class Addform(FlaskForm):
    title = StringField(label='Movie title', validators=[DataRequired('Please enter a title!')])
    submit = SubmitField(label='Submit')


class Movie_db(db.Model):
    # create the db fields(columns)
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(1000), nullable=False)
    rating = db.Column(db.Float, nullable=True)
    ranking = db.Column(db.Integer, nullable=True)
    review = db.Column(db.String(1000), nullable=True)
    img_url = db.Column(db.Text, nullable=False)


db.create_all()


@app.route("/")
def home():
    # this gets the movies from lowest rating to highest
    movie_data = Movie_db.query.order_by(Movie_db.rating).all()
    # this reverses at order
    movie_data.reverse()
    # get the index of each individual item
    for (index, movie) in enumerate(movie_data):
        movie.ranking = index + 1
        db.session.commit()
    return render_template("index.html", movie_data=movie_data)


@app.route("/edit/<int:id>", methods=['GET', 'POST'])
def edit(id):
    form = Editform(meta={'csrf': True})
    movie_id = id
    movie = Movie_db.query.get(movie_id)
    if request.method == 'POST':
        if form.validate_on_submit():
            movie.rating = float(form.rating.data)
            movie.review = form.review.data
            db.session.commit()
            return redirect(url_for('home'))
    return render_template("edit.html", movie=movie, movie_id=id, form=form)


@app.route('/delete/<int:id>')
def delete(id):
    movie_id = id
    # get the specific movie by  id
    movie = Movie_db.query.get(movie_id)
    # then delete it
    db.session.delete(movie)
    # save changes in the db
    db.session.commit()
    return redirect(url_for('home'))


@app.route('/add', methods=['GET', 'POST'])
def add():
    add_form = Addform(meta={'csrf': True})
    if request.method == 'POST':
        if add_form.validate_on_submit():
            API_KEY = '79fb80aa1e2c705e1e7296d1bccdd174'
            header = {
                'Authorization': f'Bearer{API_KEY}',
                'Content-Type': 'application/json;charset=utf-8'
            }
            url = 'https://api.themoviedb.org/3/search/movie'
            api_params = {
                'api_key': API_KEY,
                'query': add_form.title.data,
                "language": "en-US"
            }
            response = requests.get(url=url, params=api_params, headers=header)
            data = response.json()['results']
            return render_template('select.html', data=data)
    return render_template('add.html', form=add_form)


@app.route('/find/<int:id>')
def find(id):
    movie_id = id
    API_KEY = '79fb80aa1e2c705e1e7296d1bccdd174'
    header = {
        'Authorization': f'Bearer{API_KEY}',
        'Content-Type': 'application/json;charset=utf-8'
    }
    url = f'https://api.themoviedb.org/3/movie/{movie_id}'
    api_params = {
        'api_key': API_KEY,
        'movie_id': movie_id,
        "language": "en-US"
    }
    response = requests.get(url=url, params=api_params, headers=header)
    data = response.json()
    # input records
    new_movie = Movie_db(
        title=data['title'],
        year=data['release_date'],
        description=data['overview'],
        rating=data['vote_average'],
        review=data['tagline'],
        img_url=f'{MOVIE_IMAGE_URl}{data["poster_path"]}',
    )
    # add them to the db
    db.session.add(new_movie)
    # save them
    db.session.commit()
    print('Saved')
    return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(debug=True)
