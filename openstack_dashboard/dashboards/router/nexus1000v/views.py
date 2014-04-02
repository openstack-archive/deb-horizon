# vim: tabstop=4 shiftwidth=4 softtabstop=4

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
#
# @author: Abishek Subramanian, Cisco Systems, Inc.
# @author: Sergey Sudakovich,   Cisco Systems, Inc.

import logging

from django.core import urlresolvers
from django.utils import datastructures
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import tables
from horizon import tabs
from horizon.utils import memoized

from openstack_dashboard import api

from openstack_dashboard.dashboards.router.nexus1000v \
    import forms as profileforms
from openstack_dashboard.dashboards.router.nexus1000v \
    import tables as profiletables


LOG = logging.getLogger(__name__)


def _get_tenant_list(request):
    tenants = []
    try:
        tenants, has_more = api.keystone.tenant_list(request)
    except Exception:
        msg = _('Unable to retrieve project information.')
        exceptions.handle(request, msg)

    return datastructures.SortedDict([(t.id, t) for t in tenants])


def _get_profiles(request, type_p):
    try:
        profiles = api.neutron.profile_list(request, type_p)
    except Exception:
        profiles = []
        msg = _('Network Profiles could not be retrieved.')
        exceptions.handle(request, msg)
    if profiles:
        # Set project name
        tenant_dict = _get_tenant_list(request)
        bindings = api.neutron.profile_bindings_list(request, type_p)
        bindings_dict = datastructures.SortedDict(
            [(b.profile_id, b.tenant_id) for b in bindings])
        for p in profiles:
            project_id = bindings_dict.get(p.id)
            project = tenant_dict.get(project_id)
            p.project_name = getattr(project, 'name', None)
    return profiles


class NetworkProfileIndexView(tables.DataTableView):
    table_class = profiletables.NetworkProfile
    template_name = 'router/nexus1000v/network_profile/index.html'

    def get_data(self):
        return _get_profiles(self.request, 'network')


class PolicyProfileIndexView(tables.DataTableView):
    table_class = profiletables.PolicyProfile
    template_name = 'router/nexus1000v/policy_profile/index.html'

    def get_data(self):
        return _get_profiles(self.request, 'policy')


class IndexTabGroup(tabs.TabGroup):
    slug = "group"
    tabs = (NetworkProfileIndexView, PolicyProfileIndexView,)


class IndexView(tables.MultiTableView):
    table_classes = (profiletables.NetworkProfile,
                     profiletables.PolicyProfile,)
    template_name = 'router/nexus1000v/index.html'

    def get_network_profile_data(self):
        return _get_profiles(self.request, 'network')

    def get_policy_profile_data(self):
        return _get_profiles(self.request, 'policy')


class CreateNetworkProfileView(forms.ModalFormView):
    form_class = profileforms.CreateNetworkProfile
    template_name = 'router/nexus1000v/create_network_profile.html'
    success_url = urlresolvers.reverse_lazy('horizon:router:nexus1000v:index')


class UpdateNetworkProfileView(forms.ModalFormView):
    form_class = profileforms.UpdateNetworkProfile
    template_name = 'router/nexus1000v/update_network_profile.html'
    context_object_name = 'network_profile'
    success_url = urlresolvers.reverse_lazy('horizon:router:nexus1000v:index')

    def get_context_data(self, **kwargs):
        context = super(UpdateNetworkProfileView,
                        self).get_context_data(**kwargs)
        context["profile_id"] = self.kwargs['profile_id']
        return context

    @memoized.memoized_method
    def _get_object(self, *args, **kwargs):
        profile_id = self.kwargs['profile_id']
        try:
            profile = api.neutron.profile_get(self.request,
                                                   profile_id)
            LOG.debug("Network Profile object=%s", profile)
            return profile
        except Exception:
            redirect = self.success_url
            msg = _('Unable to retrieve network profile details.')
            exceptions.handle(self.request, msg, redirect=redirect)

    def get_initial(self):
        profile = self._get_object()
        return {'profile_id': profile['id'],
                'name': profile['name'],
                'segment_range': profile['segment_range'],
                'segment_type': profile['segment_type'],
                'physical_network': profile['physical_network']}
