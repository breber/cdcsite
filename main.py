#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import os
import urllib
import webapp2
import logging

from webapp2_extras import auth
from webapp2_extras import sessions

from google.appengine.ext.webapp import template
from google.appengine.ext import blobstore
from google.appengine.ext.webapp import blobstore_handlers

import models
import utils


def user_required(handler):
    """
         Decorator for checking if there's a user associated with the current session.
         Will also fail if there's no session present.
     """
    def check_login(self, *args, **kwargs):
        auth = self.auth
        if not auth.get_user_by_session():
            # If handler has no login_url specified invoke a 403 error
            try:
                self.redirect(self.auth_config['login_url'], abort=True)
            except (AttributeError, KeyError), e:
                self.abort(403)
        else:
            return handler(self, *args, **kwargs)

    return check_login

class BaseHandler(webapp2.RequestHandler):
    """
         BaseHandler for all requests

         Holds the auth and session properties so they are reachable for all requests
     """
    def dispatch(self):
        """
              Save the sessions for preservation across requests
          """
        try:
            response = super(BaseHandler, self).dispatch()
        finally:
            self.session_store.save_sessions(self.response)

    @webapp2.cached_property
    def auth(self):
        return auth.get_auth()

    @webapp2.cached_property
    def session_store(self):
        return sessions.get_store(request=self.request)

    @webapp2.cached_property
    def auth_config(self):
        """
              Dict to hold urls for login/logout
          """
        return {
            'login_url': self.uri_for('login'),
            'logout_url': self.uri_for('logout')
        }

class MainHandler(BaseHandler):
    def get(self):
        mike_exists = models.Account.all().filter('username =', 'mike')
        if not mike_exists.count():
            account = models.Account(username="mike", password="test", given_name="Michael", is_admin=True, is_employee=True, ssn='999999999')
            account.save()

        context = utils.get_context(self.auth)
        path = os.path.join(os.path.dirname(__file__), 'templates/home.html')
        self.response.out.write(template.render(path, context))


# This class is used to easily change employee information so that teams have
# unique employee information.  You are more than welcome to delete this class.
# This is the only functionality you are allowed to remove. -- White Team
class edit_employee(BaseHandler):
    @user_required
    def get(self):
        username = self.request.GET['username']
        ssn = self.request.GET['ssn']

        account = models.Account.all().filter('username =', username).fetch(1)
        account = account[0]
        account.ssn = ssn
        account.save()


class view_directory(BaseHandler):
    @user_required
    def get(self):
        context = utils.get_context(self.auth)

        if context['is_admin']:
            employee_query = models.Account.all().filter('is_employee =', True).filter('username !=', 'mike')
            employees = employee_query.fetch(1000)
            context['employees'] = employees
            path = os.path.join(os.path.dirname(__file__),
                                'templates/directory.html')
            self.response.out.write(template.render(path, context))

        else:
            path = os.path.join(os.path.dirname(__file__),
                                'templates/error_no_permission.html')
            self.response.out.write(template.render(path, context))

    @user_required
    def post(self):
        keys = {x : self.request.POST[x] for x in self.request.POST}

        employee_key = self.request.get('edit_employee', None)
        if employee_key:
            account = models.Account.get(str(employee_key))

            if 'edit_given_name' in keys:
                account.given_name = keys['edit_given_name']
            if 'edit_ssn' in keys:
                account.ssn = keys['edit_ssn']
            if 'edit_username' in keys:
                account.username = keys['edit_username']
            if 'edit_password' in keys:
                account.password = keys['edit_password']

            account.save()
            self.redirect('/directory')

        else:
            newbie = models.Account(given_name=keys['given_name'],
                                    ssn=keys['ssn'],
                                    username=keys['username'],
                                    password=keys['password'],
                                    is_employee=True,
                                    is_admin=True)

            newbie.save()

            user = self.auth.store.user_model.create_user(keys['username'], 
                                                          password_raw=keys['password'], 
                                                          is_employee=newbie.is_employee,
                                                          is_admin=newbie.is_admin)

        self.redirect('/directory')

class edit_profile(BaseHandler):
    @user_required
    def get(self):
        context = utils.get_context(self.auth)

        if context['is_employee']:
            employee = models.Account.all().filter('username =', context['username'])[0]
            context['employee'] = employee

        path = os.path.join(os.path.dirname(__file__), 'templates/profile.html')
        self.response.out.write(template.render(path, context))

    @user_required
    def post(self):
        keys = {x : self.request.POST[x] for x in self.request.POST}

        username = self.request.get('username', None)
        if username:

            account = models.Account.all().filter("username =", username)[0]

            if 'given_name' in keys:
                account.given_name = keys['given_name']
            if 'ssn' in keys:
                account.ssn = keys['ssn']
            if 'username' in keys:
                account.username = keys['username']
            if 'password' in keys:
                account.password = keys['password']

            account.save()

        self.redirect('/profile')



class delete_employee(BaseHandler):
    @user_required
    def get(self, employee_key):
        key = str(urllib.unquote(employee_key))
        fired = models.Account.all().filter('key =', key).fetch(1)[0]
        fired.delete()
        self.redirect('/directory')


class view_customers(BaseHandler):
    @user_required
    def get(self):
        context = utils.get_context(self.auth)

        if context['is_admin']:
            customer_query = models.Account.all().filter('is_customer =', True)
            customers = customer_query.fetch(1000)
            context['customers'] = customers
            path = os.path.join(os.path.dirname(__file__),
                'templates/customers.html')
            self.response.out.write(template.render(path, context))

        else:
            path = os.path.join(os.path.dirname(__file__),
                'templates/error_no_permission.html')
            self.response.out.write(template.render(path, context))


class apply(BaseHandler):
    def get(self):
        context = utils.get_context(self.auth)
        upload_url = blobstore.create_upload_url('/upload')
        upload_url = upload_url.replace('http://localhost:8080', self.request.get('host'))
        context['upload_url'] = upload_url
        path = os.path.join(os.path.dirname(__file__), 'templates/apply.html')
        self.response.out.write(template.render(path, context))


class resume_upload(blobstore_handlers.BlobstoreUploadHandler):
    def post(self):
        upload_files = self.get_uploads('file')
        blob_info = upload_files[0]
        given_name = self.request.POST.get('given_name', None)
        surname = self.request.POST.get('surname', None)
        resume = models.Resume(blob=str(blob_info.key()),
                               given_name=given_name,
                               surname=surname)
        resume.save()
        self.redirect('/thanks')

class thanks(BaseHandler):
    def get(self):
        context = utils.get_context(self.auth)
        path = os.path.join(os.path.dirname(__file__), 'templates/thanks.html')
        self.response.out.write(template.render(path, context))


class resume_download(blobstore_handlers.BlobstoreDownloadHandler):
    @user_required
    def get(self, blob_key):
        blob_key = str(urllib.unquote(blob_key))
        if not blobstore.get(blob_key):
            self.error(404)
        else:
            self.send_blob(blobstore.BlobInfo.get(blob_key), save_as=True)


class resume_delete(BaseHandler):
    @user_required
    def get(self, blob_key):
        key = str(urllib.unquote(blob_key))
        remove = models.Resume.all().filter('blob =', key).fetch(1)[0]
        if remove:
            remove.delete()
            self.redirect('/resumes')


class view_resumes(BaseHandler):
    @user_required
    def get(self):
        context = utils.get_context(self.auth)
        resumes = models.Resume.all().fetch(10000)
        context['resumes'] = resumes
        path = os.path.join(os.path.dirname(__file__),
                            'templates/view_resumes.html')
        self.response.out.write(template.render(path, context))


class login(BaseHandler):
    def post(self):
        username = self.request.POST.get('username', None)
        password = self.request.POST.get('password', None)

        try:
            user = self.auth.get_user_by_password(username, password, False, True, True)

            # Fetch the account info from the datastore and update the 
            # auth store for the given user (so they have the most up to date
            # information about who is an admin)
            acct_query = models.Account.all().filter('username =', username)
            account = acct_query.fetch(1)
            if account:
                account = account[0]
                acct = self.auth.store.user_model.get_by_auth_id(account.username)
                acct.is_employee = account.is_employee
                acct.is_admin = account.is_admin
                acct.put()
        except auth.InvalidPasswordError, e:
            logging.warning(e)
            self.redirect('/invalid_password')
        except auth.InvalidAuthIdError, e:
            logging.warning(e)
            self.redirect('/register')
            # Returns error message to self.response.write in the BaseHandler.dispatcher
            # Currently no message is attached to the exceptions

        self.redirect('/')

class logout(BaseHandler):
    def post(self):
		current_session = self.auth.get_user_by_session()
		self.auth.unset_session()

		self.redirect('/')


# I am testing a new authentication system that should be better than the
# one I have now.  I have it mostly set up, but I need to either figure out
# how to store user info on the new user model, or some other way to securely
# handle user authentication.  Remove this later.  -- Michael
class test(BaseHandler):
    @user_required
    def get(self):
        context = utils.get_context(auth.get_auth())

        #
        current_session = self.auth.get_user_by_session()
        logging.error(current_session);
        new_user_object = self.auth.store.user_model.get_by_auth_token(current_session['user_id'], current_session['token'])[0]
        logging.error(new_user_object);
        username = new_user_object.auth_ids[0]
        old_user_object = models.Account.all().filter('username =', username).fetch(1)[0].__dict__['_entity']

        if 'user' in self.request.GET:
            new_user_object = self.auth.store.user_model.get_by_auth_id(self.request.GET['user'])
            old_user_object = models.Account.all().filter('username =', self.request.GET['user']).fetch(1)[0].__dict__['_entity']
            username = new_user_object.auth_ids[0]


        context['current_session'] = current_session
        context['new_user_object'] = new_user_object
        context['user'] = username
        context['old_user_object'] = old_user_object

        path = os.path.join(os.path.dirname(__file__),
            'templates/auth_test.html')
        self.response.out.write(template.render(path, context))

config = {}
config['webapp2_extras.sessions'] = {
    'secret_key': 'some-secret-key',
}

app = webapp2.WSGIApplication([('/', MainHandler),
                                ('/directory', view_directory),
                                ('/apply', apply),
                                ('/resumes', view_resumes),
                                ('/resumes/([^/]+)?', resume_download),
                                ('/resume/delete/([^/]+)?', resume_delete),
                                ('/upload', resume_upload),
                                ('/login', login),
                                ('/logout', logout),
                                ('/test', test),
                                ('/edit', edit_employee),
                                ('/thanks', thanks),
                                ('/profile', edit_profile),
                                ('/delete_employee/([^/]+)?', delete_employee)],
                              debug=True, config=config)


