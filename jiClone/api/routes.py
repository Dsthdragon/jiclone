from flask import jsonify, request, make_response, current_app, url_for

from sqlalchemy import or_

from jiClone.api import bp

from jiClone.models import *

from jiClone import db

import uuid

ALLOWED_EXTENSIONS = ['png', 'jpeg', 'jpg', 'gif']


# User Routes
@bp.route('/user/auth')
def user_auth():
    user_id = User.decode_token(request.cookies.get('auth'))
    user = User.query.get(user_id)
    if not user:
        return jsonify(status="failed", message="Invalid token received", isAuth=False)
    client = ClientSchema().dump(user.client)
    admin = AdminSchema().dump(user.admin)
    return jsonify(status="success", message="User Logged In", isAuth=True, client=client, admin=admin)

# Client Routes
@bp.route("/client")
def get_clients():
    page = request.args.get("page", 1, type=int)
    clients = Client.query.order_by(Client.created.desc()).paginate(page, current_app.config['POSTS_PER_PAGE'], False)
    has_next = clients.has_next
    clients = ClientSchema(many=True).dump(clients.items)
    return jsonify(status="success", message="Clients Found", clients=clients, has_next=has_next)


@bp.route("/client",  methods=["POST"])
def register_client():
    data = request.get_json()

    if data is None:
        return jsonify(status="failed", message="No Data Sent!")

    if not data.get("email"):
        return jsonify(status="failed", message="Email Address required!")
    if not data.get("first_name"):
        return jsonify(status="failed", message="First Name required!")
    if not data.get("password"):
        return jsonify(status="failed", message="Password required!")

    client = Client.query.filter_by(email=data["email"]).first()
    if client:
        return jsonify(status="failed", message="Email Address already in system!")
    
    user = User()
    db.session.add(user)
    db.session.commit()

    client = Client(
            email=data.get("email"),
            phone=data.get("phone"),
            first_name=data.get("first_name"),
            last_name=data.get("last_name"),
            user_id=user.id
        )

    client.set_password(data.get("password"))

    db.session.add(client)
    db.session.commit()

    client = ClientSchema().dump(client)
    return jsonify(status="success", message="Registration SuccessFul", client=client)


@bp.route('/client/login', methods=["POST"])
def login_client():
    data = request.get_json()

    if data is None:
        return jsonify(status="failed", message="No Data Sent!")

    if not data.get("email"):
        return jsonify(status="failed", message="Email Address required!")
    if not data.get("password"):
        return jsonify(status="failed", message="Password required!")

    client = Client.query.filter_by(email=data['email']).first()
    if not client:
        return jsonify(status="failed", message="Email address not in system!")

    if not client.check_password(data['password']):
        return jsonify(status="failed", message="invalid password!")

    resp = make_response(jsonify(status="success", message="Login Successful!"))
    resp.set_cookie('auth', client.user.generate_token())
    return resp


@bp.route("/client",  methods=["PUT"])
def update_client():
    data = request.get_json()

    if data is None:
        return jsonify(status="failed", message="No Data Sent!")

    if not data.get("first_name"):
        return jsonify(status="failed", message="First Name required!")
    
    client = Client.query.get(data.get('id'))

    if not client:
        return jsonify(status="failed", message="Client not found!")

    client.first_name = data.get('first_name')
    client.phone = data.get('phone')
    client.last_name = data.get('last_name')
    db.session.commit()

    client = ClientSchema().dump(client)
    return jsonify(status="success", message="Client Data updated SuccessFul", client=client)


@bp.route("/client/avatar", methods=["POST"])
def upload_client_avatar():
    data = request.get_json()

    if data is None:
        return jsonify(status="failed", message="No data Sent!")

    if not data.get('id'):
        return jsonify(status="failed", message="Client ID required!")

    if not data.get('type'):
        return jsonify(status="failed", message="Image type required!")

    if not data.get('img'):
        return jsonify(status="failed", message="Image data not sent!")

    if data.get('type').lower() not in ALLOWED_EXTENSIONS:
        return jsonify(status="failed", message="Extension not supported!")

    client = Client.query.get(data['id'])

    unique_filename = str(uuid.uuid4()) + '.' + data['type']
    client.save_image(unique_filename, data['img'])
    client = ClientSchema().dump(client)
    return jsonify(status="success", message="Avatar Uploaded!", client=client)


@bp.route("/client/password", methods=["POST"])
def change_password():
    data = request.get_json()

    if data is None:
        return jsonify(status="failed", message="No data Sent!")

    if not data.get('id'):
        return jsonify(status="failed", message="Client ID required!")

    if not data.get('password'):
        return jsonify(status="failed", message="Password required!")

    if not data.get('new_password'):
        return jsonify(status="failed", message="New Password required!")

    if not data.get('password_confirm'):
        return jsonify(status="failed", message="Password Confirmation required!")

    client = Client.query.get(data.get('id'))

    if not client:
        return jsonify(status="failed", message="Client not found!")

    if not client.check_password(data.get('password')):
        return jsonify(status="failed", message="Invalid password!")

    if data.get('new_password') == data.get('password'):
        return jsonify(status="failed", message="New password must be different from old!")

    if data.get('new_password') != data.get('password_confirm'):
        return jsonify(status="failed", message="Password confirmation failed!")

    client.set_password(data.get('new_password'))
    db.session.commit()

    return jsonify(status="success", message="Password updated!")


@bp.route("/client/<client_id>")
def get_client(client_id):
    client = Client.query.get(client_id)

    if not client:
        return jsonify(status="failed", message="Client not found!")

    client = ClientSchema().dump(client)
    return jsonify(status="success", message="Client Found", client=client)


@bp.route("/client/avatar/<filename>")
def client_avatar(filename):
    return url_for('static', filename=f'upload/images/{filename}')

# Place Routes
@bp.route("/place")
def get_places():
    limited = request.args.get('limited', 1, type=int)
    if limited:
        page = request.args.get("page", 1, type=int)
        places = Place.query.paginate(page, current_app.config['POSTS_PER_PAGE'], False)
        has_next = places.has_next
        places = places.items
    else:
        places = Place.query.all()
        has_next = False
    places = PlaceSchema(many=True).dump(places)
    return jsonify(status="success", message="Places Found", places=places, has_next=has_next)


# Place Routes
@bp.route("/place/region/<region>")
def get_places_by_region(region):
    limited = request.args.get('limited', 1, type=int)
    if limited:
        page = request.args.get("page", 1, type=int)
        places = Place.query.filter_by(region_id=region)\
            .paginate(page, current_app.config['POSTS_PER_PAGE'], False)
        has_next = places.has_next
        places = places.items
    else:
        places = Place.query.filter_by(region_id=region).all()
        has_next = False
    places = PlaceSchema(many=True).dump(places)
    return jsonify(status="success", message="Places Found", places=places, has_next=has_next)


@bp.route("/place/<place_id>")
def get_place(place_id):
    place = Place.query.get(place_id)

    if not place:
        return jsonify(status="failed", message="Place not found!")

    place = PlaceSchema().dump(place)
    return jsonify(status="success", message="Place Found", place=place)


@bp.route("/place", methods=["POST"])
def add_place():
    data = request.get_json()
    
    if data is None:
        return jsonify(status="failed", message="No Data Sent!")

    if not data.get("title"):
        return jsonify(status="failed", message="Title Required!")
    if not data.get("region_id"):
        return jsonify(status="failed", message="Region Id Required!")
    place = Place(title=data.get('title'), region_id=data.get("region_id"))

    db.session.add(place)
    db.session.commit()

    place = PlaceSchema().dump(place)
    return jsonify(status="success", message="Place Created", place=place)


# Region Routes
@bp.route("/region")
def get_regions():
    limited = request.args.get("limited", 1, type=int)
    if limited:
        page = request.args.get("page", 1, type=int)
        regions = Region.query.paginate(page, current_app.config['POSTS_PER_PAGE'], False)
        has_next = regions.has_next
        regions = regions.items
    else:
        regions = Region.query.all()
        has_next = False
    regions = RegionSchema(many=True).dump(regions)
    return jsonify(status="success", message="Regions Found", regions=regions, has_next=has_next)


@bp.route("/region/<region_id>")
def get_region(region_id):
    region = Region.query.get(region_id)

    if not region:
        return jsonify(status="failed", message="Region not found!")

    region = RegionSchema().dump(region)
    return jsonify(status="success", message="Region Found", region=region)


@bp.route("/region", methods=["POST"])
def add_region():
    data = request.get_json()
    
    if data is None:
        return jsonify(status="failed", message="No Data Sent!")

    if not data.get("title"):
        return jsonify(status="failed", message="Title Required!")

    region = Region(title=data.get('title'))

    db.session.add(region)
    db.session.commit()

    region = RegionSchema().dump(region)
    return jsonify(status="success", message="Region Created", region=region)


# Category Routes
@bp.route("/category")
def get_categories():
    limited = request.args.get("limited", 1, type=int)
    if limited:
        page = request.args.get("page", 1, type=int)
        categories = Category.query.paginate(page, current_app.config['POSTS_PER_PAGE'], False)
        has_next = categories.has_next
        categories = categories.items
    else:
        categories = Category.query.all()
        has_next = False
    categories = CategorySchema(many=True).dump(categories)
    return jsonify(status="success", message="Categories Found", categories=categories, has_next=has_next)


@bp.route("/category/<category_id>")
def get_category(category_id):
    category = Category.query.get(category_id)

    if not category:
        return jsonify(status="failed", message="Category not found!")

    category = CategorySchema().dump(category)
    return jsonify(status="success", message="Category Found", category=category)


@bp.route("/category", methods=["POST"])
def add_category():
    data = request.get_json()
    
    if data is None:
        return jsonify(status="failed", message="No Data Sent!")

    if not data.get("title"):
        return jsonify(status="failed", message="Title Required!")

    category = Category(title=data.get('title'))

    db.session.add(category)
    db.session.commit()

    category = CategorySchema().dump(category)
    return jsonify(status="success", message="Category Created", category=category)


# Ad Post
@bp.route("/service", methods=["POST"])
def create_ad():
    data = request.get_json()

    if not data:
        return jsonify(status="failed", message="No Data Sent!")

    if not data.get('category'):
        return jsonify(status="failed", message="Category Required!")

    if not data.get('title'):
        return jsonify(status="failed", message="Title Required!")

    if not data.get('description'):
        return jsonify(status="failed", message="Description Required!")

    if not data.get('region'):
        return jsonify(status="failed", message="Region Required!")

    if not data.get('place'):
        return jsonify(status="failed", message="Place Required!")

    if not data.get('open') and not data.get('price'):
        return jsonify(status="failed", message="Price required!")

    if not data.get('summary'):
        return jsonify(status="failed", message="Summary Required!")

    if not data.get('client'):
        return jsonify(status="failed", message="Client required!")

    if not data.get('image'):
        return jsonify(status="failed", message="Title Image required!")

    if not data.get('address'):
        return jsonify(status="failed", message="Address required!")

    client = Client.query.get(data['client'])
    if not client:
        return jsonify(status="failed", message="Client not Found!")

    ad = Ad()
    ad.category_id = data['category']
    ad.open = data['open']
    ad.price = data['price']
    ad.negotiable = data['negotiable']
    ad.phone = data['phone']
    ad.description = data['description']
    ad.summary = data['summary']
    ad.title = data['title']
    ad.region_id = data['region']
    ad.place_id = data['place']
    ad.client_id = data['client']
    ad.address = data['address']

    db.session.add(ad)
    db.session.commit()

    unique_filename = str(uuid.uuid4()) + '.' + data['type']
    ad_image = AdImage()
    ad_image .image = unique_filename
    ad_image.ad_id = ad.id
    ad_image.default = True
    ad_image.save_image(unique_filename, data['image'])
    db.session.add(ad_image)
    db.session.commit()
    ad.default_image_id = ad_image.id
    db.session.commit()
    ad = AdSchema().dump(ad)
    return jsonify(status="success", message="Ad Uploaded", ad=ad)


@bp.route("/service", methods=["PUT"])
def update_ad():
    data = request.get_json()

    if not data:
        return jsonify(status="failed", message="No Data Sent!")

    if not data.get('category'):
        return jsonify(status="failed", message="Category Required!")

    if not data.get('title'):
        return jsonify(status="failed", message="Title Required!")

    if not data.get('summary'):
        return jsonify(status="failed", message="Summary Required!")

    if not data.get('description'):
        return jsonify(status="failed", message="Description Required!")

    if not data.get('region'):
        return jsonify(status="failed", message="Region Required!")

    if not data.get('place'):
        return jsonify(status="failed", message="Place Required!")

    if not data.get('address'):
        return jsonify(status="failed", message="Address Required!")

    if not data.get('open') and not data.get('price'):
        return jsonify(status="failed", message="Price required!")

    if not data.get('id'):
        return jsonify(status="failed", message="Ad required!")

    ad = Ad.query.get(data['id'])
    if not ad:
        return jsonify(status="failed", message="Ad Not Found!")
    ad.category_id = data['category']
    ad.open = data['open']
    ad.price = data['price']
    ad.negotiable = data['negotiable']
    ad.phone = data['phone']
    ad.description = data['description']
    ad.summary = data['summary']
    ad.address = data['address']
    ad.title = data['title']
    ad.region_id = data['region']
    ad.place_id = data['place']

    db.session.add(ad)
    db.session.commit()

    ad = AdSchema().dump(ad)
    return jsonify(status="success", message="Ad Uploaded", ad=ad)


@bp.route("/category_service/<category>")
def get_category_ads(category):
    limited = request.args.get("limited", 1, type=int)
    if limited:
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 0, type=int)
        per_page = per_page if per_page != 0 else current_app.config['POSTS_PER_PAGE']
        ads = Ad.query.filter_by(category_id=category)\
            .order_by(Ad.created.desc())\
            .paginate(page, per_page, False)
        has_next = ads.has_next
        ads = ads.items
    else:
        ads = Ad.query.filter_by(category_id=category).order_by(Ad.created.desc()).all()
        has_next = False
    ads = AdSchema(many=True).dump(ads)
    return jsonify(status="success", message="Ads Found", ads=ads, has_next=has_next)


@bp.route("/service")
def get_ads():
    limited = request.args.get("limited", 1, type=int)
    if limited:
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 0, type=int)
        per_page = per_page if per_page != 0 else current_app.config['POSTS_PER_PAGE']
        ads = Ad.query.order_by(Ad.created.desc()).paginate(page, per_page, False)
        has_next = ads.has_next
        ads = ads.items
    else:
        ads = Ad.query.order_by(Ad.created.desc()).all()
        has_next = False
    ads = AdSchema(many=True).dump(ads)
    return jsonify(status="success", message="Ads Found", ads=ads, has_next=has_next)


@bp.route("/find_service")
def find_ads():
    title = request.args.get("title", "", type=str)
    address = request.args.get("address", "", type=str)
    category = request.args.get("category", None, type=int)
    region = request.args.get("region", None, type=int)
    place = request.args.get("place", None, type=int)
    order_by = request.args.get("order_by", "created", type=str)
    order = request.args.get("order", 'desc', type=str)
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 0, type=int)
    per_page = per_page if per_page != 0 else current_app.config['POSTS_PER_PAGE']

    ads = Ad.query
    if title:
        ads = ads.filter(or_(Ad.title.ilike(f"%{title}%"), Ad.description.ilike(f"%{title}%")))

    if address:
        ads = ads.filter(Ad.address.ilike(f"%{address}%"))

    if category:
        ads = ads.filter_by(category_id=category)

    if region:
        ads = ads.filter_by(region_id=region)

    if place:
        ads = ads.filter_by(place_id=place)

    if order == 'desc':
        ads = ads.order_by(getattr(Ad, order_by).desc())
    else:
        ads = ads.order_by(getattr(Ad, order_by).asc())

    ads = ads.paginate(page, per_page, False)
    has_next = ads.has_next
    total = ads.total
    ads = ads.items

    ads = AdSchema(many=True).dump(ads)
    return jsonify(status="success", message="Ads Found", ads=ads, has_next=has_next, total=total)


@bp.route("/client_services/<client>")
def get_client_ads(client):
    limited = request.args.get("limited", 1, type=int)
    if limited:
        page = request.args.get("page", 1, type=int)
        ads = Ad.query.filter_by(client_id=client).order_by(
                Ad.created.desc()
            ).paginate(page, current_app.config['POSTS_PER_PAGE'], False)
        has_next = ads.has_next
        ads = ads.items
    else:
        ads = Ad.query.filter_by(client_id=client).order_by(Ad.created.desc()).all()
        has_next = False
    ads = AdSchema(many=True).dump(ads)
    return jsonify(status="success", message="Ads Found", ads=ads, has_next=has_next)


@bp.route("/service/<service_id>")
def get_ad(service_id):

    viewed = request.args.get("viewed", 0, type=int)

    ad = Ad.query.get(service_id)
    if viewed:
        if ad.views:
            ad.views += 1
        else:
            ad.views = 1
        db.session.commit()

    if not ad:
        return jsonify(status="failed", message="Ad not found!")

    ad = AdSchema().dump(ad)
    return jsonify(status="success", message="Ad Found", ad=ad)


# Ad Images
@bp.route("/service_image/<service_id>")
def get_images(service_id):
    ad = Ad.query.get(service_id)
    if not ad:
        return jsonify(status="failed", message="Ad not found!")

    ad_images = AdImage.query.filter_by(ad_id=service_id).filter(AdImage.id != ad.default_image_id).all()
    ad_images = AdImageSchema(many=True).dump(ad_images)
    return jsonify(status="success", messsage="Ad Images Found", ad_images=ad_images)


@bp.route("/service_image", methods=["POST"])
def upload_image():
    data = request.get_json()

    if not data.get('ad'):
        return jsonify(status="failed", message="Ad Required!")

    if not data.get('img'):
        return jsonify(status="failed", message="Image Required!")

    if not data.get('type'):
        return jsonify(status="failed", message="Type Required!")

    ad = Ad.query.get(data['ad'])
    if not ad:
        return jsonify(status="failed", message="Ad not Found!")

    unique_filename = str(uuid.uuid4()) + '.' + data['type']
    ad_image = AdImage()
    ad_image.image = unique_filename
    ad_image.ad_id = ad.id
    ad_image.default = True
    ad_image.save_image(unique_filename, data['img'])
    db.session.add(ad_image)
    db.session.commit()
    ad_image = AdImageSchema().dump(ad_image)
    return jsonify(status="success", message="Ad Image Uploaded", ad_image=ad_image)


@bp.route("/service_image/delete", methods=["POST"])
def delete_service_image():
    data = request.get_json()

    if not data.get('client'):
        return jsonify(status="failed", message="Client Required!")

    if not data.get('ad'):
        return jsonify(status="failed", message="Ad Required!")

    if not data.get('image'):
        return jsonify(status="failed", message="image Required!")

    ad = Ad.query.get(data['ad'])
    if not ad:
        return jsonify(status="failed", message="Ad Not found!")

    if ad.client_id != data['client']:
        return jsonify(status="failed", message="Ad Does Not belong to client!")

    ad_image = AdImage.query.get(data['image'])

    if not ad_image:
        return jsonify(status="failed", message="Ad Image Not Found!")

    if ad_image.ad_id != ad.id:
        return jsonify(status="failed", message="Image does not belong to ad")

    db.session.delete(ad_image)
    db.session.commit()
    return jsonify(status="success", message="Ad Image Delete")


@bp.route("/service_image/main", methods=["POST"])
def main_service_image():
    data = request.get_json()

    if not data.get('client'):
        return jsonify(status="failed", message="Client Required!")

    if not data.get('ad'):
        return jsonify(status="failed", message="Ad Required!")

    if not data.get('image'):
        return jsonify(status="failed", message="image Required!")

    ad = Ad.query.get(data['ad'])
    if not ad:
        return jsonify(status="failed", message="Ad Not found!")

    if ad.client_id != data['client']:
        return jsonify(status="failed", message="Ad Does Not belong to client!")

    ad_image = AdImage.query.get(data['image'])

    if not ad_image:
        return jsonify(status="failed", message="Ad Image Not Found!")

    if ad_image.ad_id != ad.id:
        return jsonify(status="failed", message="Image does not belong to ad")

    ad.default_image_id = ad_image.id
    db.session.commit()

    return jsonify(status="success", message="Ad Image Set As Main")


@bp.route("/review", methods={"POST"})
def create_review():
    data = request.get_json()

    if not data:
        return jsonify(status="failed", message="No Data Sent!")

    if not data.get('ad'):
        return jsonify(status="failed", message="Ad required!")

    if not data.get('client'):
        return jsonify(status="failed", message="Client Required!")

    if not data.get('review'):
        return jsonify(status="failed", message="Review Required!")

    if not data.get('rating'):
        return jsonify(status="failed", message="Rating Required!")

    if int(data.get('rating')) not in [1, 2, 3, 4, 5]:
        return jsonify(status="failed", message="Invalid Rating submitted!")

    ad = Ad.query.get(data['ad'])
    if not ad:
        return jsonify(status="failed", message="Ad not found!")

    if ad.client_id == data['client']:
        return jsonify(status="failed", message="Cannot Review Your Own Ad!")

    reviewed = Review.query.filter_by(client_id=data['client'], ad_id=data['ad']).first()
    if reviewed:
        return jsonify(status="failed", message="Already reviewed!")

    review = Review()
    review.client_id = data['client']
    review.ad_id = data['ad']
    review.rating = data['rating']
    review.review = data['review']

    db.session.add(review)
    db.session.commit()

    return jsonify(status="success", message="Review Successful!")


@bp.route("/check_review", methods=["POST"])
def check_review():
    data = request.get_json()
    if not data:
        return jsonify(status="failed", message="No Data Sent!")

    if not data.get('ad'):
        return jsonify(status="failed", message="Ad required!")

    if not data.get('client'):
        return jsonify(status="failed", message="Client Required!")

    reviewed = Review.query.filter_by(client_id=data['client'], ad_id=data['ad']).first()
    if reviewed:
        return jsonify(status="failed", message="Already reviewed!")

    return jsonify(status="success", message="Can review!")


@bp.route("/service_review/<ad>")
def service_review(ad):
    ad = Ad.query.get(ad)
    if not ad:
        return jsonify(status="failed", message="Ad not found")

    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 0, type=int)
    per_page = per_page if per_page != 0 else current_app.config['POSTS_PER_PAGE']
    reviews = Review.query.filter_by(ad_id=ad.id).order_by(Review.created.desc()).paginate(page, per_page, False)
    has_next = reviews.has_next
    total = reviews.total
    reviews = reviews.items

    reviews = ReviewSchema(many=True).dump(reviews)

    return jsonify(status="success", message="Reviews Found", reviews=reviews, has_next=has_next, total=total)
