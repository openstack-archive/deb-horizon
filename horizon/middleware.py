# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
# Copyright 2012 Nebula, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
"""
Middleware provided and used by Horizon.
"""

import json
import logging

from django import http
from django import shortcuts
from django.conf import settings
from django.contrib import messages as django_messages
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.views import redirect_to_login
from django.utils import timezone
from django.utils.encoding import iri_to_uri

from horizon import exceptions


LOG = logging.getLogger(__name__)


class HorizonMiddleware(object):
    """ The main Horizon middleware class. Required for use of Horizon. """

    def process_request(self, request):
        """ Adds data necessary for Horizon to function to the request. """
        # Activate timezone handling
        tz = request.session.get('django_timezone')
        if tz:
            timezone.activate(tz)

        request.horizon = {'dashboard': None,
                           'panel': None,
                           'async_messages': []}

    def process_exception(self, request, exception):
        """
        Catches internal Horizon exception classes such as NotAuthorized,
        NotFound and Http302 and handles them gracefully.
        """
        if isinstance(exception, (exceptions.NotAuthorized,
                                  exceptions.NotAuthenticated)):
            auth_url = settings.LOGIN_URL
            next_url = iri_to_uri(request.get_full_path())
            if next_url != auth_url:
                field_name = REDIRECT_FIELD_NAME
            else:
                field_name = None
            login_url = request.build_absolute_uri(auth_url)
            response = redirect_to_login(next_url, login_url=login_url,
                                         redirect_field_name=field_name)

            # TODO(gabriel): Find a way to display an appropriate message to
            # the user *on* the login form...
            if request.is_ajax():
                response_401 = http.HttpResponse(status=401)
                response_401['X-Horizon-Location'] = response['location']
                return response_401
            return response

        # If an internal "NotFound" error gets this far, return a real 404.
        if isinstance(exception, exceptions.NotFound):
            raise http.Http404(exception)

        if isinstance(exception, exceptions.Http302):
            # TODO(gabriel): Find a way to display an appropriate message to
            # the user *on* the login form...
            return shortcuts.redirect(exception.location)

    def process_response(self, request, response):
        """
        Convert HttpResponseRedirect to HttpResponse if request is via ajax
        to allow ajax request to redirect url
        """
        if request.is_ajax():
            queued_msgs = request.horizon['async_messages']
            if type(response) == http.HttpResponseRedirect:
                # Drop our messages back into the session as per usual so they
                # don't disappear during the redirect. Not that we explicitly
                # use django's messages methods here.
                for tag, message, extra_tags in queued_msgs:
                    getattr(django_messages, tag)(request, message, extra_tags)
                redirect_response = http.HttpResponse()
                redirect_response['X-Horizon-Location'] = response['location']
                return redirect_response
            if queued_msgs:
                # TODO(gabriel): When we have an async connection to the
                # client (e.g. websockets) this should be pushed to the
                # socket queue rather than being sent via a header.
                # The header method has notable drawbacks (length limits,
                # etc.) and is not meant as a long-term solution.
                response['X-Horizon-Messages'] = json.dumps(queued_msgs)
        return response
