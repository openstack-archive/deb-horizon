# vim: tabstop=4 shiftwidth=4 softtabstop=4

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

import copy

from django.conf import settings
from django.test.utils import override_settings

import horizon

from openstack_dashboard.test import helpers as test
from openstack_dashboard.test.test_panels.plugin_panel \
    import panel as plugin_panel
import openstack_dashboard.test.test_plugins.panel_group_config
from openstack_dashboard.utils import settings as util_settings


PANEL_GROUP_SLUG = 'plugin_panel_group'
HORIZON_CONFIG = copy.deepcopy(settings.HORIZON_CONFIG)
INSTALLED_APPS = list(settings.INSTALLED_APPS)

util_settings.update_dashboards([
    openstack_dashboard.test.test_plugins.panel_group_config,
], HORIZON_CONFIG, INSTALLED_APPS)


@override_settings(HORIZON_CONFIG=HORIZON_CONFIG,
                   INSTALLED_APPS=INSTALLED_APPS)
class PanelGroupPluginTests(test.PluginTestCase):
    def test_add_panel_group(self):
        dashboard = horizon.get_dashboard("admin")
        self.assertIsNotNone(dashboard.get_panel_group(PANEL_GROUP_SLUG))

    def test_add_panel(self):
        dashboard = horizon.get_dashboard("admin")
        self.assertIn(plugin_panel.PluginPanel,
                      [p.__class__ for p in dashboard.get_panels()])
