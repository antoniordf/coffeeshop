#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

from datetime import date
import json
from xmlrpc.client import Boolean
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for, abort
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
import sys
import os
from models import Venue, Artist, Show
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)

migrate = Migrate(app, db)

# TODO: connect to a local postgresql database
# Why connect to the database again here? Ist't that what app.config.from_object is doing above? 
# This is confusing.

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
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  # TODO: DONE: replace with real venues data.
  #       num_upcoming_shows should be aggregated based on number of upcoming shows per venue.

  #The .distinct() method brings all of the distinct values for a particular column.
  #The below line of code will look at the column containing all cities and states of venues and return 
  #a set of the cities and states contained.
  areas = db.session.query(Venue.city, Venue.state).distinct(Venue.city, Venue.state).order_by('state').all()

  data = []

  for area in areas:
    venues = Venue.query.filter_by(state=area.state).filter_by(city=area.city).order_by('name').all()
    venue_data = []
    data.append({
      "city": area.city,
      "state": area.state,
      "venues": venue_data
    })
    for venue in venues:
      shows = Show.query.filter_by(venue_id=venue.id).order_by('id').all()
      venue_data.append({
        "id": venue.id,
        "name": venue.name,
        "num_upcoming_shows": len(shows)
      })

  return render_template('pages/venues.html', areas=data)
  

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # TODO: implement search on venues with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"

  search_term = request.form.get('search_term', '')
  result = Venue.query.filter(Venue.name.ilike(f'%{search_term}%'))

  response = {
    'count': result.count(),
    'data': result
  }
  
  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # DONE: shows the venue page with the given venue_id
  # TODO: DONE: replace with real venue data from the venues table, using venue_id

  venue = Venue.query.get_or_404(venue_id)
  shows = db.session.query(Show, Venue).join(Artist).filter_by(id=venue_id).all()
  
  upcoming_shows = []
  past_shows = []  

  for show, artist in shows:
    tmp_show = {
      'venue_id': artist.id,
      'venue_name': artist.name,
      'venue_image_link': artist.image_link,
      'start_time': show.start_time.strftime("%d/%m/%Y, %H:%M") #See https://knowledge.udacity.com/questions/321974
    }

    if show.start_time <= datetime.now():
      past_shows.append(tmp_show)
    else:
      upcoming_shows.append(tmp_show)

  data = vars(venue)  

  data['past_shows'] = past_shows
  data['upcoming_shows'] = upcoming_shows
  data['past_shows_count'] = len(past_shows)
  data['upcoming_shows_count'] = len(upcoming_shows)
  
  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  
  form = VenueForm(request.form, meta={'csrf': False})

  '''
  With Flask-WTF the below code is not necessary.

  data = request.form
  name = data['name']
  city = data['city']
  state = data['state']
  address = data['address']
  phone = data['phone']
  genres = data.getlist('genres') #getlist used so that multiple genres are added successfully to db 
  facebook_link = data['facebook_link']
  image_link = data['image_link']
  website_link = data['website_link']
  seeking_talent = False
  if seeking_talent in data: #seeking_talent is a box that should be ticked on the browser.
    seeking_talent = True
  seeking_description = data['seeking_description']
  '''

  venue = Venue(
    name=form.name.data, 
    city=form.city.data, 
    state=form.state.data, 
    address=form.address.data, 
    phone=form.phone.data, 
    image_link=form.image_link.data, 
    facebook_link=form.facebook_link.data, 
    website_link=form.website_link.data, 
    genres=form.genres.data,
    seeking_talent=form.seeking_talent.data,
    seeking_description=form.seeking_description.data
  )
  '''
  I could also have done the below, but I opted to left the code explicit so I learn what's happening:

  form = VenueForm(request.form)
  try:
    venue = Venue()
    form.populate_obj(venue)
    db.session.add(venue)

  '''
  try:
    db.session.add(venue)
    db.session.commit()
    flash('Venue ' + form.name.data + ' has been successfully listed.')
  except:
    db.session.rollback()
    print(sys.exc_info())
    flash('An error occured. Venue '+ form.name.data + 'could not be added.')
  finally:
    db.session.close()
  
  return render_template('pages/home.html')

  # TODO: DONE:insert form data as a new Venue record in the db, instead
  # TODO: NOT SURE WHAT TO DO HERE: modify data to be the data object returned from db insertion
  # DONE: on successful db insert, flash success
  # TODO: DONE: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
  

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  
  try:
    Venue.query.filter_by(id=venue_id).delete()
    db.session.commit()
    flash(Venue.name + 'has been deleted')
  except:
    db.session.rollback()
    flash(Venue.name + 'could not be deleted')
  finally:
    db.session.close()
    
  return redirect(url_for('index'))


  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.

  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # TODO: DONE: replace with real data returned from querying the database

  data = []

  artists = Artist.query.order_by(Artist.id).all()

  for artist in artists:
    data.extend([{
      "id": artist.id,
      "name": artist.name
  }])

  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # TODO: DONE: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".

  search_term = request.form.get('search_term', '')
  result = Artist.query.filter(Artist.name.ilike(f'%{search_term}%'))

  response = {
    'count': result.count(),
    'data': result
  }

  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # DONE: shows the artist page with the given artist_id
  # TODO: replace with real artist data from the artist table, using artist_id

  artist = Artist.query.get_or_404(artist_id)
  shows = db.session.query(Show, Venue).join(Artist).filter_by(id=artist_id).all()
  
  upcoming_shows = []
  past_shows = []  

  for show, venue in shows:
    tmp_show = {
      'venue_id': venue.id,
      'venue_name': venue.name,
      'venue_image_link': venue.image_link,
      'start_time': show.start_time.strftime("%d/%m/%Y, %H:%M") #See https://knowledge.udacity.com/questions/321974
    }

    if show.start_time <= datetime.now():
      past_shows.append(tmp_show)
    else:
      upcoming_shows.append(tmp_show)

  '''
  The vars() function returns the __dict__ attribute of an object. Basically it converts 
  the attributes of an object into a dictionary. See https://www.w3schools.com/python/ref_func_vars.asp
  In this case vars(artist) is equivalent to:
  data {
    'name':artist.name,
    'city':artist.city,
    ...
  }
  '''
  data = vars(artist)  

  data['past_shows'] = past_shows
  data['upcoming_shows'] = upcoming_shows
  data['past_shows_count'] = len(past_shows)
  data['upcoming_shows_count'] = len(upcoming_shows)
  
  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  artist = Artist.query.filter_by(id=artist_id).first_or_404()

  data = {
    "id": artist.id, 
    "name": artist.name, 
    "genres": artist.genres, 
    "city": artist.city, 
    "state": artist.state,
    "phone": artist.phone, 
    "website_link": artist.website_link, 
    "facebook_link": artist.facebook_link, 
    "seeking_venue": artist.seeking_venue, 
    "seeking_description": artist.seeking_description, 
    "image_link": artist.image_link 
  }
  return render_template('forms/edit_artist.html', form=form, artist=data)

  # TODO: DONE: populate form with fields from artist with ID <artist_id>

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):

  artist = Artist.query.filter_by(id=artist_id).first_or_404()
  form = ArtistForm(request.form, meta={'csrf': False})

  if form.validate(): #.validate() checks if form was filled correctly. If not, field highlights red and wont submit.

    artist.name = form.name.data
    artist.city = form.city.data
    artist.state = form.state.data
    artist.phone = form.phone.data
    artist.genres = form.genres.data
    artist.facebook_link = form.facebook_link.data
    artist.image_link = form.image_link.data
    artist.website_link = form.website_link.data
    artist.seeking_venue = form.seeking_venue.data
    artist.seeking_description = form.seeking_description.data

    try:
      db.session.commit()
      flash('The Artist ' + form.name.data + ' has been successfully updated!')
    except Exception as e:
      print(e)
      print(sys.exc_info())
      db.session.rollback()
      flash('Error! Artist could not be updated.')
    finally:
      db.session.close()

  else:
    message = []
    for field, errors in form.errors.items():
      message.append(str(form[field].label) + ', '.join(errors))
      flash('Errors: ' + '|'.join(message))

  return redirect(url_for('show_artist', artist_id=artist_id))

  # TODO: DONE: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes

  

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  venue = Venue.query.filter_by(id=venue_id).first_or_404()

  data = {
    "id": venue.id, 
    "name": venue.name, 
    "genres": venue.genres, 
    "city": venue.city, 
    "state": venue.state,
    "phone": venue.phone,
    "address": venue.address, 
    "website_link": venue.website_link, 
    "facebook_link": venue.facebook_link, 
    "seeking_talent": venue.seeking_talent, 
    "seeking_description": venue.seeking_description, 
    "image_link": venue.image_link
    }

  return render_template('forms/edit_venue.html', form=form, venue=data)

  # TODO: DONE: populate form with values from venue with ID <venue_id>

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):

  venue = Venue.query.filter_by(id=venue_id).first_or_404()
  form = VenueForm(request.form, meta={'csrf': False})

  if form.validate(): #.validate() checks if form was filled correctly. If not, field highlights red and wont submit.

    venue.name = form.name.data
    venue.city = form.city.data
    venue.state = form.state.data
    venue.address = form.address.data
    venue.phone = form.phone.data
    venue.genres = form.genres.data
    venue.facebook_link = form.facebook_link.data
    venue.image_link = form.image_link.data
    venue.website_link = form.website_link.data
    venue.seeking_talent = form.seeking_talent.data
    venue.seeking_description = form.seeking_description.data

    try:
      db.session.commit()
      flash('The Venue ' + form.name.data + ' has been successfully updated!')
    except Exception as e:
      print(e)
      print(sys.exc_info())
      db.session.rollback()
      flash('Error! Venue could not be updated.')
    finally:
      db.session.close()

  else:
    message = []
    for field, errors in form.errors.items():
      message.append(str(form[field].label) + ', '.join(errors))
      flash('Errors: ' + '|'.join(message))

  return redirect(url_for('show_venue', venue_id=venue_id))


  # TODO: DONE: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():

  form = ArtistForm(request.form, meta={'csrf': False})

  artist = Artist(
    name=form.name.data, 
    city=form.city.data, 
    state=form.state.data,  
    phone=form.phone.data, 
    image_link=form.image_link.data, 
    facebook_link=form.facebook_link.data, 
    website_link=form.website_link.data, 
    genres=form.genres.data,
    seeking_venue=form.seeking_venue.data,
    seeking_description=form.seeking_description.data
  )
  
  try:
    db.session.add(artist)
    db.session.commit()
    flash('Artist ' + form.name.data + ' has been successfully listed.')
  except:
    db.session.rollback()
    print(sys.exc_info())
    flash('An error occured. Artist '+ form.name.data + 'could not be added.')
  finally:
    db.session.close()
  
  return render_template('pages/home.html')

  # called upon submitting the new artist listing form
  # TODO: DONE: insert form data as a new Venue record in the db, instead
  # TODO: DONE: modify data to be the data object returned from db insertion
  # DONE: on successful db insert, flash success
  # TODO: DONE: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():

  data = []

  shows = Show.query.order_by(Show.start_time.desc()).all()

  for show in shows:
    data.extend([{
      'venue_id': show.venue.id,
      'venue_name': show.venue.name,
      'artist_id': show.artist.id,
      'artist_name': show.artist.name,
      'artist_image_link': show.artist.image_link,
      'start_time': show.start_time.strftime("%m/%d/%Y, %H:%M")
    }])

  return render_template('pages/shows.html', shows=data)

  # DONE: displays list of shows at /shows
  # TODO: replace with real venues data.

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():

  form = ShowForm(request.form, meta={'csrf': False})

  show = Show(
    artist_id=form.artist_id.data, 
    venue_id=form.venue_id.data, 
    start_time=form.start_time.data
  )
  
  try:
    db.session.add(show)
    db.session.commit()
    flash('Show has been successfully listed.')
  except:
    db.session.rollback()
    print(sys.exc_info())
    flash('An error occurred. Show could not be added.')
  finally:
    db.session.close()
  
  return render_template('pages/home.html')

  # DONE: called to create new shows in the db, upon submitting new show listing form
  # TODO: DONE: insert form data as a new Show record in the db, instead
  # DONE: on successful db insert, flash success
  # TODO: DONE: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Show could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/

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

# Default port:

if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=3000) #Changed port to 3000 due to this issue: https://medium.com/pythonistas/port-5000-already-in-use-macos-monterey-issue-d86b02edd36c

'''
# Or specify port manually:
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
