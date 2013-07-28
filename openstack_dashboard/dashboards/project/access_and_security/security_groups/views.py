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
Views for managing instances.
"""
import logging

from django.core.urlresolvers import reverse
from django.core.urlresolvers import reverse_lazy
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import tables

from openstack_dashboard import api
from openstack_dashboard.utils.filters import get_int_or_uuid

from openstack_dashboard.dashboards.project.access_and_security.\
    security_groups.forms import AddRule
from openstack_dashboard.dashboards.project.access_and_security.\
    security_groups.forms import CreateGroup
from openstack_dashboard.dashboards.project.access_and_security.\
    security_groups.tables import RulesTable


LOG = logging.getLogger(__name__)


class DetailView(tables.DataTableView):
    table_class = RulesTable
    template_name = 'project/access_and_security/security_groups/detail.html'

    def _get_data(self):
        if not hasattr(self, '_sg'):
            sg_id = get_int_or_uuid(self.kwargs['security_group_id'])
            try:
                self._sg = api.network.security_group_get(self.request, sg_id)
            except:
                redirect = reverse('horizon:project:access_and_security:index')
                exceptions.handle(self.request,
                                  _('Unable to retrieve security group.'),
                                  redirect=redirect)
        return self._sg

    def get_data(self):
        return self._get_data().rules

    def get_context_data(self, **kwargs):
        context = super(DetailView, self).get_context_data(**kwargs)
        context["security_group"] = self._get_data()
        return context


class AddRuleView(forms.ModalFormView):
    form_class = AddRule
    template_name = 'project/access_and_security/security_groups/add_rule.html'

    def get_success_url(self):
        sg_id = self.kwargs['security_group_id']
        return reverse("horizon:project:access_and_security:"
                       "security_groups:detail", args=[sg_id])

    def get_context_data(self, **kwargs):
        context = super(AddRuleView, self).get_context_data(**kwargs)
        context["security_group_id"] = self.kwargs['security_group_id']
        return context

    def get_initial(self):
        return {'id': self.kwargs['security_group_id']}

    def get_form_kwargs(self):
        kwargs = super(AddRuleView, self).get_form_kwargs()

        try:
            groups = api.network.security_group_list(self.request)
        except:
            groups = []
            exceptions.handle(self.request,
                              _("Unable to retrieve security groups."))

        security_groups = []
        for group in groups:
            if group.id == get_int_or_uuid(self.kwargs['security_group_id']):
                security_groups.append((group.id,
                                        _("%s (current)") % group.name))
            else:
                security_groups.append((group.id, group.name))
        kwargs['sg_list'] = security_groups
        return kwargs


class CreateView(forms.ModalFormView):
    form_class = CreateGroup
    template_name = 'project/access_and_security/security_groups/create.html'
    success_url = reverse_lazy('horizon:project:access_and_security:index')
