from app import db

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Show(db.Model):
  __tablename__ = "show"

  id = db.Column(db.Integer, primary_key=True)
  start_time = db.Column(db.DateTime(timezone=False), nullable=False)
  artist_id = db.Column(db.Integer, db.ForeignKey("artist.id"), nullable=False)
  venue_id = db.Column(db.Integer, db.ForeignKey("venue.id"), nullable=False)


class Venue(db.Model):
  __tablename__ = 'venue'

  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String, nullable=False)
  genres = db.Column(db.String(120), nullable=False, default="")
  city = db.Column(db.String(120), nullable=False, default="N/A")
  state = db.Column(db.String(120), nullable=False)
  address = db.Column(db.String(120), nullable=False, default="N/A")
  phone = db.Column(db.String(120), default="N/A")
  image_link = db.Column(db.String(500), nullable=False,
                         default="https://cdn3.iconfinder.com/data/icons/buildings-places/512/Venue-512.png")
  facebook_link = db.Column(db.String(120), default="No Facebook Page")

  #// TODO: implement any missing fields, as a database migration using Flask-Migrate
  website = db.Column(db.String(120), default="No Website")
  seeking_talent = db.Column(db.Boolean, nullable=False, default=False)
  seeking_description = db.Column(db.String(120))
  shows = db.relationship("Show", backref="venue", lazy=True)
  #// TODO: Add UPCOMING SHOWS
  #// TODO: Add Past SHOWS

  def __repr__(self):
      return f"name: {self.name}, id: {self.id}, location: {self.city}, {self.state}, address: {self.address}"


class Artist(db.Model):
  __tablename__ = 'artist'

  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String, nullable=False)
  city = db.Column(db.String(120))
  state = db.Column(db.String(120))
  phone = db.Column(db.String(120), default="N/A")
  genres = db.Column(db.String(120), nullable=False, default="")
  image_link = db.Column(db.String(500), nullable=False,
                         default="https://eitrawmaterials.eu/wp-content/uploads/2016/09/person-icon.png")
  facebook_link = db.Column(db.String(120), default="No Facebook Page")
  #// TODO: implement any missing fields, as a database migration using Flask-Migrate
  website = db.Column(db.String(120), default="No Website")
  seeking_venue = db.Column(db.Boolean, nullable=False, default=False)
  seeking_description = db.Column(db.String(120))
  shows = db.relationship("Show", backref="artist", lazy=True)
  #// TODO: Add UPCOMING SHOWS
  #// TODO: Add Past SHOWS


#// TODO Implement Show and Artist models, and complete all model relationships and properties, as a database migration.
