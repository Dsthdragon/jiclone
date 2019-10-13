from datetime import datetime

import base64
import os

import jwt

from jiClone import db, ma

from werkzeug.security import generate_password_hash, check_password_hash

from sqlalchemy_utils import EncryptedType
from sqlalchemy_utils.types.encrypted.encrypted_type import AesEngine

from sqlalchemy import event
from sqlalchemy.ext.hybrid import hybrid_property

from marshmallow import fields

from PIL import Image
from io import BytesIO

from config import Config


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    created = db.Column(db.DateTime, default=datetime.utcnow)
    client = db.relationship("Client", backref=db.backref("user", lazy=True),  uselist=False)
    admin = db.relationship("Admin", backref=db.backref("user", lazy=True),  uselist=False)

    def generate_token(self):
        return jwt.encode(
            {
                'id': self.id
            },
            Config.SECRET_KEY,
            algorithm='HS256'
        ).decode()

    @staticmethod
    def decode_token(token):
        try:
            payload = jwt.decode(token, Config.SECRET_KEY)
            return payload['id']
        except jwt.ExpiredSignatureError:
            return 'Signature expired. Please log in again.'
        except jwt.InvalidTokenError:
            return 'Invalid token. Please log in again.'


class UserSchema(ma.TableSchema):
    class Meta:
        table = User.__table__


class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(EncryptedType(db.String, Config.SECRET_KEY, AesEngine, 'pkcs5'), nullable=False)
    phone = db.Column(EncryptedType(db.String, Config.SECRET_KEY, AesEngine, 'pkcs5'), nullable=True)
    first_name = db.Column(EncryptedType(db.String, Config.SECRET_KEY, AesEngine, 'pkcs5'), nullable=False)
    last_name = db.Column(EncryptedType(db.String, Config.SECRET_KEY, AesEngine, 'pkcs5'))
    password_hash = db.Column(db.String(255), nullable=False)
    avatar = db.Column(EncryptedType(db.String, Config.SECRET_KEY, AesEngine, 'pkcs5'))
    created = db.Column(db.DateTime, default=datetime.utcnow)
    updated = db.Column(db.DateTime, onupdate=datetime.utcnow)

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))

    ads = db.relationship(
        "Ad", cascade="all,delete", backref=db.backref("client", lazy=True), lazy=True
    )

    reviews = db.relationship(
        "Review", cascade="all,delete", backref=db.backref("client", lazy=True), lazy=True
    )

    favourites = db.relationship(
        "Favourite", cascade="all,delete", backref=db.backref("client", lazy=True), lazy=True
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def save_image(self, filename, image64):
        path = os.path.join(Config.UPLOAD_FOLDER, filename)
        new_height = 200
        new_width = 200
        img = Image.open(BytesIO(base64.b64decode(image64)))
        width, height = img.size

        height_ratio = height/new_height
        width_ratio = width/new_width

        optimal_ratio = width_ratio
        if height_ratio < width_ratio:
            optimal_ratio = height_ratio

        optimal_size = (int(width / optimal_ratio), int(height / optimal_ratio))
        img = img.resize(optimal_size)

        width, height = img.size

        left = (width - new_width) / 2
        top = (height - new_height) / 2
        right = (width + new_width) / 2
        bottom = (height + new_height) / 2

        img = img.crop((left, top, right, bottom))
        img.save(path)

        self.set_new_image(filename)

    def set_new_image(self, filename):
        if self.avatar:
            old = os.path.join(Config.UPLOAD_FOLDER, self.avatar)
            if os.path.exists(old):
                os.remove(old)
        self.avatar = filename
        db.session.commit()


class ClientSchema(ma.TableSchema):
    class Meta:
        table = Client.__table__
    user_id = fields.Int()


class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    role_id = db.Column(db.Integer, db.ForeignKey("role.id"), nullable=False)
    fullname = db.Column(EncryptedType(db.String, Config.SECRET_KEY, AesEngine, 'pkcs5'), nullable=False)
    email = db.Column(EncryptedType(db.String, Config.SECRET_KEY, AesEngine, 'pkcs5'), nullable=False)
    password_hash = db.Column(db.String(400), nullable=False)
    avatar = db.Column(EncryptedType(db.String, Config.SECRET_KEY, AesEngine, 'pkcs5'))
    created = db.Column(db.DateTime, default=datetime.utcnow)
    updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class AdminSchema(ma.TableSchema):
    class Meta:
        table = Admin.__table__

    
class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    role = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(1000), nullable=False)
    created = db.Column(db.DateTime, default=datetime.utcnow)

    administrators = db.relationship(
        "Admin", cascade="all,delete", backref=db.backref("role", lazy=True), lazy=True
    )
    
    
class RoleSchema(ma.TableSchema):
    class Meta:
        table = Role.__table__


class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    ads = db.relationship(
        "Ad", cascade="all,delete", backref=db.backref("category", lazy=True), lazy=True
    )


class CategorySchema(ma.TableSchema):
    class Meta:
        table = Category.__table__


class Region(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(300), nullable=False)
    ads = db.relationship(
        "Ad", cascade="all,delete", backref=db.backref("region", lazy=True), lazy=True
    )


class RegionSchema(ma.TableSchema):
    class Meta:
        table = Region.__table__


class Place(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(300), nullable=False)
    region_id = db.Column(db.Integer, db.ForeignKey("region.id"), nullable=False)
    ads = db.relationship(
        "Ad", cascade="all,delete", backref=db.backref("place", lazy=True), lazy=True
    )


class PlaceSchema(ma.TableSchema):
    class Meta:
        table = Place.__table__


class AdImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    image = db.Column(db.String(300), nullable=False)
    ad_id = db.Column(db.Integer, db.ForeignKey("ad.id"), nullable=False)

    def save_image(self, filename, image64):
        path = os.path.join(Config.ADS_UPLOAD_FOLDER, filename)
        new_height = 400
        new_width = 400
        img = Image.open(BytesIO(base64.b64decode(image64)))
        width, height = img.size

        height_ratio = height/new_height
        width_ratio = width/new_width

        optimal_ratio = width_ratio
        if height_ratio < width_ratio:
            optimal_ratio = height_ratio

        optimal_size = (int(width / optimal_ratio), int(height / optimal_ratio))
        img = img.resize(optimal_size)
        img.save(path)
        self.image = filename


class AdImageSchema(ma.TableSchema):
    class Meta:
        table = AdImage.__table__


class Ad(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    summary = db.Column(db.Text, nullable=False, default="Summary")
    description = db.Column(db.Text, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey("category.id"), nullable=False)
    open = db.Column(db.Boolean, default=False)
    price = db.Column(db.Float, nullable=True)
    negotiable = db.Column(db.Boolean, default=False)
    phone = db.Column(db.String(20), nullable=False)
    address = db.Column(db.String(500))
    views = db.Column(db.Integer)
    region_id = db.Column(db.Integer,  db.ForeignKey("region.id"), nullable=False)
    client_id = db.Column(db.Integer,  db.ForeignKey("client.id"), nullable=False)
    place_id = db.Column(db.Integer,  db.ForeignKey("place.id"), nullable=False)
    default_image_id = db.Column(db.Integer, db.ForeignKey("ad_image.id", use_alter=True, name="ad_ibfk_4"))
    created = db.Column(db.DateTime, default=datetime.utcnow)
    updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    default_image = db.relationship("AdImage", foreign_keys=default_image_id, post_update=True)

    reviews = db.relationship(
        "Review", cascade="all,delete", backref=db.backref("ad", lazy=True), lazy=True
    )

    @hybrid_property
    def rating(self):
        return (
            sum(review.rating for review in self.reviews) / len(self.reviews) if self.reviews else 0
        )


class AdSchema(ma.TableSchema):
    class Meta:
        table = Ad.__table__
    rating = fields.Number()
    default_image = fields.Nested(AdImageSchema)
    category = fields.Nested(CategorySchema, only=["title", 'id'])
    region = fields.Nested(RegionSchema, only=["id", "title"])
    place = fields.Nested(PlaceSchema, only=["id", "title"])
    client = fields.Nested(ClientSchema, only=["id", "first_name", "last_name", "avatar"])


class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer,  db.ForeignKey("client.id"), nullable=False)
    ad_id = db.Column(db.Integer,  db.ForeignKey("ad.id"), nullable=False)
    review = db.Column(db.Text, nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    created = db.Column(db.DateTime, default=datetime.utcnow)


class ReviewSchema(ma.TableSchema):
    class Meta:
        table = Review.__table__
    ad = fields.Nested(AdSchema, only=["id", "title"])
    client = fields.Nested(ClientSchema, only=["id", "first_name", "last_name", "avatar"])


class Favourite(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer,  db.ForeignKey("client.id"), nullable=False)
    ad_id = db.Column(db.Integer,  db.ForeignKey("ad.id"), nullable=False)
    created = db.Column(db.DateTime, default=datetime.utcnow)


class FavouriteSchema(ma.TableSchema):
    class Meta:
        table = Review.__table__
    ad = fields.Nested(AdSchema, only=["id", "title"])
    client = fields.Nested(ClientSchema, only=["id", "first_name", "last_name", "avatar"])



@event.listens_for(AdImage, 'after_delete')
def delete_image(mapper, connection, target):
    old = os.path.join(Config.ADS_UPLOAD_FOLDER, target.image)
    if os.path.exists(old):
        os.remove(old)
