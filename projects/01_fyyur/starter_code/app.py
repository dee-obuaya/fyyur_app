#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#
import sys
import datetime
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_migrate import Migrate
import logging
from logging import Formatter, FileHandler
from forms import ArtistForm, ShowForm, VenueForm
from models import Artist, db, Show, Venue
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
app.config.from_object('config')

db.init_app(app)
moment = Moment(app)

# TODO: connect to a local postgresql database
migrate = Migrate(app, db)


#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
    date = dateutil.parser.parse(value)
    if format == 'full':
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format = "EE MM, dd, y h:mma"
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
    # TODO: replace with real venues data.
    #       num_upcoming_shows should be aggregated based on number of upcoming shows per venue.
    cities = db.session.query(Venue.city, Venue.state).group_by(
        Venue.city, Venue.state).all()

    venues = db.session.query(Venue.id, Venue.city, Venue.name).group_by(Venue.id, Venue.city).all()

    data = [{
        'city': cities[i][0],
        'state': cities[i][1],
        'venues': [{
            'id': venue.id,
            'name': venue.name,
            # 'num_upcoming_shows': venue.upcoming_shows_count
        } for venue in venues if venue.city == cities[i][0]]
    } for i in range(len(cities))]

    return render_template('pages/venues.html', areas=data)


@app.route('/venues/search', methods=['POST'])
def search_venues():
    # TODO: implement search on venues with partial string search. Ensure it is case-insensitive.
    # seach for Hop should return "The Musical Hop".
    # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
    search_query = request.form.get('search_term', '')
    venues_response = Venue.query.filter(Venue.name.ilike(
        f'%{search_query}%') | Venue.name.contains(search_query.title()) | Venue.city.ilike(
        f'%{search_query}%') | Venue.city.contains(search_query.title()) | Venue.state.ilike(
        f'%{search_query}%') | Venue.state.contains(search_query.title()))
    # response = {
    #     "count": 1,
    #     "data": [{
    #         "id": 2,
    #         "name": "The Dueling Pianos Bar",
    #         "num_upcoming_shows": 0,
    #     }]
    # }
    response = {
        "count": venues_response.count(),
        "data": [{
            "id": venue.id,
            "name": venue.name,
            "num_upcoming_shows": venue.upcoming_shows_count
        } for venue in venues_response.all()]
    }
    print(response)
    return render_template('pages/search_venues.html', results=response, search_term=search_query)


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    # shows the venue page with the given venue_id
    # TODO: replace with real venue data from the venues table, using venue_id
    venue = Venue.query.get(venue_id)
    # shows_for_venue = Show.query.filter_by(venue_id=venue_id).all()

    past_shows_query = db.session.query(Show).join(Venue).filter(
        Show.venue_id == venue_id).filter(Show.start_time < str(datetime.datetime.now())).all()
    upcoming_shows_query = db.session.query(Show).join(Venue).filter(
        Show.venue_id == venue_id).filter(Show.start_time > str(datetime.datetime.now())).all()

    upcoming_shows = []
    past_shows = []

    for show in upcoming_shows_query:
        upcoming_show = {
            "artist_id": show.artist_id,
            "artist_name": show.artist.name,
            "artist_image_link": show.artist.image_link,
            "start_time": show.start_time
        }
        upcoming_shows.append(upcoming_show)

    for show in past_shows_query:
        past_show = {
            "artist_id": show.artist_id,
            "artist_name": show.artist.name,
            "artist_image_link": show.artist.image_link,
            "start_time": show.start_time
        }
        past_shows.append(past_show)

    venue = {
        "id": venue.id,
        "name": venue.name,
        "genres": venue.genres,
        "address": venue.address,
        "city": venue.city,
        "state": venue.state,
        "phone": venue.phone,
        "website": venue.website,
        "facebook_link": venue.facebook_link,
        "seeking_talent": venue.seeking_talent,
        "seeking_description": venue.seeking_description,
        "image_link": venue.image_link,
        "past_shows": past_shows,
        "upcoming_shows": upcoming_shows,
        "past_shows_count": len(past_shows),
        "upcoming_shows_count": len(upcoming_shows),
    }

    return render_template('pages/show_venue.html', venue=venue)

#  Create Venue
#  ----------------------------------------------------------------


@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create/submit', methods=['POST'])
def create_venue_submission():
    # TODO: insert form data as a new Venue record in the db, instead
    # TODO: modify data to be the data object returned from db insertion
    form = VenueForm()
    print(form)
    if form.validate_on_submit():
        # genres = form.getlist('genres').data
        genres = request.form.getlist('genres')
        try:
            new_venue = Venue(
                name=form.name.data,
                city=form.city.data,
                state=form.state.data,
                address=form.address.data,
                phone=form.phone.data,
                genres=genres,
                facebook_link=form.facebook_link.data,
                image_link=form.image_link.data,
                website=form.website_link.data,
                seeking_talent=form.seeking_talent.data,
                seeking_description=form.seeking_description.data,
            )
            db.session.add(new_venue)
            db.session.commit()
            # on successful db insert, flash success
            flash(f'Venue {form.name.data} was successfully listed!')
        except:
            db.session.rollback()
            print(sys.exc_info())
            # TODO: on unsuccessful db insert, flash an error instead. e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
            # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
            flash(f'Venue {form.name.data} could not be listed')
        finally:
            db.session.close()
            return redirect(url_for('venues'))

    else:
        for field, message in form.errors.items():
            flash(field + ' - ' + str(message), 'danger')

    return render_template('pages/home.html')


@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
    # TODO: Complete this endpoint for taking a venue_id, and using
    # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.

    venue = Venue.query.get(venue_id)

    try:
        db.session.delete(venue)
        db.session.commit()
        flash(f'{venue.name} successfully deleted.')
    except:
        db.sessio.rollback()
        flash(f'Could not successfully delete {venue.name}. Try again.')
    finally:
        db.session.close()

        return redirect(url_for('index'))

    # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
    # clicking that button delete it from the db then redirect the user to the homepage

#  Artists
#  ----------------------------------------------------------------


@app.route('/artists')
def artists():
    # TODO: replace with real data returned from querying the database
    all_artists = Artist.query.all()

    artists = [{
        'id': artist.id,
        'name': artist.name,
    } for artist in all_artists]

    return render_template('pages/artists.html', artists=artists)


@app.route('/artists/search', methods=['POST'])
def search_artists():
    # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
    # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
    # search for "band" should return "The Wild Sax Band".
    search_query = request.form.get('search_term', '')

    artists_response = Artist.query.filter(
        Artist.name.ilike(f'%{search_query}%') | Artist.name.contains(search_query.title(
        )) | Artist.city.ilike(f'%{search_query}%') | Artist.city.contains(search_query.title()) | Artist.state.ilike(f'%{search_query}%') | Artist.state.contains(search_query.title())
    )

    response = {
        "count": artists_response.count(),
        "data": [{
            "id": artist.id,
            "name": artist.name,
            "num_upcoming_shows": artist.upcoming_shows_count
        } for artist in artists_response.all()]
    }
    return render_template('pages/search_artists.html', results=response, search_term=search_query)


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    # shows the artist page with the given artist_id
    # TODO: replace with real artist data from the artist table, using artist_id
    artist = Artist.query.get(artist_id)
    past_shows_query = Show.query.join(Venue).filter(Show.artist_id == artist_id).filter(
        Show.start_time < str(datetime.datetime.now())).all()

    upcoming_shows_query = Show.query.join(Venue).filter(Show.artist_id == artist_id).filter(
        Show.start_time > str(datetime.datetime.now())).all()

    upcoming_shows = []
    past_shows = []

    for show in upcoming_shows_query:
        upcoming_show = {
            "venue_id": show.venue_id,
            "venue_name": show.venue.name,
            "venue_image_link": show.venue.image_link,
            "start_time": show.start_time
        }
        upcoming_shows.append(upcoming_show)

    for show in past_shows_query:
        past_show = {
            "venue_id": show.venue_id,
            "venue_name": show.venue.name,
            "venue_image_link": show.venue.image_link,
            "start_time": show.start_time
        }
        past_shows.append(past_show)

    artist = {
        "id": artist.id,
        "name": artist.name,
        "genres": artist.genres,
        "city": artist.city,
        "state": artist.state,
        "phone": artist.phone,
        "website": artist.website,
        "facebook_link": artist.facebook_link,
        "seeking_venue": artist.seeking_venue,
        "seeking_description": artist.seeking_description,
        "image_link": artist.image_link,
        "past_shows": past_shows,
        "upcoming_shows": upcoming_shows,
        "past_shows_count": len(past_shows),
        "upcoming_shows_count": len(upcoming_shows),
    }

    return render_template('pages/show_artist.html', artist=artist)

#  Update
#  ----------------------------------------------------------------


@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    # TODO: populate form with fields from artist with ID <artist_id>
    artist = Artist.query.get(artist_id)

    edit_form = ArtistForm(
        name=artist.name,
        city=artist.city,
        state=artist.state,
        phone=artist.phone,
        image_link=artist.image_link,
        genres=artist.genres,
        facebook_link=artist.facebook_link,
        website_link=artist.website,
        seeking_venue=artist.seeking_venue,
        seeking_description=artist.seeking_description
    )
    return render_template('forms/edit_artist.html', form=edit_form, artist=artist)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    # TODO: take values from the form submitted, and update existing
    # artist record with ID <artist_id> using the new attributes

    artist = Artist.query.get(artist_id)
    form = ArtistForm(form.data)

    print(form)

    if form.validate_on_submit():

        try:
            artist.name = form.name.data
            artist.city = form.city.data
            artist.state = form.state.data
            artist.phone = form.phone.data
            artist.image_link = form.image_link.data
            artist.genres = form.getlist('genres').data
            artist.facebook_link = form.facebook_link.data
            artist.website_link = form.website_link.data
            artist.seeking_venue = form.seeking_venue.data
            artist.seeking_description = artist.seeking_description.data

            db.session.commit()
            flash(f'Venue {artist.name} successfully updated!')
        except:
            db.session.rollback()
            flash(f'Venue {artist.name} could not be updated.')
        finally:
            db.session.close()
            return redirect(url_for('artists'))
        
    else:
        for field, message in form.errors.items():
            flash(field + ' - ' + str(message), 'danger')

    return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    # TODO: populate form with values from venue with ID <venue_id>

    venue = Venue.query.get(venue_id)

    edit_form = VenueForm(
        name=venue.name,
        city=venue.city,
        state=venue.state,
        address=venue.address,
        phone=venue.phone,
        image_link=venue.image_link,
        genres=venue.genres,
        facebook_link=venue.facebook_link,
        website_link=venue.website,
        seeking_talent=venue.seeking_talent,
        seeking_description=venue.seeking_description
    )

    return render_template('forms/edit_venue.html', form=edit_form, venue=venue)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    # TODO: take values from the form submitted, and update existing
    # venue record with ID <venue_id> using the new attributes
    venue = Venue.query.get(venue_id)
    form = VenueForm(request.form)

    if form.validate_on_submit():
        try:
            venue.name = form.name.data
            venue.city = form.city.data
            venue.state = form.state.data
            venue.address = form.address.data
            venue.phone = form.phone.data
            venue.image_link = form.image_link.data
            venue.genres = form.getlist('genres').data
            venue.facebook_link = form.facebook_link.data
            venue.website = form.website_link.data
            venue.seeking_talent = form.seeking_talent.data
            venue.seeking_description = form.seeking_description.data

            db.session.commit()
            flash(f'Venue {venue.name} successfully updated!')
        except:
            db.session.rollback()
            flash(f'Venue {venue.name} could not be updated.')
        finally:
            db.session.close()
            return redirect(url_for('venues'))

    return redirect(url_for('show_venue', venue_id=venue.id))

#  Create Artist
#  ----------------------------------------------------------------


@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create/submit', methods=['POST'])
def create_artist_submission():
    # called upon submitting the new artist listing form
    # TODO: insert form data as a new Venue record in the db, instead
    # TODO: modify data to be the data object returned from db insertion
    form = ArtistForm()

    if form.validate_on_submit():
        genres = request.form.getlist('genres')

        try:
            new_artist = Artist(
                name=form.name.data,
                genres=genres,
                city=form.city.data,
                state=form.state.data,
                phone=form.phone.data,
                website=form.website_link.data,
                facebook_link=form.facebook_link.data,
                seeking_venue=form.seeking_venue.data,
                seeking_description=form.seeking_description.data,
                image_link=form.image_link.data,
            )
            db.session.add(new_artist)
            db.session.commit()
            flash(f"Artist {form.name.data} successfully added")
        except:
            db.session.rollback()
            print(sys.exc_info)
            flash(f"Could not successfully add artist {form.name.data}")
        finally:
            db.session.close()
            return redirect(url_for('artists'))

    # on successful db insert, flash success
    # flash('Artist ' + request.form['name'] + ' was successfully listed!')
    # TODO: on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.')
    return render_template('pages/home.html', form=form)


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
    # displays list of shows at /shows
    # TODO: replace with real venues data.
    all_shows = Show.query.all()

    shows = [{
        "venue_id": show.venue_id,
        "venue_name": show.venue.name,
        "artist_id": show.artist_id,
        "artist_name": show.artist.name,
        "artist_image_link": show.artist.image_link,
        "start_time": show.start_time
    } for show in all_shows]

    return render_template('pages/shows.html', shows=shows)


@app.route('/shows/create')
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    # called to create new shows in the db, upon submitting new show listing form
    # TODO: insert form data as a new Show record in the db, instead
    form = ShowForm(request.form)

    if form.validate_on_submit():

        try:
            new_show = Show(
                venue_id=form.venue_id.data,
                artist_id=form.artist_id.data,
                start_time=form.start_time.data
            )

            db.session.add(new_show)
            db.session.commit()
            # on successful db insert, flash success
            flash('Show was successfully listed!')
        except:
            db.session.rollback()
            # TODO: on unsuccessful db insert, flash an error instead.
            # e.g., flash('An error occurred. Show could not be listed.')
            # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
            flash('Show could not be listed. Try again.')
        finally:
            db.session.close()
            return redirect(url_for('shows'))

    return render_template('pages/home.html')


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
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
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
