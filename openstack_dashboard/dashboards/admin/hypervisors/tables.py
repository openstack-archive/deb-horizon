# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2013 B1 Systems GmbH
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

from django.utils.translation import ugettext_lazy as _

from horizon import tables
from horizon.templatetags import sizeformat


class AdminHypervisorsTable(tables.DataTable):
    hostname = tables.Column("hypervisor_hostname",
                             link=("horizon:admin:hypervisors:detail"),
                             verbose_name=_("Hostname"))

    hypervisor_type = tables.Column("hypervisor_type",
                                    verbose_name=_("Type"))

    vcpus = tables.Column("vcpus",
                          verbose_name=_("VCPUs (total)"))

    vcpus_used = tables.Column("vcpus_used",
                               verbose_name=_("VCPUs (used)"))

    memory = tables.Column('memory_mb',
                           verbose_name=_("RAM (total)"),
                           attrs={'data-type': 'size'},
                           filters=(sizeformat.mbformat,))

    memory_used = tables.Column('memory_mb_used',
                                verbose_name=_("RAM (used)"),
                                attrs={'data-type': 'size'},
                                filters=(sizeformat.mbformat,))

    local = tables.Column('local_gb',
                          verbose_name=_("Storage (total)"),
                          attrs={'data-type': 'size'},
                          filters=(sizeformat.diskgbformat,))

    local_used = tables.Column('local_gb_used',
                               verbose_name=_("Storage (used)"),
                               attrs={'data-type': 'size'},
                          filters=(sizeformat.diskgbformat,))

    running_vms = tables.Column("running_vms",
                                verbose_name=_("Instances"))

    def get_object_id(self, hypervisor):
        return hypervisor.hypervisor_hostname

    class Meta:
        name = "hypervisors"
        verbose_name = _("Hypervisors")


class AdminHypervisorInstancesTable(tables.DataTable):
    name = tables.Column("name",
                         verbose_name=_("Instance Name"))

    instance_id = tables.Column("uuid",
                                verbose_name=_("Instance ID"))

    def get_object_id(self, server):
        return server['uuid']

    class Meta:
        name = "hypervisor_instances"
        verbose_name = _("Hypervisor Instances")
