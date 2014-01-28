# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2013 Hewlett-Packard Development Company, L.P.
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

from django.core.urlresolvers import reverse
from django.core.urlresolvers import reverse_lazy
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import tables
from horizon.utils import memoized

from openstack_dashboard import api

from openstack_dashboard.dashboards.admin.groups import constants
from openstack_dashboard.dashboards.admin.groups \
    import forms as project_forms
from openstack_dashboard.dashboards.admin.groups \
    import tables as project_tables


class IndexView(tables.DataTableView):
    table_class = project_tables.GroupsTable
    template_name = constants.GROUPS_INDEX_VIEW_TEMPLATE

    def get_data(self):
        groups = []
        domain_context = self.request.session.get('domain_context', None)
        try:
            groups = api.keystone.group_list(self.request,
                                             domain=domain_context)
        except Exception:
            exceptions.handle(self.request,
                              _('Unable to retrieve group list.'))
        return groups


class CreateView(forms.ModalFormView):
    form_class = project_forms.CreateGroupForm
    template_name = constants.GROUPS_CREATE_VIEW_TEMPLATE
    success_url = reverse_lazy(constants.GROUPS_INDEX_URL)


class UpdateView(forms.ModalFormView):
    form_class = project_forms.UpdateGroupForm
    template_name = constants.GROUPS_UPDATE_VIEW_TEMPLATE
    success_url = reverse_lazy(constants.GROUPS_INDEX_URL)

    @memoized.memoized_method
    def get_object(self):
        try:
            return api.keystone.group_get(self.request,
                self.kwargs['group_id'])
        except Exception:
            redirect = reverse(constants.GROUPS_INDEX_URL)
            exceptions.handle(self.request,
                              _('Unable to update group.'),
                              redirect=redirect)

    def get_context_data(self, **kwargs):
        context = super(UpdateView, self).get_context_data(**kwargs)
        context['group'] = self.get_object()
        return context

    def get_initial(self):
        group = self.get_object()
        return {'group_id': group.id,
                'name': group.name,
                'description': group.description}


class GroupManageMixin(object):
    @memoized.memoized_method
    def _get_group(self):
        group_id = self.kwargs['group_id']
        return api.keystone.group_get(self.request, group_id)

    @memoized.memoized_method
    def _get_group_members(self):
        group_id = self.kwargs['group_id']
        return api.keystone.user_list(self.request, group=group_id)

    @memoized.memoized_method
    def _get_group_non_members(self):
        domain_id = self._get_group().domain_id
        all_users = api.keystone.user_list(self.request,
                                           domain=domain_id)
        group_members = self._get_group_members()
        group_member_ids = [user.id for user in group_members]
        return filter(lambda u: u.id not in group_member_ids, all_users)


class ManageMembersView(GroupManageMixin, tables.DataTableView):
    table_class = project_tables.GroupMembersTable
    template_name = constants.GROUPS_MANAGE_VIEW_TEMPLATE

    def get_context_data(self, **kwargs):
        context = super(ManageMembersView, self).get_context_data(**kwargs)
        context['group'] = self._get_group()
        return context

    def get_data(self):
        group_members = []
        try:
            group_members = self._get_group_members()
        except Exception:
            exceptions.handle(self.request,
                              _('Unable to retrieve group users.'))
        return group_members


class NonMembersView(GroupManageMixin, forms.ModalFormMixin,
                     tables.DataTableView):
    template_name = constants.GROUPS_ADD_MEMBER_VIEW_TEMPLATE
    ajax_template_name = constants.GROUPS_ADD_MEMBER_AJAX_VIEW_TEMPLATE
    table_class = project_tables.GroupNonMembersTable

    def get_context_data(self, **kwargs):
        context = super(NonMembersView, self).get_context_data(**kwargs)
        context['group'] = self._get_group()
        return context

    def get_data(self):
        group_non_members = []
        try:
            group_non_members = self._get_group_non_members()
        except Exception:
            exceptions.handle(self.request,
                              _('Unable to retrieve users.'))
        return group_non_members
