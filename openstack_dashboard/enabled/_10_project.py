# Copyright 2015, Hewlett-Packard Development Company, L.P.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# The slug of the dashboard to be added to HORIZON['dashboards']. Required.
DASHBOARD = 'project'
# If set to True, this dashboard will be set as the default dashboard.
DEFAULT = True
# A dictionary of exception classes to be added to HORIZON['exceptions'].
ADD_EXCEPTIONS = {}
# A list of applications to be added to INSTALLED_APPS.
ADD_INSTALLED_APPS = ['openstack_dashboard.dashboards.project']

ADD_ANGULAR_MODULES = [
    'hz.dashboard.project',
]

AUTO_DISCOVER_STATIC_FILES = True

LAUNCH_INST = 'dashboard/launch-instance/'

ADD_JS_FILES = [
    'dashboard/dashboard.module.js',
    LAUNCH_INST + 'launch-instance.module.js',
    LAUNCH_INST + 'launch-instance-workflow.service.js',
    LAUNCH_INST + 'launch-instance-modal.controller.js',
    LAUNCH_INST + 'launch-instance-wizard.controller.js',
    LAUNCH_INST + 'launch-instance-model.js',
    LAUNCH_INST + 'source/source.controller.js',
    LAUNCH_INST + 'source/source-help.controller.js',
    LAUNCH_INST + 'flavor/flavor.controller.js',
    LAUNCH_INST + 'flavor/select-flavor-table.directive.js',
    LAUNCH_INST + 'flavor/flavor-help.controller.js',
    LAUNCH_INST + 'network/network.controller.js',
    LAUNCH_INST + 'network/network-help.controller.js',
    LAUNCH_INST + 'security-groups/security-groups.controller.js',
    LAUNCH_INST + 'security-groups/security-groups-help.controller.js',
    LAUNCH_INST + 'keypair/keypair.js',
    LAUNCH_INST + 'configuration/configuration.controller.js',
    LAUNCH_INST + 'configuration/configuration-help.controller.js',
    LAUNCH_INST + 'configuration/load-edit.directive.js',

    'dashboard/tech-debt/tech-debt.module.js',
    'dashboard/tech-debt/image-form-ctrl.js',
]

ADD_JS_SPEC_FILES = [
    'dashboard/dashboard.module.spec.js',
    LAUNCH_INST + 'launch-instance.module.spec.js',
    LAUNCH_INST + 'launch-instance-workflow.service.spec.js',
    LAUNCH_INST + 'launch-instance-modal.controller.spec.js',
    LAUNCH_INST + 'launch-instance-wizard.controller.spec.js',
    LAUNCH_INST + 'launch-instance-model.spec.js',
    LAUNCH_INST + 'source/source.spec.js',
    LAUNCH_INST + 'flavor/flavor.spec.js',
    LAUNCH_INST + 'network/network.spec.js',
    LAUNCH_INST + 'security-groups/security-groups.spec.js',
    LAUNCH_INST + 'keypair/keypair.spec.js',
    LAUNCH_INST + 'configuration/configuration.spec.js',
]

ADD_SCSS_FILES = [
    'dashboard/project/project.scss'
]
