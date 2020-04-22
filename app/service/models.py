from app import db
from datetime import datetime
from sqlalchemy.ext.mutable import Mutable
from sqlalchemy.orm import relationship, backref
from sqlalchemy.schema import UniqueConstraint
from sqlalchemy.types import TypeDecorator, VARCHAR
from sqlalchemy.dialects.postgresql import TSVECTOR
import json


class JSONEncodedDict(TypeDecorator):
    "Represents an immutable structure as a json-encoded string."

    impl = VARCHAR

    def process_bind_param(self, value, dialect):
        if value is not None:
            value = json.dumps(value)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            value = json.loads(value)
        return value


class MutableDict(Mutable, dict):
    @classmethod
    def coerce(cls, key, value):
        "Convert plain dictionaries to MutableDict."

        if not isinstance(value, MutableDict):
            if isinstance(value, dict):
                return MutableDict(value)

            # this call will raise ValueError
            return Mutable.coerce(key, value)
        else:
            return value

    def __setitem__(self, key, value):
        "Detect dictionary set events and emit change events."

        dict.__setitem__(self, key, value)
        self.changed()

    def __delitem__(self, key):
        "Detect dictionary del events and emit change events."

        dict.__delitem__(self, key)
        self.changed()


# CREATING TABLES
class Advertisers(db.Model):
    __tablename__ = "advertisers"

    id = db.Column(db.Integer, primary_key=True)
    page_id = db.Column(db.String(25), unique=True, nullable=False)
    page_name = db.Column(db.Text, nullable=True, index=True)  # WTM advertiserName
    country = db.Column(db.String(10), nullable=False)  # GB,US...
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.now)
    updated_at = db.Column(
        db.DateTime(timezone=True), default=datetime.now, onupdate=datetime.now
    )

    def __init__(self, page_id, page_name, country):
        self.page_id = page_id
        self.page_name = page_name
        self.country = country

    def __repr__(self):
        return "page_id=" + str(self.page_id)


class Adverts(db.Model):
    __tablename__ = "adverts"

    id = db.Column(db.Integer, primary_key=True)
    page_id = db.Column(db.String(25), nullable=False)  # WTM advertiserId
    page_name = db.Column(db.Text, nullable=True, index=True)  # WTM advertiserName
    post_id = db.Column(db.String(25), unique=True, nullable=False)  # WTM postId
    country = db.Column(db.String(10), nullable=False)  # GB,US...
    ad_creation_time = db.Column(db.DateTime(timezone=True), nullable=True)
    ad_creative_body = db.Column(db.Text, nullable=True)
    ad_creative_link_caption = db.Column(db.Text, nullable=True)
    ad_creative_link_description = db.Column(db.Text, nullable=True)
    ad_creative_link_title = db.Column(db.Text, nullable=True)
    ad_delivery_start_time = db.Column(
        db.DateTime(timezone=True), nullable=True, index=True
    )
    ad_delivery_stop_time = db.Column(db.DateTime(timezone=True), nullable=True)
    ad_snapshot_url = db.Column(
        db.Text, nullable=True
    )  # temp link to ad in archive (includes token)
    image_link = db.Column(db.Text, nullable=True)  # AWS3
    currency = db.Column(db.String(10), nullable=True)
    funding_entity = db.Column(db.Text, nullable=True, index=True)
    ad_info = db.Column(
        JSONEncodedDict, nullable=True
    )  # additional page info from python media scrape
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.now)
    updated_at = db.Column(
        db.DateTime(timezone=True), default=datetime.now, onupdate=datetime.now
    )
    md = relationship("Media", cascade="all, delete-orphan", backref="adverts")
    text_search = db.Column(TSVECTOR)

    def __init__(
        self,
        page_id,
        page_name,
        post_id,
        country,
        ad_creation_time,
        ad_creative_body,
        ad_creative_link_caption,
        ad_creative_link_description,
        ad_creative_link_title,
        ad_delivery_start_time,
        ad_delivery_stop_time,
        ad_snapshot_url,
        image_link,
        currency,
        funding_entity,
        ad_info,
    ):
        self.page_id = page_id
        self.page_name = page_name
        self.post_id = post_id
        self.country = country
        self.ad_creation_time = ad_creation_time
        self.ad_creative_body = ad_creative_body
        self.ad_creative_link_caption = ad_creative_link_caption
        self.ad_creative_link_description = ad_creative_link_description
        self.ad_creative_link_title = ad_creative_link_title
        self.ad_delivery_start_time = ad_delivery_start_time
        self.ad_delivery_stop_time = ad_delivery_stop_time
        self.ad_snapshot_url = ad_snapshot_url
        self.image_link = image_link
        self.currency = currency
        self.funding_entity = funding_entity
        self.ad_info = ad_info

    def __repr__(self):
        return "The page_id is {}, page_name is {} ".format(
            self.page_id, self.page_name
        )


class Impressions(db.Model):
    __tablename__ = "impressions"

    id = db.Column(db.Integer, primary_key=True)
    advert_id = db.Column(
        db.Integer, db.ForeignKey("adverts.id"), nullable=False, index=True
    )
    page_id = db.Column(db.String(25), nullable=False, index=True)  # WTM advertiserId
    post_id = db.Column(db.String(25), nullable=False, index=True)
    country = db.Column(db.String(10), nullable=False)  # GB,US...
    demographic_distribution = db.Column(db.JSON, nullable=True)  # raw value
    _demographic_distribution_hash = db.Column(db.Text)
    region_distribution = db.Column(db.JSON, nullable=True)  # raw value
    _region_distribution_hash = db.Column(db.Text)
    impressions = db.Column(JSONEncodedDict, nullable=True)  # raw value
    spend = db.Column(JSONEncodedDict, nullable=True)  # raw value
    lower_bound_impressions = db.Column(db.String(25), nullable=True)  # parsed
    upper_bound_impressions = db.Column(db.String(25), nullable=True)  # parsed
    lower_bound_spend = db.Column(db.String(25), nullable=True)  # parsed
    upper_bound_spend = db.Column(db.String(25), nullable=True)  # parsed
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.now)
    updated_at = db.Column(
        db.DateTime(timezone=True), default=datetime.now, onupdate=datetime.now
    )
    dd = relationship(
        "Demographic_distribution", cascade="all, delete-orphan", backref="impressions"
    )
    rd = relationship(
        "Region_distribution", cascade="all, delete-orphan", backref="impressions"
    )

    __table_args__ = (
        UniqueConstraint(
            "post_id",
            "impressions",
            "spend",
            "_region_distribution_hash",
            "_demographic_distribution_hash",
            name="ix_unique_post_id_impressions_spend_region_demographic",
        ),
    )

    def __init__(
        self,
        advert_id,
        page_id,
        post_id,
        country,
        demographic_distribution,
        region_distribution,
        impressions,
        lower_bound_impressions,
        upper_bound_impressions,
        spend,
        lower_bound_spend,
        upper_bound_spend,
    ):
        self.advert_id = advert_id
        self.page_id = page_id
        self.post_id = post_id
        self.country = country
        self.demographic_distribution = demographic_distribution
        self.region_distribution = region_distribution
        self.impressions = impressions
        self.lower_bound_impressions = lower_bound_impressions
        self.upper_bound_impressions = upper_bound_impressions
        self.spend = spend
        self.lower_bound_spend = lower_bound_spend
        self.upper_bound_spend = upper_bound_spend

    def __repr__(self):
        return "The spend is {}, page_id is {}".format(self.spend, self.page_id)


class Demographic_distribution(db.Model):
    __tablename__ = "demographic_distribution"

    id = db.Column(db.Integer, primary_key=True)
    impression_id = db.Column(
        db.Integer, db.ForeignKey("impressions.id"), nullable=False, index=True
    )
    percentage = db.Column(db.Float, nullable=True)
    age = db.Column(db.String(10), nullable=True)
    gender = db.Column(db.String(10), nullable=True)  # "Male", "Female", "Unknown"
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.now)
    updated_at = db.Column(
        db.DateTime(timezone=True), default=datetime.now, onupdate=datetime.now
    )
    # impr = relationship("Impressions", backref=backref("dd", cascade="all, delete-orphan"))

    __table_args__ = (
        UniqueConstraint(
            "impression_id",
            "age",
            "gender",
            "percentage",
            name="ix_unique_impression_id_age_gender_percentage",
        ),
    )

    def __init__(self, impression_id, percentage, age, gender):
        self.impression_id = impression_id
        self.percentage = percentage
        self.age = age
        self.gender = gender

    def __repr__(self):
        return "The percentage is {}, impression_id is {}".format(
            self.percentage, self.impression_id
        )


class Region_distribution(db.Model):
    __tablename__ = "region_distribution"

    id = db.Column(db.Integer, primary_key=True)
    impression_id = db.Column(
        db.Integer, db.ForeignKey("impressions.id"), nullable=False, index=True
    )
    percentage = db.Column(db.Float, nullable=True)
    region = db.Column(db.String(255), nullable=True, index=True)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.now)
    updated_at = db.Column(
        db.DateTime(timezone=True), default=datetime.now, onupdate=datetime.now
    )
    # impr = relationship("Impressions", backref=backref("rd", cascade="all, delete-orphan"))

    __table_args__ = (
        UniqueConstraint(
            "impression_id",
            "region",
            "percentage",
            name="ix_unique_impression_id_region_percentage",
        ),
    )

    def __init__(self, impression_id, percentage, region):
        self.impression_id = impression_id
        self.percentage = percentage
        self.region = region

    def __repr__(self):
        return "The percentage is {}, impression_id is {}".format(
            self.percentage, self.impression_id
        )


class Media(db.Model):
    __tablename__ = "media"

    id = db.Column(db.Integer, primary_key=True)
    advert_id = db.Column(
        db.Integer, db.ForeignKey("adverts.id"), nullable=False, index=True
    )
    www_links = db.Column(db.JSON, nullable=True)  # raw value
    aws_links = db.Column(db.JSON, nullable=True)  # raw value
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.now)
    updated_at = db.Column(
        db.DateTime(timezone=True), default=datetime.now, onupdate=datetime.now
    )

    def __init__(self, advert_id, www_links, aws_links):
        self.advert_id = advert_id
        self.www_links = www_links
        self.aws_links = aws_links

    def __repr__(self):
        return "The link is {}".format(self.aws_links)


class Tokens(db.Model):
    __tablename__ = "tokens"

    id = db.Column(db.Integer, primary_key=True)
    short_token = db.Column(db.Text, unique=True, nullable=False)
    long_token = db.Column(db.Text, unique=True, nullable=True)
    short_last_updated_at = db.Column(
        db.DateTime(timezone=True), default=datetime.now, onupdate=datetime.now
    )
    long_last_updated_at = db.Column(
        db.DateTime(timezone=True), default=datetime.now, onupdate=datetime.now
    )
    long_token_expires_on = db.Column(db.DateTime(timezone=True), default=datetime.now)

    def __init__(
        self,
        short_token,
        long_token,
        short_last_updated_at,
        long_last_updated_at,
        long_token_expires_on,
    ):
        self.short_token = short_token
        self.long_token = long_token
        self.short_last_updated_at = short_last_updated_at
        self.long_last_updated_at = long_last_updated_at
        self.long_token_expires_on = long_token_expires_on

    def __repr__(self):
        return "long_last_updated_at is {}".format(self.long_last_updated_at)
