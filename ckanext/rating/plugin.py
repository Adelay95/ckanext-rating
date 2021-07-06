import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
from ckan.common import c, g
import sqlalchemy
import ckan.model as model

from ckanext.rating.logic import action
from ckanext.rating import helpers
import ckanext.rating.logic.auth as rating_auth
from ckanext.rating.model import Rating
from ckan.lib.plugins import DefaultTranslation
from ckan.plugins.toolkit import get_action
from helpers import show_rating_in_type

import logging

log = logging.getLogger(__name__)

def sort_by_rating(sort):
    limit = g.datasets_per_page
    if c.current_page:
        page = c.current_page
    else:
        page = 1
    offset = (page - 1) * limit
    c.count_pkg = model.Session.query(
                sqlalchemy.func.count(model.Package.id)).\
        filter(model.Package.type == 'dataset').\
        filter(
            model.Package.private == False # noqa E712
        ).\
        filter(model.Package.state == 'active').scalar()
    query = model.Session.query(
                model.Package.id, model.Package.title).\
                outerjoin(Rating, Rating.package_id == model.Package.id).\
                filter(model.Package.type == 'dataset').\
                filter(
                    model.Package.private == False # noqa E712
                ).\
                filter(model.Package.state == 'active').\
                group_by(model.Package.id).\
                distinct().order_by(sqlalchemy.desc(Rating.rating))
    res = query.offset(offset).limit(limit)
    c.qr = q = [id[0] for id in res]
    tmp = 'id:('
    for id in q:
        tmp += id + ' OR '
    q = tmp[:-4] + ')'
    return q



class RatingPlugin(plugins.SingletonPlugin, DefaultTranslation):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IActions)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.IAuthFunctions)
    plugins.implements(plugins.IPackageController, inherit=True)
    plugins.implements(plugins.IRoutes, inherit=True)
    if toolkit.check_ckan_version(min_version='2.5.0'):
        plugins.implements(plugins.ITranslation, inherit=True)

    # IConfigurer

    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')
        toolkit.add_resource('fanstatic', 'rating')
        toolkit.add_resource('public/css/', 'rating_css')
        toolkit.add_resource('public/js/', 'rating_js')

    # IActions

    def get_actions(self):
        return {
            'rating_package_create': action.rating_package_create,
            'rating_package_get': action.rating_package_get,
            'rating_showcase_create': action.rating_package_create,
            'rating_showcase_get': action.rating_package_get
        }

    # ITemplateHelpers
    def get_helpers(self):
        return {
            'package_rating': action.rating_package_get,
            'get_user_rating': helpers.get_user_rating,
            'show_rating_in_type': helpers.show_rating_in_type,
            'package_rating_template': action.rating_package_from_template
        }

    # IAuthFunctions

    def get_auth_functions(self):
        return rating_auth.get_rating_auth_dict()

    # IPackageController

    def before_index(self, data_dict):
        rating_dict = action.rating_package_get(None, {'package_id': data_dict['id']})
        data_dict['rating'] = rating_dict.first().rating if rating_dict.first() is not None else False
        return data_dict

    def after_show(self, context, pkg_dict):
        if show_rating_in_type(pkg_dict.get('type')):
            rating_dict = get_action('rating_package_get')(context, {'package_id': pkg_dict.get('id')})
            pkg_dict['rating'] = rating_dict.first().rating if rating_dict.first() is not None else False
        return pkg_dict

    def after_search(self, search_results, search_params):
        for pkg in search_results['results']:
            if show_rating_in_type(pkg.get('type')):
                rating_dict = get_action('rating_package_get')({}, {'package_id': pkg.get('id')})
                pkg['rating'] = rating_dict.first().rating if rating_dict.first() is not None else False
        return search_results

    # IRoutes

    def before_map(self, map):
        map.connect('/rating/dataset/:package/:rating',
                    controller='ckanext.rating.controller:RatingController',
                    action='submit_package_rating')

        map.connect('/rating/showcase/:package/:rating',
                    controller='ckanext.rating.controller:RatingController',
                    action='submit_showcase_rating')

        map.connect(
            '/dataset',
            controller='ckanext.rating.controller:RatingPackageController',
            action='search',
            highlight_actions='index search'
        )

        return map
