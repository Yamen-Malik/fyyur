#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask.helpers import make_response
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from jinja2 import defaults
from sqlalchemy.orm import query
from forms import *
import sys
from datetime import datetime
from models import *
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)


#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime


#----------------------------------------------------------------------------#
# 
#----------------------------------------------------------------------------#
def get_shows_data(shows):
  '''Sorts shows data in a dictionary object

    Keyword arguments:
      shows -- List of Show objects
    Return: Tuple with two dictionaries where the first one is past shows data and the second is upcoming shows data
  '''
  upcoming_shows = []
  past_shows = []
  for show in shows:
    show_data = {
    "artist_id": show.artist_id,
    "artist_name": show.artist.name,
    "artist_image_link": show.artist.image_link,
    "venue_id": show.venue.id,
    "venue_name": show.venue.name,
    "venue_image_link": show.venue.image_link,
    "start_time": str(show.start_time)
    }

    if (show.start_time - datetime.now()).days >= 0:
      upcoming_shows.append(show_data)
    else:
      past_shows.append(show_data)
  
  return (past_shows, upcoming_shows)


def get_detailed_shows_count(shows):
  '''
    Keyword arguments:
    shows -- list of Show objects
    Returns: Tuple with two integer numbers where the first one is past shows count and the second is upcoming shows count
  '''
  past_shows_count = 0
  for show in shows:
    if (show.start_time - datetime.now()).days < 0:
      past_shows_count += 1
  return (past_shows_count, len(shows) - past_shows_count)


def get_past_shows_count(shows):
  '''
    Keyword arguments:
      shows -- list of Show objects
    Returns: The number of past shows in the given list
  '''
  return get_detailed_shows_count(shows)[0]


def get_upcoming_shows_count(shows):
  '''
    Keyword arguments:
      shows -- list of Show objects
    Returns: The number of upcoming shows in the given list
  '''
  return get_detailed_shows_count(shows)[1]

def get_object_data(obj):
  '''Sorts Artist/Venue data in a dictionary object

    Keyword arguments:
      obj -- Artist/Venue object
    Return: tuple with two dictionaries where the first one is past shows data and the second is upcoming shows data
  '''
  data = obj.__dict__.copy()
  del data["_sa_instance_state"]
  if "genres" in data:
    data["genres"] = obj.genres.split(" ")
  
  if obj.shows:
    if isinstance(obj, Artist):
      table_to_join = "venue"
      result = db.session.query(Show, Venue).join(Venue).filter(Show.artist_id == obj.id)
    else:
      table_to_join = "artist"
      result = db.session.query(Show, Artist).join(Artist).filter(Show.venue_id == obj.id)

    past_shows = result.filter(Show.start_time < datetime.now()).all()
    upcoming_shows = result.filter(Show.start_time > datetime.now()).all()
    past_shows_data = []
    upcoming_shows_data = []
    for show, venue in past_shows:
      past_shows_data.append({
          table_to_join + "_id": venue.id,
          table_to_join + "_name": venue.name,
          table_to_join + "_image_link": venue.image_link,
          "start_time": str(show.start_time)
      })
    for show, venue in upcoming_shows:
      upcoming_shows_data.append({
          table_to_join + "_id": venue.id,
          table_to_join + "_name": venue.name,
          table_to_join + "_image_link": venue.image_link,
          "start_time": str(show.start_time)
      })
    
    data["past_shows"] = past_shows_data
    data["upcoming_shows"] = upcoming_shows_data
    data["past_shows_count"] = len(past_shows_data)
    data["upcoming_shows_count"] = len(upcoming_shows_data)
  
  return data

def set_object_attributes_from_dict(obj, dict):
  '''Sets Artist/Venue or Show attributes from a dictionary containing the attributes and thier values

    Keyword arguments:
      obj -- Artist/Venue object
      dict -- Dictionary of attribute -> value
    Return: None
  '''
  for attribute, value in dict.items():
    value = value.strip()
    if value == "":
      continue
    elif value == "y":
      value = True
    if attribute == "website_link":
      attribute = "website"
    setattr(obj, attribute, value)
#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  artists = []
  venues = []
  for artist in Artist.query.order_by(Artist.id.desc()).limit(10).all():
    artists.append(get_object_data(artist))
  for venue in Venue.query.order_by(Venue.id.desc()).limit(10).all():
    venues.append(get_object_data(venue))
  return render_template('pages/home.html', artists=artists, venues=venues)


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  data = []
  query = db.session.query(Venue.city, Venue.state).distinct().all()
  for city, state in query:
    dic = {}
    dic["city"], dic["state"] = city, state
    venues = Venue.query.filter_by(city = city, state = state).all()
    dic["venues"] = []
    for venue in venues:
      dic["venues"].append({"id": venue.id, "name": venue.name, "num_upcoming_shows": get_upcoming_shows_count(venue.shows)})
    data.append(dic)
  return render_template('pages/venues.html', areas=data);

@app.route('/venues/search', methods=['POST'])
def search_venues():
  search_term = request.form['search_term'].strip()
  response = {}
  venues = Venue.query.filter(Venue.name.ilike(f"%{search_term}%")).all()
  if not venues:
    if "," in search_term:
      city, state = search_term.split(",")
      venues = Venue.query.filter(Venue.city.ilike(
          f"%{city.strip()}%"), Venue.state.ilike(f"%{state.strip()}%")).all()
    else:
      venues = Venue.query.filter(Venue.city.ilike(f"%{search_term}%")).all()
      if not venues:
        venues = Venue.query.filter(Venue.state.ilike(f"%{search_term}%")).all()

  response["count"] = len(venues)
  response["data"] = []
  for venue in venues:
    response["data"].append({
      "id": venue.id,
      "name": venue.name,
      "num_upcoming_shows": get_upcoming_shows_count(venue.shows)
    })
  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  venue = Venue.query.filter_by(id = venue_id).first()
  if (not venue):
    return not_found_error("Venue not found")
  data = get_object_data(venue)
  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  error_message = None
  try:
    data = request.form
    if Venue.query.filter_by(name = data["name"]).first():
      error_message = f"Venue \"{data['name']}\" already exists"
      raise Exception(error_message)
    elif data["name"].strip() == "":
      error_message = "nonsensical venue name"
      raise Exception(error_message)

    venue = Venue()
    set_object_attributes_from_dict(venue, data)
   
    db.session.add(venue)
    db.session.commit()
    flash(f"Venue \"{data['name']}\" was successfully listed!")
  except:
    db.session.rollback()
    print(sys.exc_info())
    flash(error_message if error_message else f"An error occurred. Venue \"{data['name']}\" could not be listed.")
  finally:
    db.session.close()

  return redirect("/")

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  venue = Venue.query.filter_by(id = venue_id).first()
  error_message = None
  error_code = None
  try:
    if not venue:
      error_code = 404
      error_message = "Venue not found"
      raise Exception(error_message)

    session = db.session.object_session(venue)
    session.delete(venue)
    session.commit()
    flash(f"Venue with id:{venue_id} was successfully deleted!")
  except:
    db.session.rollback()
    flash(error_message if error_message else f"An error occurred. Venue with id:{venue_id} could not be deleted.")
  finally:
    db.session.close()
  
  return make_response(error_message if error_message else "ok")

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  data = []
  for id, name in Artist.query.with_entities(Artist.id, Artist.name).all():
    data.append({"id": id, "name": name})
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  search_term = request.form['search_term'].strip()
  response = {}
  artists = Artist.query.filter(Artist.name.ilike(f"%{search_term}%")).all()
  if not artists:
    if "," in search_term:
      city, state = search_term.split(",")
      artists = Artist.query.filter(Artist.city.ilike(
          f"%{city.strip()}%"), Artist.state.ilike(f"%{state.strip()}%")).all()
    else:
      artists = Artist.query.filter(Artist.city.ilike(f"%{search_term}%")).all()
      if not artists:
        artists = Artist.query.filter(Artist.state.ilike(f"%{search_term}%")).all()
  response["count"] = len(artists)
  response["data"] = []
  for artist in artists:
    response["data"].append({
        "id": artist.id,
        "name": artist.name,
        "num_upcoming_shows": get_upcoming_shows_count(artist.shows)
    })
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  artist = Artist.query.filter_by(id=artist_id).first()
  if (not artist):
    return not_found_error("Artist Not found")
 
  data = get_object_data(artist)
  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  artist = Artist.query.filter_by(id = artist_id).first()
  if not artist:
    return not_found_error("Artist not found")
  
  artist = get_object_data(artist)
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  error_message = None
  try:
    data = request.form
    artist = Artist.query.filter_by(id = artist_id).first()
    if (not artist):
      error_message = "Artist not found"
      raise Exception(error_message)

    set_object_attributes_from_dict(artist, data)
    db.session.commit()
    flash(f"Artis \"{data['name']}\" was successfully edited!")
  except:
    flash(error_message if error_message else f"An error occurred. Artist with id:{artist_id} could not be edited.")
  finally:
    db.session.close()

  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  venue = Venue.query.filter_by(id = venue_id).first()
  if not venue:
    return not_found_error("Venue not found")
  
  venue = get_object_data(venue)
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  error_message = None
  try:
    data = request.form
    venue = Venue.query.filter_by(id=venue_id).first()
    if (not venue):
      error_message = "Venue not found"
      raise Exception(error_message)

    set_object_attributes_from_dict(venue, data)
    db.session.commit()
    flash(f"Venue \"{data['name']}\" was successfully edited!")
  except:
    flash(error_message if error_message else f"An error occurred. Venue with id:{venue_id} could not be edited.")
  finally:
    db.session.close()

  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  error_message = None
  try:
    data = request.form
    if Artist.query.filter_by(name = data["name"]).first():
      error_message = f"Artist \"{data['name']}\" already exists"
      raise Exception(error_message)
    elif data["name"].strip() == "":
      error_message = "nonsensical artist name"
      raise Exception(error_message)

    artist = Artist()
    set_object_attributes_from_dict(artist, data)
    db.session.add(artist)
    db.session.commit()
    flash(f"Artist \"{request.form['name']}\" was successfully listed!")
  except:
    db.session.rollback()
    print(sys.exc_info())
    flash(error_message if error_message else f"An error occurred. Artist \"{data['name']}\" could not be listed.")
  finally:
    db.session.close()

  return redirect("/")


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  data = get_shows_data(Show.query.all())
  data = data[0] + data[1]
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  error_message = None
  try:
    data = request.form
    if Show.query.filter_by(artist_id = data["artist_id"], start_time = data["start_time"]).first():
      error_message = "Show already exists"
      raise Exception(error_message)
    elif not Artist.query.filter_by(id = data["artist_id"]).first():
      error_message = "Artist doesn't exists"
      raise Exception(error_message)
    elif not Venue.query.filter_by(id = data["venue_id"]).first():
      error_message = "Venue doesn't exists"
      raise Exception(error_message)
    
    show = Show()
    set_object_attributes_from_dict(show, data)
    db.session.add(show)
    db.session.commit()
    flash('Show was successfully listed!')
  except:
    db.session.rollback()
    print(sys.exc_info())
    flash(error_message if error_message else "An error occurred. Show could not be listed.")
  finally:
    db.session.close()
  
  return redirect("/")

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

if __name__ == '__main__':
    app.run()
