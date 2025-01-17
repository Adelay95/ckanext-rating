import uuid
import datetime

from sqlalchemy import Column
from sqlalchemy import types
from sqlalchemy.ext.declarative import declarative_base
from ckan.lib import dictization
import ckan.model as model
import ckan.logic as logic
import ckan.plugins.toolkit as toolkit
import ckan.common as common

log = __import__('logging').getLogger(__name__)

Base = declarative_base()

def make_uuid():
    return unicode(uuid.uuid4())


class Rating(Base):

    __tablename__ = 'review'

    id = Column(types.UnicodeText, primary_key=True, default=make_uuid)
    package_id = Column(types.UnicodeText, nullable=True, index=True)
    rating = Column(types.Boolean, nullable=False)
    user_id = Column(types.UnicodeText, nullable=True, index=True)
    rater_ip = Column(types.UnicodeText)  # Used for identification if user is not authenticated
    created = Column(types.DateTime, default=datetime.datetime.now)
    updated = Column(types.DateTime, default=datetime.datetime.now)

    def as_dict(self):
        context = {'model': model}
        rating_dict = dictization.table_dictize(self, context)
        return rating_dict

    @classmethod
    def create_package_rating(cls, package_id, rating, ip_or_user):

        existing_rating = cls.get_user_package_rating(ip_or_user, package_id)
        if (existing_rating.first()):
            existing_rating.update({'rating': rating})
            model.repo.commit()
            log.info('Review updated for package')
        else:
            user_id = None
            from ckan.model import User

            if isinstance(ip_or_user, User):
                user_id = ip_or_user.id
                ip_or_user = None

            review = Rating(
                user_id=user_id,
                rater_ip=ip_or_user,
                package_id=package_id,
                rating=rating
            )
            
            model.Session.add(review)
            model.repo.commit()
            log.info('Review added for package')
        rating_count = cls.get_package_rating(package_id)
        package_show = logic.get_action(u'package_show')
        user = toolkit.get_action(u'get_site_user')({u'ignore_auth': True}, {})
        context = {
            'model': model,
            'session': model.Session,
            'user': user[u'name'],
            'return_id_only': True,
            'auth_user_obj': common.c.userobj
        }
        pkg = package_show(context, {u'id': package_id})
        pkg['rating_count'] = rating_count.get('ratings_count')
        logic.get_action('package_update')(context, pkg)

    @classmethod
    def get_user_package_rating(cls, ip_or_user, package_id):

        user_id = None
        from ckan.model import User

        if isinstance(ip_or_user, User):
            user_id = ip_or_user.id
            ip_or_user = None

        rating = model.Session.query(cls).filter(
                    cls.package_id == package_id,
                    cls.user_id == user_id,
                    cls.rater_ip == ip_or_user)

        return rating

    @classmethod
    def get_package_rating(cls, package_id):
        ratings = model.Session.query(cls) \
                    .filter(cls.package_id == package_id) \
                    .filter(Rating.rating == True) \
                    .all()
        return {
            'rating': True if len(ratings) > 0 else False,
            'ratings_count': len(ratings)
        }


def init_tables(engine):
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    log.info('Rating database tables are set-up')
