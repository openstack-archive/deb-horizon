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

import logging

from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms

from openstack_dashboard import api
from openstack_dashboard.dashboards.project.networks.ports \
    import views as project_views

from .forms import CreatePort, UpdatePort

LOG = logging.getLogger(__name__)


class CreateView(forms.ModalFormView):
    form_class = CreatePort
    template_name = 'admin/networks/ports/create.html'
    success_url = 'horizon:admin:networks:detail'
    failure_url = 'horizon:admin:networks:detail'

    def get_success_url(self):
        return reverse(self.success_url,
                       args=(self.kwargs['network_id'],))

    def get_object(self):
        if not hasattr(self, "_object"):
            try:
                network_id = self.kwargs["network_id"]
                self._object = api.quantum.network_get(self.request,
                                                       network_id)
            except:
                redirect = reverse(self.failure_url,
                                   args=(self.kwargs['network_id'],))
                msg = _("Unable to retrieve network.")
                exceptions.handle(self.request, msg, redirect=redirect)
        return self._object

    def get_context_data(self, **kwargs):
        context = super(CreateView, self).get_context_data(**kwargs)
        context['network'] = self.get_object()
        return context

    def get_initial(self):
        network = self.get_object()
        return {"network_id": self.kwargs['network_id'],
                "network_name": network.name}


class UpdateView(project_views.UpdateView):
    form_class = UpdatePort
    template_name = 'admin/networks/ports/update.html'
    context_object_name = 'port'
    success_url = 'horizon:admin:networks:detail'
