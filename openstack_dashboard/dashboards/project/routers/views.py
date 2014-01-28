# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012,  Nachi Ueno,  NTT MCL,  Inc.
# Copyright 2013,  Big Switch Networks, Inc.
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
Views for managing Neutron Routers.
"""

from django.core.urlresolvers import reverse_lazy
from django.utils.datastructures import SortedDict
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import tables
from horizon import tabs
from horizon.utils import memoized
from openstack_dashboard import api
from openstack_dashboard.dashboards.project.routers\
    import forms as project_forms
from openstack_dashboard.dashboards.project.routers import tables as rtables
from openstack_dashboard.dashboards.project.routers import tabs as rdtabs


class IndexView(tables.DataTableView):
    table_class = rtables.RoutersTable
    template_name = 'project/routers/index.html'

    def _get_routers(self, search_opts=None):
        try:
            tenant_id = self.request.user.tenant_id
            routers = api.neutron.router_list(self.request,
                                              tenant_id=tenant_id,
                                              search_opts=search_opts)
        except Exception:
            routers = []
            exceptions.handle(self.request,
                              _('Unable to retrieve router list.'))

        ext_net_dict = self._list_external_networks()

        for r in routers:
            r.set_id_as_name_if_empty()
            self._set_external_network(r, ext_net_dict)
        return routers

    def get_data(self):
        routers = self._get_routers()
        return routers

    def _list_external_networks(self):
        try:
            search_opts = {'router:external': True}
            ext_nets = api.neutron.network_list(self.request,
                                                **search_opts)
            for ext_net in ext_nets:
                ext_net.set_id_as_name_if_empty()
            ext_net_dict = SortedDict((n['id'], n.name) for n in ext_nets)
        except Exception as e:
            msg = _('Unable to retrieve a list of external networks "%s".') % e
            exceptions.handle(self.request, msg)
            ext_net_dict = {}
        return ext_net_dict

    def _set_external_network(self, router, ext_net_dict):
        gateway_info = router.external_gateway_info
        if gateway_info:
            ext_net_id = gateway_info['network_id']
            if ext_net_id in ext_net_dict:
                gateway_info['network'] = ext_net_dict[ext_net_id]
            else:
                msg = _('External network "%s" not found.') % (ext_net_id)
                exceptions.handle(self.request, msg)


class DetailView(tabs.TabbedTableView):
    tab_group_class = rdtabs.RouterDetailTabs
    template_name = 'project/routers/detail.html'
    failure_url = reverse_lazy('horizon:project:routers:index')

    @memoized.memoized_method
    def _get_data(self):
        try:
            router_id = self.kwargs['router_id']
            router = api.neutron.router_get(self.request, router_id)
            router.set_id_as_name_if_empty(length=0)
        except Exception:
            msg = _('Unable to retrieve details for router "%s".') \
                % (router_id)
            exceptions.handle(self.request, msg, redirect=self.failure_url)
        if router.external_gateway_info:
            ext_net_id = router.external_gateway_info['network_id']
            try:
                ext_net = api.neutron.network_get(self.request, ext_net_id,
                                                  expand_subnet=False)
                ext_net.set_id_as_name_if_empty(length=0)
                router.external_gateway_info['network'] = ext_net.name
            except Exception:
                msg = _('Unable to retrieve an external network "%s".') \
                    % (ext_net_id)
                exceptions.handle(self.request, msg)
                router.external_gateway_info['network'] = ext_net_id
        return router

    def get_context_data(self, **kwargs):
        context = super(DetailView, self).get_context_data(**kwargs)
        context["router"] = self._get_data()
        return context

    def get(self, request, *args, **kwargs):
        router = self._get_data()
        self.kwargs['router'] = router
        return super(DetailView, self).get(request, *args, **kwargs)


class CreateView(forms.ModalFormView):
    form_class = project_forms.CreateForm
    template_name = 'project/routers/create.html'
    success_url = reverse_lazy("horizon:project:routers:index")
