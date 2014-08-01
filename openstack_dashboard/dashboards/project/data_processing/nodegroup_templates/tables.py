# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from django import template

import logging

from django.utils.translation import ugettext_lazy as _

from horizon import tables
from openstack_dashboard.api import sahara as saharaclient

LOG = logging.getLogger(__name__)


class CreateNodegroupTemplate(tables.LinkAction):
    name = "create"
    verbose_name = _("Create Template")
    url = ("horizon:project:data_processing.nodegroup_templates:"
           "create-nodegroup-template")
    classes = ("ajax-modal", "btn-create", "create-nodegrouptemplate-btn")


class ConfigureNodegroupTemplate(tables.LinkAction):
    name = "configure"
    verbose_name = _("Configure Template")
    url = ("horizon:project:data_processing.nodegroup_templates:"
           "configure-nodegroup-template")
    classes = ("ajax-modal", "btn-create", "configure-nodegrouptemplate-btn")
    attrs = {"style": "display: none"}


class CopyTemplate(tables.LinkAction):
    name = "copy"
    verbose_name = _("Copy Template")
    url = "horizon:project:data_processing.nodegroup_templates:copy"
    classes = ("ajax-modal", )


class DeleteTemplate(tables.BatchAction):
    name = "delete_nodegroup_template"
    verbose_name = _("Delete")
    classes = ("btn-terminate", "btn-danger")

    action_present = _("Delete")
    action_past = _("Deleted")
    data_type_singular = _("Template")
    data_type_plural = _("Templates")

    def action(self, request, template_id):
        saharaclient.nodegroup_template_delete(request, template_id)


def render_processes(nodegroup_template):
    template_name = (
        'project/data_processing.nodegroup_templates/_processes_list.html')
    context = {"processes": nodegroup_template.node_processes}
    return template.loader.render_to_string(template_name, context)


class NodegroupTemplatesTable(tables.DataTable):
    name = tables.Column("name",
        verbose_name=_("Name"),
        link=("horizon:project:data_processing.nodegroup_templates:details"))
    plugin_name = tables.Column("plugin_name",
                                verbose_name=_("Plugin"))
    hadoop_version = tables.Column("hadoop_version",
                                   verbose_name=_("Hadoop Version"))
    node_processes = tables.Column(render_processes,
                                   verbose_name=_("Node Processes"))

    class Meta:
        name = "nodegroup_templates"
        verbose_name = _("Node Group Templates")
        table_actions = (CreateNodegroupTemplate,
                         ConfigureNodegroupTemplate,
                         DeleteTemplate)
        row_actions = (CopyTemplate,
                       DeleteTemplate,)
