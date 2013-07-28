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

from django.utils.translation import ugettext_lazy as _

import horizon


class BasePanels(horizon.PanelGroup):
    slug = "compute"
    name = _("Manage Compute")
    panels = ('overview',
              'instances',
              'volumes',
              'images_and_snapshots',
              'access_and_security',)


class NetworkPanels(horizon.PanelGroup):
    slug = "network"
    name = _("Manage Network")
    panels = ('networks',
              'routers',
              'loadbalancers',
              'network_topology',)


class ObjectStorePanels(horizon.PanelGroup):
    slug = "object_store"
    name = _("Object Store")
    panels = ('containers',)


class OrchestrationPanels(horizon.PanelGroup):
    name = _("Orchestration")
    slug = "orchestration"
    panels = ('stacks',)


class Project(horizon.Dashboard):
    name = _("Project")
    slug = "project"
    panels = (
        BasePanels, NetworkPanels, ObjectStorePanels, OrchestrationPanels)
    default_panel = 'overview'
    supports_tenants = True


horizon.register(Project)
