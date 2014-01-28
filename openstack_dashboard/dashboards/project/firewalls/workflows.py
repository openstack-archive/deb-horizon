# vim: tabstop=4 shiftwidth=4 softtabstop=4
#    Copyright 2013, Big Switch Networks, Inc.
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
#
# @author: KC Wang, Big Switch Networks

from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon.utils import fields
from horizon.utils import validators
from horizon import workflows

from openstack_dashboard import api

port_validator = validators.validate_port_or_colon_separated_port_range


class AddRuleAction(workflows.Action):
    name = forms.CharField(
        max_length=80,
        label=_("Name"),
        required=False)
    description = forms.CharField(
        max_length=80,
        label=_("Description"),
        required=False)
    protocol = forms.ChoiceField(
        label=_("Protocol"),
        choices=[('tcp', _('TCP')),
                 ('udp', _('UDP')),
                 ('icmp', _('ICMP')),
                 ('any', _('ANY'))],)
    action = forms.ChoiceField(
        label=_("Action"),
        choices=[('allow', _('ALLOW')),
                 ('deny', _('DENY'))],)
    source_ip_address = fields.IPField(
        label=_("Source IP Address/Subnet"),
        version=fields.IPv4 | fields.IPv6,
        required=False, mask=True)
    destination_ip_address = fields.IPField(
        label=_("Destination IP Address/Subnet"),
        version=fields.IPv4 | fields.IPv6,
        required=False, mask=True)
    source_port = forms.CharField(
        max_length=80,
        label=_("Source Port/Port Range"),
        required=False,
        validators=[port_validator])
    destination_port = forms.CharField(
        max_length=80,
        label=_("Destination Port/Port Range"),
        required=False,
        validators=[port_validator])
    shared = forms.BooleanField(
        label=_("Shared"), initial=False, required=False)
    enabled = forms.BooleanField(
        label=_("Enabled"), initial=True, required=False)

    def __init__(self, request, *args, **kwargs):
        super(AddRuleAction, self).__init__(request, *args, **kwargs)

    class Meta:
        name = _("AddRule")
        permissions = ('openstack.services.network',)
        help_text = _("Create a firewall rule.\n\n"
                      "Protocol and action must be specified. "
                      "Other fields are optional.")


class AddRuleStep(workflows.Step):
    action_class = AddRuleAction
    contributes = ("name", "description", "protocol", "action",
                   "source_ip_address", "source_port",
                   "destination_ip_address", "destination_port",
                   "enabled", "shared")

    def contribute(self, data, context):
        context = super(AddRuleStep, self).contribute(data, context)
        if data:
            if context['protocol'] == 'any':
                del context['protocol']
            for field in ['source_port',
                          'destination_port',
                          'source_ip_address',
                          'destination_ip_address']:
                if not context[field]:
                    del context[field]
            return context


class AddRule(workflows.Workflow):
    slug = "addrule"
    name = _("Add Rule")
    finalize_button_name = _("Add")
    success_message = _('Added Rule "%s".')
    failure_message = _('Unable to add Rule "%s".')
    success_url = "horizon:project:firewalls:index"
    # fwaas is designed to support a wide range of vendor
    # firewalls. Considering the multitude of vendor firewall
    # features in place today, firewall_rule definition can
    # involve more complex configuration over time. Hence,
    # a workflow instead of a single form is used for
    # firewall_rule add to be ready for future extension.
    default_steps = (AddRuleStep,)

    def format_status_message(self, message):
        return message % self.context.get('name')

    def handle(self, request, context):
        try:
            api.fwaas.rule_create(request, **context)
            return True
        except Exception as e:
            msg = self.format_status_message(self.failure_message) + str(e)
            exceptions.handle(request, msg)
            return False


class SelectRulesAction(workflows.Action):
    rule = forms.MultipleChoiceField(
        label=_("Rules"),
        required=False,
        widget=forms.CheckboxSelectMultiple(),
        help_text=_("Create a policy with selected rules."))

    class Meta:
        name = _("Rules")
        permissions = ('openstack.services.network',)
        help_text = _("Select rules for your policy.")

    def populate_rule_choices(self, request, context):
        try:
            tenant_id = self.request.user.tenant_id
            rules = api.fwaas.rule_list(request, tenant_id=tenant_id)
            for r in rules:
                r.set_id_as_name_if_empty()
            rules = sorted(rules,
                           key=lambda rule: rule.name)
            rule_list = [(rule.id, rule.name) for rule in rules
                         if not rule.firewall_policy_id]
        except Exception as e:
            rule_list = []
            exceptions.handle(request,
                              _('Unable to retrieve rules (%(error)s).') % {
                                  'error': str(e)})
        return rule_list


class SelectRulesStep(workflows.Step):
    action_class = SelectRulesAction
    template_name = "project/firewalls/_update_rules.html"
    contributes = ("firewall_rules",)

    def contribute(self, data, context):
        if data:
            rules = self.workflow.request.POST.getlist("rule")
            if rules:
                rules = [r for r in rules if r != '']
                context['firewall_rules'] = rules
            return context


class AddPolicyAction(workflows.Action):
    name = forms.CharField(max_length=80,
                           label=_("Name"),
                           required=True)
    description = forms.CharField(max_length=80,
                                  label=_("Description"),
                                  required=False)
    shared = forms.BooleanField(label=_("Shared"),
                                initial=False,
                                required=False)
    audited = forms.BooleanField(label=_("Audited"),
                                 initial=False,
                                 required=False)

    def __init__(self, request, *args, **kwargs):
        super(AddPolicyAction, self).__init__(request, *args, **kwargs)

    class Meta:
        name = _("AddPolicy")
        permissions = ('openstack.services.network',)
        help_text = _("Create a firewall policy with an ordered list "
                      "of firewall rules.\n\n"
                      "A name must be given. Firewall rules are "
                      "added in the order placed under the Rules tab.")


class AddPolicyStep(workflows.Step):
    action_class = AddPolicyAction
    contributes = ("name", "description", "shared", "audited")

    def contribute(self, data, context):
        context = super(AddPolicyStep, self).contribute(data, context)
        if data:
            return context


class AddPolicy(workflows.Workflow):
    slug = "addpolicy"
    name = _("Add Policy")
    finalize_button_name = _("Add")
    success_message = _('Added Policy "%s".')
    failure_message = _('Unable to add Policy "%s".')
    success_url = "horizon:project:firewalls:index"
    default_steps = (AddPolicyStep, SelectRulesStep)

    def format_status_message(self, message):
        return message % self.context.get('name')

    def handle(self, request, context):
        try:
            api.fwaas.policy_create(request, **context)
            return True
        except Exception as e:
            msg = self.format_status_message(self.failure_message) + str(e)
            exceptions.handle(request, msg)
            return False


class AddFirewallAction(workflows.Action):
    name = forms.CharField(max_length=80,
                           label=_("Name"),
                           required=False)
    description = forms.CharField(max_length=80,
                                  label=_("Description"),
                                  required=False)
    firewall_policy_id = forms.ChoiceField(label=_("Policy"),
                                           required=True)
    shared = forms.BooleanField(label=_("Shared"),
                                initial=False,
                                required=False)
    admin_state_up = forms.BooleanField(label=_("Admin State"),
                                        initial=True,
                                        required=False)

    def __init__(self, request, *args, **kwargs):
        super(AddFirewallAction, self).__init__(request, *args, **kwargs)

        firewall_policy_id_choices = [('', _("Select a Policy"))]
        try:
            tenant_id = self.request.user.tenant_id
            policies = api.fwaas.policy_list(request, tenant_id=tenant_id)
            policies = sorted(policies, key=lambda policy: policy.name)
        except Exception as e:
            exceptions.handle(
                request,
                _('Unable to retrieve policy list (%(error)s).') % {
                    'error': str(e)})
            policies = []
        for p in policies:
            p.set_id_as_name_if_empty()
            firewall_policy_id_choices.append((p.id, p.name))
        self.fields['firewall_policy_id'].choices = firewall_policy_id_choices
        # only admin can set 'shared' attribute to True
        if not request.user.is_superuser:
            self.fields['shared'].widget.attrs['disabled'] = 'disabled'

    class Meta:
        name = _("AddFirewall")
        permissions = ('openstack.services.network',)
        help_text = _("Create a firewall based on a policy.\n\n"
                      "A policy must be selected. "
                      "Other fields are optional.")


class AddFirewallStep(workflows.Step):
    action_class = AddFirewallAction
    contributes = ("name", "firewall_policy_id", "description",
                   "shared", "admin_state_up")

    def contribute(self, data, context):
        context = super(AddFirewallStep, self).contribute(data, context)
        return context


class AddFirewall(workflows.Workflow):
    slug = "addfirewall"
    name = _("Add Firewall")
    finalize_button_name = _("Add")
    success_message = _('Added Firewall "%s".')
    failure_message = _('Unable to add Firewall "%s".')
    success_url = "horizon:project:firewalls:index"
    # fwaas is designed to support a wide range of vendor
    # firewalls. Considering the multitude of vendor firewall
    # features in place today, firewall definition can
    # involve more complex configuration over time. Hence,
    # a workflow instead of a single form is used for
    # firewall_rule add to be ready for future extension.
    default_steps = (AddFirewallStep,)

    def format_status_message(self, message):
        return message % self.context.get('name')

    def handle(self, request, context):
        try:
            api.fwaas.firewall_create(request, **context)
            return True
        except Exception as e:
            msg = self.format_status_message(self.failure_message) + str(e)
            exceptions.handle(request, msg)
            return False
