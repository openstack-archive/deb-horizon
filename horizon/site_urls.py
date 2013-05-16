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

from django.views.generic import TemplateView
from django.conf.urls.defaults import patterns, url, include
from django.conf import settings


urlpatterns = patterns('horizon.views',
    url(r'home/$', 'user_home', name='user_home')
)

# Client-side i18n URLconf.
urlpatterns += patterns('',
    url(r'^i18n/js/(?P<packages>\S+?)/$',
        'django.views.i18n.javascript_catalog',
        name='jsi18n'),
    url(r'^i18n/setlang/$',
        'django.views.i18n.set_language',
        name="set_language"),
    url(r'^i18n/', include('django.conf.urls.i18n'))
)

if settings.DEBUG:
    urlpatterns += patterns('',
        url(r'^qunit/$',
            TemplateView.as_view(template_name="horizon/qunit.html"),
            name='qunit_tests'))
