# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import os

from oslo.config import cfg


DashboardGroup = [
    cfg.StrOpt('dashboard_url',
               default='http://localhost/',
               help="Where the dashboard can be found"),
    cfg.StrOpt('login_url',
               default='http://localhost/auth/login/',
               help="Login page for the dashboard"),
    cfg.IntOpt('page_timeout',
               default=10,
               help="Timeout in seconds"),
]

IdentityGroup = [
    cfg.StrOpt('username',
               default='demo',
               help="Username to use for non-admin API requests."),
    cfg.StrOpt('password',
               default='pass',
               help="API key to use when authenticating.",
               secret=True),
    cfg.StrOpt('admin_username',
               default='admin',
               help="Administrative Username to use for admin API "
               "requests."),
    cfg.StrOpt('admin_password',
               default='pass',
               help="API key to use when authenticating as admin.",
               secret=True),
]


def _get_config_files():
    conf_dir = os.path.join(
        os.path.abspath(os.path.dirname(os.path.dirname(__file__))),
        'integration_tests')
    conf_file = os.environ.get('HORIZON_INTEGRATION_TESTS_CONFIG_FILE',
                               "%s/horizon.conf" % conf_dir)
    return [conf_file]


def get_config():
    cfg.CONF([], project='horizon', default_config_files=_get_config_files())

    cfg.CONF.register_opts(DashboardGroup, group="dashboard")
    cfg.CONF.register_opts(IdentityGroup, group="identity")

    return cfg.CONF
