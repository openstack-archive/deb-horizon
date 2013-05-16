# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 NEC Corporation
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
Views for managing Quantum Subnets.
"""
import logging

from django.core.urlresolvers import reverse_lazy, reverse
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import tabs
from horizon import workflows

from openstack_dashboard import api
from .tabs import SubnetDetailTabs
from .workflows import CreateSubnet, UpdateSubnet


LOG = logging.getLogger(__name__)


class CreateView(workflows.WorkflowView):
    workflow_class = CreateSubnet
    template_name = 'project/networks/subnets/create.html'

    def get_object(self):
        if not hasattr(self, "_object"):
            try:
                network_id = self.kwargs["network_id"]
                self._object = api.quantum.network_get(self.request,
                                                       network_id)
                self._object.set_id_as_name_if_empty()
            except:
                redirect = reverse('horizon:project:networks:index')
                msg = _("Unable to retrieve network.")
                exceptions.handle(self.request, msg, redirect=redirect)
        return self._object

    def get_initial(self):
        network = self.get_object()
        return {"network_id": self.kwargs['network_id'],
                "network_name": network.name}


class UpdateView(workflows.WorkflowView):
    workflow_class = UpdateSubnet
    template_name = 'project/networks/subnets/update.html'

    def _get_object(self, *args, **kwargs):
        if not hasattr(self, "_object"):
            subnet_id = self.kwargs['subnet_id']
            try:
                self._object = api.quantum.subnet_get(self.request, subnet_id)
            except:
                redirect = reverse("horizon:project:networks:index")
                msg = _('Unable to retrieve subnet details')
                exceptions.handle(self.request, msg, redirect=redirect)
        return self._object

    def get_initial(self):
        initial = super(UpdateView, self).get_initial()

        subnet = self._get_object()

        initial['network_id'] = self.kwargs['network_id']
        initial['subnet_id'] = subnet['id']
        initial['subnet_name'] = subnet['name']

        for key in ('cidr', 'ip_version', 'enable_dhcp'):
            initial[key] = subnet[key]

        initial['gateway_ip'] = subnet['gateway_ip'] or ''
        initial['no_gateway'] = (subnet['gateway_ip'] is None)

        initial['dns_nameservers'] = '\n'.join(subnet['dns_nameservers'])
        pools = ['%s,%s' % (p['start'], p['end'])
                 for p in subnet['allocation_pools']]
        initial['allocation_pools'] = '\n'.join(pools)
        routes = ['%s,%s' % (r['destination'], r['nexthop'])
                 for r in subnet['host_routes']]
        initial['host_routes'] = '\n'.join(routes)

        return initial


class DetailView(tabs.TabView):
    tab_group_class = SubnetDetailTabs
    template_name = 'project/networks/subnets/detail.html'
