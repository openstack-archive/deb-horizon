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

from django.conf import settings
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from horizon import tables

from openstack_dashboard import api
from openstack_dashboard.utils import filters


class DeleteGroup(tables.DeleteAction):
    data_type_singular = _("Security Group")
    data_type_plural = _("Security Groups")

    def allowed(self, request, security_group=None):
        if not security_group:
            return True
        return security_group.name != 'default'

    def delete(self, request, obj_id):
        api.network.security_group_delete(request, obj_id)


class CreateGroup(tables.LinkAction):
    name = "create"
    verbose_name = _("Create Security Group")
    url = "horizon:project:access_and_security:security_groups:create"
    classes = ("ajax-modal", "btn-create")


class EditGroup(tables.LinkAction):
    name = "edit"
    verbose_name = _("Edit Security Group")
    url = "horizon:project:access_and_security:security_groups:update"
    classes = ("ajax-modal", "btn-edit")

    def allowed(self, request, security_group=None):
        if not security_group:
            return True
        return security_group.name != 'default'


class ManageRules(tables.LinkAction):
    name = "manage_rules"
    verbose_name = _("Manage Rules")
    url = "horizon:project:access_and_security:security_groups:detail"
    classes = ("btn-edit")


class SecurityGroupsTable(tables.DataTable):
    name = tables.Column("name", verbose_name=_("Name"))
    description = tables.Column("description", verbose_name=_("Description"))

    def sanitize_id(self, obj_id):
        return filters.get_int_or_uuid(obj_id)

    class Meta:
        name = "security_groups"
        verbose_name = _("Security Groups")
        table_actions = (CreateGroup, DeleteGroup)
        row_actions = (ManageRules, EditGroup, DeleteGroup)


class CreateRule(tables.LinkAction):
    name = "add_rule"
    verbose_name = _("Add Rule")
    url = "horizon:project:access_and_security:security_groups:add_rule"
    classes = ("ajax-modal", "btn-create")

    def get_link_url(self):
        return reverse(self.url, args=[self.table.kwargs['security_group_id']])


class DeleteRule(tables.DeleteAction):
    data_type_singular = _("Rule")
    data_type_plural = _("Rules")

    def delete(self, request, obj_id):
        api.network.security_group_rule_delete(request, obj_id)

    def get_success_url(self, request):
        sg_id = self.table.kwargs['security_group_id']
        return reverse("horizon:project:access_and_security:"
                       "security_groups:detail", args=[sg_id])


def get_remote(rule):
    if 'cidr' in rule.ip_range:
        if rule.ip_range['cidr'] is None:
            range = '::/0' if rule.ethertype == 'IPv6' else '0.0.0.0/0'
        else:
            range = rule.ip_range['cidr']
        return range + ' (CIDR)'
    elif 'name' in rule.group:
        return rule.group['name']
    else:
        return None


def get_port_range(rule):
    ip_proto = rule.ip_protocol
    if rule.from_port == rule.to_port:
        return check_rule_template(rule.from_port, ip_proto)
    else:
        return (u"%(from)s - %(to)s" %
                {'from': check_rule_template(rule.from_port, ip_proto),
                 'to': check_rule_template(rule.to_port, ip_proto)})


def filter_direction(direction):
    if direction is None or direction.lower() == 'ingress':
        return _('Ingress')
    else:
        return _('Egress')


def filter_protocol(protocol):
    if protocol is None:
        return _('Any')
    return unicode.upper(protocol)


def check_rule_template(port, ip_proto):
    rules_dict = getattr(settings, 'SECURITY_GROUP_RULES', {})
    if not rules_dict:
        return port
    templ_rule = filter(lambda rule: str(port) == rule['from_port']
                        and str(port) == rule['to_port']
                        and ip_proto == rule['ip_protocol'],
                        [rule for rule in rules_dict.values()])
    if templ_rule:
        return u"%(from_port)s (%(name)s)" % templ_rule[0]
    return port


class RulesTable(tables.DataTable):
    direction = tables.Column("direction",
                              verbose_name=_("Direction"),
                              filters=(filter_direction,))
    ethertype = tables.Column("ethertype",
                              verbose_name=_("Ether Type"))
    protocol = tables.Column("ip_protocol",
                             verbose_name=_("IP Protocol"),
                             filters=(filter_protocol,))
    port_range = tables.Column(get_port_range,
                               verbose_name=_("Port Range"))
    remote = tables.Column(get_remote, verbose_name=_("Remote"))

    def sanitize_id(self, obj_id):
        return filters.get_int_or_uuid(obj_id)

    def get_object_display(self, rule):
        return unicode(rule)

    class Meta:
        name = "rules"
        verbose_name = _("Security Group Rules")
        table_actions = (CreateRule, DeleteRule)
        row_actions = (DeleteRule,)
