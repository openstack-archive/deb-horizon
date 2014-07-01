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

import logging

from django.utils.datastructures import SortedDict
from django.utils.http import urlencode
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions

from novaclient import exceptions as nova_exception

from openstack_dashboard import api

LOG = logging.getLogger(__name__)

CONSOLES = SortedDict([('VNC', api.nova.server_vnc_console),
                       ('SPICE', api.nova.server_spice_console),
                       ('RDP', api.nova.server_rdp_console)])


def get_console(request, console_type, instance):
    """Get a console url based on console type."""
    if console_type == 'AUTO':
        check_consoles = CONSOLES
    else:
        try:
            check_consoles = {'console_type': CONSOLES[console_type]}
        except KeyError:
            msg = _('Console type "%s" not supported.') % console_type
            LOG.error(msg)
            raise exceptions.NotAvailable(msg)

    for api_call in check_consoles.values():
        try:
            console = api_call(request, instance.id)
        #if not supported don't log it to avoid lot of errors
        #in case of AUTO
        except nova_exception.HTTPNotImplemented:
            continue
        except Exception as e:
            LOG.exception(e)
            continue

        console_url = "%s&%s(%s)" % (
                      console.url,
                      urlencode({'title': getattr(instance, "name", "")}),
                      instance.id)
        return console_url

    raise exceptions.NotAvailable(_('No available console found.'))
