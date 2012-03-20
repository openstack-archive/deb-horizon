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

import logging

from django import http
from django import shortcuts

from django.core.urlresolvers import reverse
from django.contrib import messages
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.utils.encoding import iri_to_uri

from horizon import exceptions
from horizon import users


LOG = logging.getLogger(__name__)


class HorizonMiddleware(object):
    """ The main Horizon middleware class. Required for use of Horizon. """

    def process_request(self, request):
        """ Adds data necessary for Horizon to function to the request.

        Adds the current "active" :class:`~horizon.Dashboard` and
        :class:`~horizon.Panel` to ``request.horizon``.

        Adds a :class:`~horizon.users.User` object to ``request.user``.
        """
        request.__class__.user = users.LazyUser()
        request.horizon = {'dashboard': None, 'panel': None}

    def process_exception(self, request, exception):
        """
        Catches internal Horizon exception classes such as NotAuthorized,
        NotFound and Http302 and handles them gracefully.
        """
        if isinstance(exception, exceptions.NotAuthorized):
            auth_url = reverse("horizon:auth_login")
            next_url = iri_to_uri(request.get_full_path())
            if next_url != auth_url:
                param = "?%s=%s" % (REDIRECT_FIELD_NAME, next_url)
                redirect_to = "".join((auth_url, param))
            else:
                redirect_to = auth_url
            messages.error(request, unicode(exception))
            if request.is_ajax():
                response_401 = http.HttpResponse(status=401)
                response_401["REDIRECT_URL"] = redirect_to
                return response_401
            return shortcuts.redirect(redirect_to)

        # If an internal "NotFound" error gets this far, return a real 404.
        if isinstance(exception, exceptions.NotFound):
            raise http.Http404(exception)

        if isinstance(exception, exceptions.Http302):
            if exception.message:
                messages.error(request, exception.message)
            return shortcuts.redirect(exception.location)
