# vim: tabstop=4 shiftwidth=4 softtabstop=4

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
Views for managing Nova volumes.
"""

import logging

from django import shortcuts
from django.core.urlresolvers import reverse_lazy
from django.utils.translation import ugettext_lazy as _
from django.utils.datastructures import SortedDict

from horizon import api
from horizon import exceptions
from horizon import forms
from horizon import tables
from horizon import tabs
from .forms import CreateForm, AttachForm, CreateSnapshotForm
from .tables import AttachmentsTable, VolumesTable
from .tabs import VolumeDetailTabs


LOG = logging.getLogger(__name__)


class IndexView(tables.DataTableView):
    table_class = VolumesTable
    template_name = 'nova/volumes/index.html'

    def get_data(self):
        # Gather our volumes
        try:
            volumes = api.volume_list(self.request)
        except:
            volumes = []
            exceptions.handle(self.request,
                              _('Unable to retrieve volume list.'))
        try:
            instance_list = api.server_list(self.request)
        except:
            instance_list = []
            exceptions.handle(self.request,
                              _("Unable to retrieve volume/instance "
                                "attachment information"))

        instances = SortedDict([(inst.id, inst) for inst in instance_list])
        for volume in volumes:
            # It is possible to create a volume with no name through the
            # EC2 API, use the ID in those cases.
            if not volume.display_name:
                volume.display_name = volume.id

            for att in volume.attachments:
                server_id = att.get('server_id', None)
                att['instance'] = instances.get(server_id, None)
        return volumes


class DetailView(tabs.TabView):
    tab_group_class = VolumeDetailTabs
    template_name = 'nova/volumes/detail.html'


class CreateView(forms.ModalFormView):
    form_class = CreateForm
    template_name = 'nova/volumes/create.html'
    success_url = reverse_lazy("horizon:nova:volumes:index")

    def get_context_data(self, **kwargs):
        context = super(CreateView, self).get_context_data(**kwargs)
        try:
            context['usages'] = api.tenant_quota_usages(self.request)
        except:
            exceptions.handle(self.request)
        return context


class CreateSnapshotView(forms.ModalFormView):
    form_class = CreateSnapshotForm
    template_name = 'nova/volumes/create_snapshot.html'
    success_url = reverse_lazy("horizon:nova:images_and_snapshots:index")

    def get_context_data(self, **kwargs):
        context = super(CreateSnapshotView, self).get_context_data(**kwargs)
        context['volume_id'] = self.kwargs['volume_id']
        return context

    def get_initial(self):
        return {'volume_id': self.kwargs["volume_id"]}


class EditAttachmentsView(tables.DataTableView, forms.ModalFormView):
    table_class = AttachmentsTable
    form_class = AttachForm
    template_name = 'nova/volumes/attach.html'
    success_url = reverse_lazy("horizon:nova:volumes:index")

    def get_object(self):
        if not hasattr(self, "_object"):
            volume_id = self.kwargs['volume_id']
            try:
                self._object = api.volume_get(self.request, volume_id)
            except:
                self._object = None
                exceptions.handle(self.request,
                                  _('Unable to retrieve volume information.'))
        return self._object

    def get_data(self):
        try:
            volumes = self.get_object()
            attachments = [att for att in volumes.attachments if att]
        except:
            attachments = []
            exceptions.handle(self.request,
                              _('Unable to retrieve volume information.'))
        return attachments

    def get_initial(self):
        try:
            instances = api.nova.server_list(self.request)
        except:
            instances = []
            exceptions.handle(self.request,
                              _("Unable to retrieve attachment information."))
        return {'volume': self.get_object(),
                'instances': instances}

    def get_form(self):
        if not hasattr(self, "_form"):
            form_class = self.get_form_class()
            self._form = super(EditAttachmentsView, self).get_form(form_class)
        return self._form

    def get_context_data(self, **kwargs):
        context = super(EditAttachmentsView, self).get_context_data(**kwargs)
        context['form'] = self.get_form()
        volume = self.get_object()
        if volume and volume.status == 'available':
            context['show_attach'] = True
        else:
            context['show_attach'] = False
        context['volume'] = volume
        if self.request.is_ajax():
            context['hide'] = True
        return context

    def get(self, request, *args, **kwargs):
        # Table action handling
        handled = self.construct_tables()
        if handled:
            return handled
        return self.render_to_response(self.get_context_data(**kwargs))

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.get(request, *args, **kwargs)
