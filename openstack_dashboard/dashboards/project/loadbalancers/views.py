# vim: tabstop=4 shiftwidth=4 softtabstop=4

#    Copyright 2013, Big Switch Networks, Inc.
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

from django.core.urlresolvers import reverse_lazy
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import tabs
from horizon import workflows

import logging

from openstack_dashboard import api
from openstack_dashboard.dashboards.project.loadbalancers.forms import \
    UpdateMember
from openstack_dashboard.dashboards.project.loadbalancers.forms import \
    UpdateMonitor
from openstack_dashboard.dashboards.project.loadbalancers.forms import \
    UpdatePool
from openstack_dashboard.dashboards.project.loadbalancers.forms import \
    UpdateVip
from openstack_dashboard.dashboards.project.loadbalancers.tabs import \
    LoadBalancerTabs
from openstack_dashboard.dashboards.project.loadbalancers.tabs import \
    MemberDetailsTabs
from openstack_dashboard.dashboards.project.loadbalancers.tabs import \
    MonitorDetailsTabs
from openstack_dashboard.dashboards.project.loadbalancers.tabs import \
    PoolDetailsTabs
from openstack_dashboard.dashboards.project.loadbalancers.tabs import \
    VipDetailsTabs
from openstack_dashboard.dashboards.project.loadbalancers.workflows import \
    AddMember
from openstack_dashboard.dashboards.project.loadbalancers.workflows import \
    AddMonitor
from openstack_dashboard.dashboards.project.loadbalancers.workflows import \
    AddPMAssociation
from openstack_dashboard.dashboards.project.loadbalancers.workflows import \
    AddPool
from openstack_dashboard.dashboards.project.loadbalancers.workflows import \
    AddVip
from openstack_dashboard.dashboards.project.loadbalancers.workflows import \
    DeletePMAssociation

import re

LOG = logging.getLogger(__name__)


class IndexView(tabs.TabView):
    tab_group_class = (LoadBalancerTabs)
    template_name = 'project/loadbalancers/details_tabs.html'

    def post(self, request, *args, **kwargs):
        obj_ids = request.POST.getlist('object_ids')
        action = request.POST['action']
        m = re.search('.delete([a-z]+)', action).group(1)
        if obj_ids == []:
            obj_ids.append(re.search('([0-9a-z-]+)$', action).group(1))
        if m == 'monitor':
            for obj_id in obj_ids:
                try:
                    api.lbaas.pool_health_monitor_delete(request, obj_id)
                except:
                    exceptions.handle(request,
                                      _('Unable to delete monitor.'))
        if m == 'pool':
            for obj_id in obj_ids:
                try:
                    api.lbaas.pool_delete(request, obj_id)
                except:
                    exceptions.handle(request,
                                      _('Must delete VIP first.'))
        if m == 'member':
            for obj_id in obj_ids:
                try:
                    api.lbaas.member_delete(request, obj_id)
                except:
                    exceptions.handle(request,
                                      _('Unable to delete member.'))
        if m == 'vip':
            for obj_id in obj_ids:
                try:
                    vip_id = api.lbaas.pool_get(request, obj_id).vip_id
                except:
                    exceptions.handle(request,
                                      _('Unable to locate VIP to delete.'))
                if vip_id is not None:
                    try:
                        api.lbaas.vip_delete(request, vip_id)
                    except:
                        exceptions.handle(request,
                                          _('Unable to delete VIP.'))
        return self.get(request, *args, **kwargs)


class AddPoolView(workflows.WorkflowView):
    workflow_class = AddPool

    def get_initial(self):
        initial = super(AddPoolView, self).get_initial()
        return initial


class AddVipView(workflows.WorkflowView):
    workflow_class = AddVip

    def get_context_data(self, **kwargs):
        context = super(AddVipView, self).get_context_data(**kwargs)
        return context

    def get_initial(self):
        initial = super(AddVipView, self).get_initial()
        initial['pool_id'] = self.kwargs['pool_id']
        try:
            pool = api.lbaas.pool_get(self.request, initial['pool_id'])
            initial['subnet'] = api.neutron.subnet_get(
                self.request, pool.subnet_id).cidr
        except:
            initial['subnet'] = ''
            msg = _('Unable to retrieve pool subnet.')
            exceptions.handle(self.request, msg)
        return initial


class AddMemberView(workflows.WorkflowView):
    workflow_class = AddMember

    def get_initial(self):
        initial = super(AddMemberView, self).get_initial()
        return initial


class AddMonitorView(workflows.WorkflowView):
    workflow_class = AddMonitor

    def get_initial(self):
        initial = super(AddMonitorView, self).get_initial()
        return initial


class PoolDetailsView(tabs.TabView):
    tab_group_class = (PoolDetailsTabs)
    template_name = 'project/loadbalancers/details_tabs.html'


class VipDetailsView(tabs.TabView):
    tab_group_class = (VipDetailsTabs)
    template_name = 'project/loadbalancers/details_tabs.html'


class MemberDetailsView(tabs.TabView):
    tab_group_class = (MemberDetailsTabs)
    template_name = 'project/loadbalancers/details_tabs.html'


class MonitorDetailsView(tabs.TabView):
    tab_group_class = (MonitorDetailsTabs)
    template_name = 'project/loadbalancers/details_tabs.html'


class UpdatePoolView(forms.ModalFormView):
    form_class = UpdatePool
    template_name = "project/loadbalancers/updatepool.html"
    context_object_name = 'pool'
    success_url = reverse_lazy("horizon:project:loadbalancers:index")

    def get_context_data(self, **kwargs):
        context = super(UpdatePoolView, self).get_context_data(**kwargs)
        context["pool_id"] = self.kwargs['pool_id']
        return context

    def _get_object(self, *args, **kwargs):
        if not hasattr(self, "_object"):
            pool_id = self.kwargs['pool_id']
            try:
                self._object = api.lbaas.pool_get(self.request, pool_id)
            except:
                redirect = self.success_url
                msg = _('Unable to retrieve pool details.')
                exceptions.handle(self.request, msg, redirect=redirect)
        return self._object

    def get_initial(self):
        pool = self._get_object()
        return {'name': pool['name'],
                'pool_id': pool['id'],
                'description': pool['description'],
                'lb_method': pool['lb_method'],
                'admin_state_up': pool['admin_state_up']}


class UpdateVipView(forms.ModalFormView):
    form_class = UpdateVip
    template_name = "project/loadbalancers/updatevip.html"
    context_object_name = 'vip'
    success_url = reverse_lazy("horizon:project:loadbalancers:index")

    def get_context_data(self, **kwargs):
        context = super(UpdateVipView, self).get_context_data(**kwargs)
        context["vip_id"] = self.kwargs['vip_id']
        return context

    def _get_object(self, *args, **kwargs):
        if not hasattr(self, "_object"):
            vip_id = self.kwargs['vip_id']
            try:
                self._object = api.lbaas.vip_get(self.request, vip_id)
            except:
                redirect = self.success_url
                msg = _('Unable to retrieve vip details.')
                exceptions.handle(self.request, msg, redirect=redirect)
        return self._object

    def get_initial(self):
        vip = self._get_object()
        stype = vip['session_persistence']
        if stype['type'] == 'APP_COOKIE':
            cookie = stype['cookie_name']
        else:
            cookie = ''

        return {'name': vip['name'],
                'vip_id': vip['id'],
                'description': vip['description'],
                'pool_id': vip['pool_id'],
                'session_persistence': vip['session_persistence']['type'],
                'cookie_name': cookie,
                'connection_limit': vip['connection_limit'],
                'admin_state_up': vip['admin_state_up']}


class UpdateMemberView(forms.ModalFormView):
    form_class = UpdateMember
    template_name = "project/loadbalancers/updatemember.html"
    context_object_name = 'member'
    success_url = reverse_lazy("horizon:project:loadbalancers:index")

    def get_context_data(self, **kwargs):
        context = super(UpdateMemberView, self).get_context_data(**kwargs)
        context["member_id"] = self.kwargs['member_id']
        return context

    def _get_object(self, *args, **kwargs):
        if not hasattr(self, "_object"):
            member_id = self.kwargs['member_id']
            try:
                self._object = api.lbaas.member_get(self.request, member_id)
            except:
                redirect = self.success_url
                msg = _('Unable to retrieve member details.')
                exceptions.handle(self.request, msg, redirect=redirect)
        return self._object

    def get_initial(self):
        member = self._get_object()
        return {'member_id': member['id'],
                'pool_id': member['pool_id'],
                'weight': member['weight'],
                'admin_state_up': member['admin_state_up']}


class UpdateMonitorView(forms.ModalFormView):
    form_class = UpdateMonitor
    template_name = "project/loadbalancers/updatemonitor.html"
    context_object_name = 'monitor'
    success_url = reverse_lazy("horizon:project:loadbalancers:index")

    def get_context_data(self, **kwargs):
        context = super(UpdateMonitorView, self).get_context_data(**kwargs)
        context["monitor_id"] = self.kwargs['monitor_id']
        return context

    def _get_object(self, *args, **kwargs):
        if not hasattr(self, "_object"):
            monitor_id = self.kwargs['monitor_id']
            try:
                self._object = api.lbaas.pool_health_monitor_get(
                                    self.request, monitor_id)
            except:
                redirect = self.success_url
                msg = _('Unable to retrieve health monitor details.')
                exceptions.handle(self.request, msg, redirect=redirect)
        return self._object

    def get_initial(self):
        monitor = self._get_object()
        return {'monitor_id': monitor['id'],
                'delay': monitor['delay'],
                'timeout': monitor['timeout'],
                'max_retries': monitor['max_retries'],
                'admin_state_up': monitor['admin_state_up']}


class AddPMAssociationView(workflows.WorkflowView):
    workflow_class = AddPMAssociation

    def get_initial(self):
        initial = super(AddPMAssociationView, self).get_initial()
        initial['pool_id'] = self.kwargs['pool_id']
        try:
            pool = api.lbaas.pool_get(self.request, initial['pool_id'])
            initial['pool_name'] = pool.name
            initial['pool_monitors'] = pool.health_monitors
        except:
            msg = _('Unable to retrieve pool.')
            exceptions.handle(self.request, msg)
        return initial


class DeletePMAssociationView(workflows.WorkflowView):
    workflow_class = DeletePMAssociation

    def get_initial(self):
        initial = super(DeletePMAssociationView, self).get_initial()
        initial['pool_id'] = self.kwargs['pool_id']
        try:
            pool = api.lbaas.pool_get(self.request, initial['pool_id'])
            initial['pool_name'] = pool.name
            initial['pool_monitors'] = pool.health_monitors
        except:
            msg = _('Unable to retrieve pool.')
            exceptions.handle(self.request, msg)
        return initial
