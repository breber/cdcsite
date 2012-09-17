import webapp2
from webapp2_extras import auth
from webapp2_extras import sessions

def get_context(auth):
    context = {}

    current_session = auth.get_user_by_session()

    if not current_session is None:
        user_objects = auth.store.user_model.get_by_auth_token(current_session['user_id'], current_session['token'])
        user_object = user_objects[0]
        
        if not user_object is None:
            context['username'] = user_object.auth_ids[0]
            context['is_admin'] = user_object.is_admin
            context['is_employee'] = user_object.is_employee

    return context
