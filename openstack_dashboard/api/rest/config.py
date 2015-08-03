# Copyright 2015 IBM Corp.
# Copyright 2015, Hewlett-Packard Development Company, L.P.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from django.conf import settings
from django.views import generic

from openstack_dashboard.api.rest import urls
from openstack_dashboard.api.rest import utils as rest_utils


# settings that we allow to be retrieved via REST API
# these settings are available to the client and are not secured.
# *** THEY SHOULD BE TREATED WITH EXTREME CAUTION ***
settings_required = getattr(settings, 'REST_API_REQUIRED_SETTINGS', [])
settings_additional = getattr(settings, 'REST_API_ADDITIONAL_SETTINGS', [])

settings_allowed = settings_required + settings_additional


@urls.register
class Settings(generic.View):
    """API for retrieving settings.

    This API returns read-only settings values.
    This configuration object can be fetched as needed.
    Examples of settings: OPENSTACK_HYPERVISOR_FEATURES
    """
    url_regex = r'settings/$'

    @rest_utils.ajax()
    def get(self, request):
        return {k: getattr(settings, k, None) for k in settings_allowed}
