import logging

from ckan.common import _
from ckan.logic import ValidationError
from ckan.plugins import toolkit

log = logging.getLogger(__name__)


def rating_package_create(context, data_dict):
    '''Review a dataset (package).
    :param package: the name or id of the dataset to rate
    :type package: string
    :param rating: rate the dataset
    :type rating: boolean
    '''
    model = context.get('model')
    user = context.get('user')
    user = model.User.by_name(user)

    from ckan.model import User
    if not isinstance(user, User):
        if toolkit.request.environ.get('HTTP_X_FORWARDED_FOR') is None:
            user = toolkit.request.environ.get('REMOTE_ADDR')
        else:
            user = toolkit.request.environ.get('HTTP_X_FORWARDED_FOR')

    package_ref = data_dict.get('package')
    rating = data_dict.get('rating')
    error = None
    if not package_ref:
        error = _('You must supply a package id or name '
                  '(parameter "package").')
    elif not rating:
        error = _('You must supply a rating (parameter "rating").')
    else:
        package = model.Package.get(package_ref)
        if not package:
            error = _('Not found') + ': %r' % package_ref
    if error:
        raise ValidationError(error)
        
    from ckanext.rating.model import Rating
    Rating.create_package_rating(package.id, rating, user)

    return Rating.get_user_package_rating(user, package.id)


@toolkit.side_effect_free
def rating_package_get(context, data_dict):
    '''
    Get the rating and count of ratings for a package.

    Returns a dictionary containing rating and ratings counts.

    :param package_id: the id of the package
    :type package_id: string
    :rtype: dictionary

    '''
    package_id = data_dict.get('package_id')

    model = context.get('model')
    user = context.get('user')

    user = model.User.by_name(user)

    from ckan.model import User
    if not isinstance(user, User):
        if toolkit.request.environ.get('HTTP_X_FORWARDED_FOR') is None:
            user = toolkit.request.environ.get('REMOTE_ADDR')
        else:
            user = toolkit.request.environ.get('HTTP_X_FORWARDED_FOR')

    error = None

    if not package_id:
        error = _('You must supply a package id '
                  '(parameter "package_id").')
    if error:
        raise ValidationError(error)

    from ckanext.rating.model import Rating

    return Rating.get_user_package_rating(user, package_id)


@toolkit.side_effect_free
def rating_package_from_template(data_dict):
    '''
    Get the rating and count of ratings for a package.

    Returns a dictionary containing rating and ratings counts.

    :param package_id: the id of the package
    :type package_id: string
    :rtype: dictionary

    '''
    package_id = data_dict.get('package_id')

    error = None

    if not package_id:
        error = _('You must supply a package id '
                  '(parameter "package_id").')
    if error:
        raise ValidationError(error)

    from ckanext.rating.model import Rating

    return Rating.get_package_rating(package_id)
