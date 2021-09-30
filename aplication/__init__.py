from flask import Flask, flash, render_template, url_for, request, session, redirect
from flask_paginate import Pagination, get_page_parameter
import os
from datetime import datetime
import base64
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import and_, or_, not_

app = Flask(__name__)

# -------------------------- app and database configuration-----------------
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['DEBUG'] = False
# app.config['SECRET_KEY'] = 'secret'
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:berzone@localhost/Artwork'
# os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


# --------------------------configuration end----------------------------

class Artwork(db.Model):
    __tablename__='artwork'
    id = db.Column(db.Integer, primary_key = True)
    title = db.Column(db.String(200), nullable=False, default="No title given")
    year = db.Column(db.Integer, nullable=False, default='0')
    category = db.Column(db.String, nullable=False, default="no category given")
    rating = db.Column(db.Integer, nullable=True)
    status = db.Column(db.String, nullable=False)
    info = db.Column(db.Text)
    date = db.Column(db.DateTime, default=datetime.now)
    favourite = db.Column(db.String)
    image = db.Column(db.LargeBinary)
    comments = db.relationship('Comment', back_populates='comment_text')
    tags = db.relationship('Tag', back_populates='hashtag')


class Comment(db.Model):
    __tablename__='comment'
    id = db.Column(db.Integer, primary_key = True)
    comment_highlight = db.Column(db.String, nullable=False, default="No Title")
    comment = db.Column(db.Text, nullable=False, default="No Comment")
    artwork_id = db.Column(db.Integer, db.ForeignKey('artwork.id'))

    comment_text = db.relationship('Artwork', back_populates='comments')


    def __init__(self, comment_highlight, comment, artwork_id):
        self.comment_highlight = comment_highlight
        self.comment = comment
        self.artwork_id = artwork_id


class Tag(db.Model):
    __tablename__='tag'
    id = db.Column(db.Integer, primary_key = True)
    tag = db.Column(db.String(50), nullable=True)
    artwork_id = db.Column(db.Integer, db.ForeignKey('artwork.id'))

    hashtag = db.relationship('Artwork', back_populates='tags')

    def __init__(self, tag, artwork_id):
        self.tag = tag
        self.artwork_id = artwork_id

# Custom filter in jinja_env
def b64encode(data):
    return base64.b64encode(data).decode()
    app.jinja_env.filters['b64encode'] = b64encode

def shorter_title(title):
    if len(title) > 35:
        title = title[:35] + "..."
    else:
        pass
    return title
    app.jinja_env.filters['shorter_title'] = shorter_title


perpage = 25


@app.route('/')
def home():
    app.jinja_env.filters['shorter_title'] = shorter_title
    app.jinja_env.filters['b64encode'] = b64encode

    page = request.args.get('page', 1, type=int)
    favourite_artworks = Artwork.query.order_by(Artwork.date.desc()).all()
    artwork = Artwork.query.order_by(Artwork.date.desc()).paginate(page=page,per_page=perpage)

    total = Artwork.query.count()

    pagination = Pagination(page=page, total=total, record_name='artworks',per_page=perpage)

    return render_template('home.html', artwork=artwork, favourite_artworks=favourite_artworks, pagination=pagination)



@app.route('/add_new_artwork', methods=['GET', 'POST'])
def add_new():
    path = os.path.abspath(os.getcwd())
    full_path = os.path.join(path, "aplication\static\pics", "")

    if request.method == 'POST':
        if request.form.get('star'):
            favourite = "True"
        else:
            favourite = "False"

        if request.form['title']:
            title = request.form['title']
        else:
            title = "Untitled"

        year = int(request.form.get('year'))

        if request.form.get('category'):
            category = request.form.get('category')
        else:
            category = "No category given"


        rating = int(request.form['rating'])
        date = datetime.now()
        status = request.form['status']
        info = request.form.get('info')
        tag = request.form['hdn-tag']



        if request.files['image']:
            image = request.files['image'].read()
        else:
            if request.form.get('category') == "novel":
                image = open (full_path + "novel.png", "rb").read()
            elif request.form.get('category') == "movie":
                image = open (full_path + "movie.png", "rb").read()
            elif request.form.get('category') == "series":
                image = open (full_path + "series.png", "rb").read()
            elif request.form.get('category') == "anime":
                image = open (full_path + "anime.png", "rb").read()
            else:
                image = open (full_path + "no_ctgr.png", "rb").read()

        save_new_artwork = Artwork(title=title, year=year, category=category, rating=rating, status=status, info=info, date=date, image=image, favourite=favourite)
        db.session.add(save_new_artwork)
        db.session.commit()

        last_artwork = Artwork.query.order_by(Artwork.date.desc()).first()
        tag_list = list(tag.split())

        for tag in tag_list:
            if tag != "on":
                save_tag = Tag(tag=tag, artwork_id=last_artwork.id)
                db.session.add(save_tag)
            else:
                pass
        db.session.commit()

        return redirect(url_for('home'))
        return render_template('add.html')
    else:
        return render_template('add.html')


# href="{{url_for('artwork_info', artwork_id=x.id)}}">{{ x.title | shorter_title }}</a>
# artwork_id comes from above. It is in artwork_card.html
@app.route('/artwork/<int:artwork_id>/info')
def artwork_info(artwork_id):
    app.jinja_env.filters['b64encode'] = b64encode

    # artwork
    artwork_row = Artwork.query.filter(Artwork.id == artwork_id).first()

    # tags
    artwork_tags = Tag.query.filter(Tag.artwork_id == artwork_id).all()

    # comments
    artwork_comments = Comment.query.filter(Comment.artwork_id == artwork_id).order_by(Comment.id.desc()).all()

    return render_template('artwork_info.html', artwork_row=artwork_row, artwork_tags=artwork_tags, artwork_comments=artwork_comments)

@app.route('/rated/<int:artwork_rate>')
def rated(artwork_rate):
    app.jinja_env.filters['shorter_title'] = shorter_title
    app.jinja_env.filters['b64encode'] = b64encode
    artwork = Artwork.query.filter(Artwork.rating == artwork_rate).order_by(Artwork.date.desc()).all()
    title = " Artworks with Rating " + str(artwork_rate)
    total = Artwork.query.filter(Artwork.rating == artwork_rate).count()
    return render_template('selected.html', artwork=artwork, title=title, total=total)

@app.route('/year/<int:artwork_year>')
def year(artwork_year):
    app.jinja_env.filters['shorter_title'] = shorter_title
    app.jinja_env.filters['b64encode'] = b64encode
    artwork = Artwork.query.filter(Artwork.year == artwork_year).order_by(Artwork.date.desc()).all()
    title = "Artworks from year " + str(artwork_year)
    total = Artwork.query.filter(Artwork.year == artwork_year).count()
    return render_template('selected.html', artwork=artwork, title=title, total=total)

@app.route('/category/<artwork_category>')
def category(artwork_category):
    app.jinja_env.filters['shorter_title'] = shorter_title
    app.jinja_env.filters['b64encode'] = b64encode
    artwork = Artwork.query.filter(Artwork.category == artwork_category).order_by(Artwork.date.desc()).all()
    title = "Artworks with Category " +"'" + artwork_category + "'"
    total = Artwork.query.filter(Artwork.category == artwork_category).count()
    return render_template('selected.html', artwork=artwork, title=title, total=total)

@app.route('/status/<artwork_status>')
def status(artwork_status):
    app.jinja_env.filters['shorter_title'] = shorter_title
    app.jinja_env.filters['b64encode'] = b64encode
    artwork = Artwork.query.filter(Artwork.status == artwork_status).order_by(Artwork.date.desc()).all()
    title = "Artworks with status " + "'" + artwork_status.upper() + "'"
    total = Artwork.query.filter(Artwork.status == artwork_status).count()
    return render_template('selected.html', artwork=artwork, title=title, total=total)


@app.route('/favourite')
def favourite():
    app.jinja_env.filters['shorter_title'] = shorter_title
    app.jinja_env.filters['b64encode'] = b64encode
    artwork = Artwork.query.filter(Artwork.favourite == 'True').order_by(Artwork.date.desc()).all()
    title = "My Favourites of All Times"
    total = Artwork.query.filter(Artwork.favourite == "True").count()
    return render_template('selected.html', artwork=artwork, title=title, total=total)

@app.route('/rating/8-10')
def rating_high():
    app.jinja_env.filters['shorter_title'] = shorter_title
    app.jinja_env.filters['b64encode'] = b64encode
    artwork = Artwork.query.filter(Artwork.rating > 7).order_by(Artwork.date.desc()).all()
    title = "I have given HIGH grade to these artworks"
    total = Artwork.query.filter(Artwork.rating > 7).count()
    return render_template('selected.html', artwork=artwork, title=title, total=total)

@app.route('/rating/4-7')
def rating_medium():
    app.jinja_env.filters['shorter_title'] = shorter_title
    app.jinja_env.filters['b64encode'] = b64encode
    artwork = Artwork.query.filter(Artwork.rating > 3, Artwork.rating < 8).order_by(Artwork.date.desc()).all()
    title = "I have given MEDIUM grade to these artworks"
    total = Artwork.query.filter(Artwork.rating > 3, Artwork.rating < 8).count()
    return render_template('selected.html', artwork=artwork, title=title, total=total)

@app.route('/rating/0-3')
def rating_low():
    app.jinja_env.filters['shorter_title'] = shorter_title
    app.jinja_env.filters['b64encode'] = b64encode
    artwork = Artwork.query.filter(Artwork.rating < 4).order_by(Artwork.date.desc()).all()
    title = "I have given LOW grade to these artworks"
    total = Artwork.query.filter(Artwork.rating < 4).count()
    return render_template('selected.html', artwork=artwork, title=title, total=total)

@app.route('/tag/<artwork_tag>')
def only_tag(artwork_tag):
    app.jinja_env.filters['shorter_title'] = shorter_title
    app.jinja_env.filters['b64encode'] = b64encode
    list_of_ids = []
    for a in Tag.query.filter(Tag.tag == artwork_tag).all():
        list_of_ids.append(a.artwork_id)

    artwork = Artwork.query.filter(Artwork.id.in_(list_of_ids)).all()
    title = "Artworks which have " + "'" + artwork_tag + "'"
    total = Artwork.query.filter(Artwork.id.in_(list_of_ids)).count()
    return render_template('selected.html', artwork=artwork, title=title, total=total)

@app.route('/add_comment', methods=['GET', 'POST'])
def add_comment():
    comment_highlight = request.form['highlight']
    comment = request.form.get('comment')
    artwork_id = request.form.get('art_id')

    save_comment = Comment(comment_highlight=comment_highlight, comment=comment, artwork_id=artwork_id)
    db.session.add(save_comment)
    db.session.commit()

    return redirect(url_for('artwork_info', artwork_id=artwork_id))

@app.route('/remove_comment/<comment_id>', methods=['GET', 'POST'])
def remove_comment(comment_id):
    artwork_id_object = Comment.query.filter(Comment.id == comment_id).first()
    artwork_id = artwork_id_object.artwork_id
    Comment.query.filter(Comment.id == comment_id).delete()
    db.session.commit()
    return redirect(url_for('artwork_info', artwork_id=artwork_id))

@app.route('/edit/<artwork_id>')
def edit_artwork(artwork_id):
    app.jinja_env.filters['b64encode'] = b64encode
    artwork_edit = Artwork.query.filter(Artwork.id == artwork_id).first()
    return render_template('edit.html', artwork_edit=artwork_edit)

@app.route('/delete/<artwork_id>')
def delete_artwork(artwork_id):
    Artwork.query.filter(Artwork.id == artwork_id).delete()
    db.session.commit()
    return redirect(url_for('home'))
@app.route('/edit_all/<artwork_id>', methods=['GET', 'POST'])
def edit_all(artwork_id):
    app.jinja_env.filters['b64encode'] = b64encode
    path = os.path.abspath(os.getcwd())
    full_path = os.path.join(path, "aplication\static\pics", "")

    if request.method == 'POST':
        if request.form.get('star'):
            favourite = "True"
        else:
            favourite = "False"

        if request.form['title']:
            title = request.form['title']
        else:
            title = "Untitled"

        year = int(request.form.get('year'))

        if request.form.get('category'):
            category = request.form.get('category')
        else:
            category = "No category given"
        rating = int(request.form['rating'])

        status = request.form['status']
        info = request.form.get('info')
        tag = request.form['hdn-tag']

        edit_object = Artwork.query.filter(Artwork.id == artwork_id).first()
        if favourite != edit_object.favourite:
            edit_object.favourite = favourite

        if title != edit_object.title:
            edit_object.title = title

        if year != edit_object.year:
            edit_object.year = year

        if category != edit_object.category:
            edit_object.category = category

        if rating != edit_object.rating:
            edit_object.rating = rating

        if status != edit_object.status:
            edit_object.status = status

        if info != edit_object.info:
            edit_object.info = info

        if tag != edit_object.tags:

            tag_list = list(tag.split())

            for tag in tag_list:
                if tag != "on":
                    save_tag = Tag(tag=tag, artwork_id=edit_object.id)
                    db.session.add(save_tag)
                else:
                    pass
            db.session.commit()
        tags_to_remove = request.form.get('hdn-tag-to-remove')
        if tags_to_remove != 'on' and tags_to_remove != '':
            remove = list(request.form['hdn-tag-to-remove'].split())
            for item in remove:
                db.session.delete(Tag.query.filter(Tag.artwork_id==edit_object.id, Tag.tag == item).first())
            db.session.commit()
        if request.files['image']:
            image = request.files['image'].read()
            edit_object.image = image
        db.session.commit()
        return redirect(url_for('artwork_info', artwork_id=artwork_id))
    return redirect(url_for('home'))


@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/search', methods=['GET','POST'])
def search():
    if request.method == 'POST':
        ttl = request.form.get('titleSearchBar')

        if ttl != '':
            ttl = ttl.capitalize()

        artwork = Artwork.query.filter(Artwork.title==ttl).first()
        if artwork is not None:
            return redirect(url_for('artwork_info', artwork_id=artwork.id))
        else:
            flash(f'Artwork with title "{ttl}" does not exist, try to search again!')
            return redirect(url_for('home'))

    return redirect(url_for('home'))
