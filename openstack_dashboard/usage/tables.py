# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from django.core import urlresolvers
from django.template.defaultfilters import floatformat  # noqa
from django.template.defaultfilters import timesince  # noqa
from django.utils.translation import ugettext_lazy as _

from horizon import tables
from horizon.templatetags import sizeformat
from horizon.utils import filters


class CSVSummary(tables.LinkAction):
    name = "csv_summary"
    verbose_name = _("Download CSV Summary")
    classes = ("btn-download",)

    def get_link_url(self, usage=None):
        return self.table.kwargs['usage'].csv_link()


class BaseUsageTable(tables.DataTable):
    vcpus = tables.Column('vcpus', verbose_name=_("VCPUs"))
    disk = tables.Column('local_gb', verbose_name=_("Disk"))
    memory = tables.Column('memory_mb',
                           verbose_name=_("RAM"),
                           filters=(sizeformat.mbformat,),
                           attrs={"data-type": "size"})
    hours = tables.Column('vcpu_hours', verbose_name=_("VCPU Hours"),
                          filters=(lambda v: floatformat(v, 2),))


class GlobalUsageTable(BaseUsageTable):
    project = tables.Column('project_name', verbose_name=_("Project Name"))
    disk_hours = tables.Column('disk_gb_hours',
                               verbose_name=_("Disk GB Hours"),
                               filters=(lambda v: floatformat(v, 2),))

    def get_object_id(self, datum):
        return datum.tenant_id

    class Meta:
        name = "global_usage"
        verbose_name = _("Usage")
        columns = ("project", "vcpus", "disk", "memory",
                   "hours", "disk_hours")
        table_actions = (CSVSummary,)
        multi_select = False


def get_instance_link(datum):
    view = "horizon:project:instances:detail"
    if datum.get('instance_id', False):
        return urlresolvers.reverse(view, args=(datum.get('instance_id'),))
    else:
        return None


class ProjectUsageTable(BaseUsageTable):
    instance = tables.Column('name',
                             verbose_name=_("Instance Name"),
                             link=get_instance_link)
    uptime = tables.Column('uptime_at',
                           verbose_name=_("Uptime"),
                           filters=(filters.timesince_sortable,),
                           attrs={'data-type': 'timesince'})

    def get_object_id(self, datum):
        return datum.get('instance_id', id(datum))

    class Meta:
        name = "project_usage"
        verbose_name = _("Usage")
        columns = ("instance", "vcpus", "disk", "memory", "uptime")
        table_actions = (CSVSummary,)
        multi_select = False
