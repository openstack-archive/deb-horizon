# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
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

import netaddr

from django.conf import settings
from django.core.urlresolvers import reverse
from django.core import validators
from django.forms import ValidationError  # noqa
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import messages
from horizon.utils import fields
from horizon.utils import validators as utils_validators

from openstack_dashboard import api
from openstack_dashboard.utils import filters


class CreateGroup(forms.SelfHandlingForm):
    name = forms.CharField(label=_("Name"),
                           max_length=255,
                           error_messages={
                               'required': _('This field is required.'),
                               'invalid': _("The string may only contain"
                                            " ASCII characters and numbers.")},
                           validators=[validators.validate_slug])
    description = forms.CharField(label=_("Description"))

    def handle(self, request, data):
        try:
            sg = api.network.security_group_create(request,
                                                   data['name'],
                                                   data['description'])
            messages.success(request,
                             _('Successfully created security group: %s')
                               % data['name'])
            return sg
        except Exception:
            redirect = reverse("horizon:project:access_and_security:index")
            exceptions.handle(request,
                              _('Unable to create security group.'),
                              redirect=redirect)


class UpdateGroup(forms.SelfHandlingForm):
    id = forms.CharField(widget=forms.HiddenInput())
    name = forms.CharField(label=_("Name"),
                           max_length=255,
                           error_messages={
                               'required': _('This field is required.'),
                               'invalid': _("The string may only contain"
                                            " ASCII characters and numbers.")},
                           validators=[validators.validate_slug])
    description = forms.CharField(label=_("Description"))

    def handle(self, request, data):
        try:
            sg = api.network.security_group_update(request,
                                                   data['id'],
                                                   data['name'],
                                                   data['description'])
            messages.success(request,
                             _('Successfully updated security group: %s')
                               % data['name'])
            return sg
        except Exception:
            redirect = reverse("horizon:project:access_and_security:index")
            exceptions.handle(request,
                              _('Unable to update security group.'),
                              redirect=redirect)


class AddRule(forms.SelfHandlingForm):
    id = forms.CharField(widget=forms.HiddenInput())
    rule_menu = forms.ChoiceField(label=_('Rule'),
                                  widget=forms.Select(attrs={
                                      'class': 'switchable',
                                      'data-slug': 'rule_menu'}))

    # "direction" field is enabled only when custom mode.
    # It is because most common rules in local_settings.py is meaningful
    # when its direction is 'ingress'.
    direction = forms.ChoiceField(
        label=_('Direction'),
        required=False,
        widget=forms.Select(attrs={
            'class': 'switched',
            'data-switch-on': 'rule_menu',
            'data-rule_menu-tcp': _('Direction'),
            'data-rule_menu-udp': _('Direction'),
            'data-rule_menu-icmp': _('Direction'),
            'data-rule_menu-custom': _('Direction'),
            'data-rule_menu-all_tcp': _('Direction'),
            'data-rule_menu-all_udp': _('Direction'),
            'data-rule_menu-all_icmp': _('Direction'),
        }))

    ip_protocol = forms.IntegerField(
        label=_('IP Protocol'), required=False,
        help_text=_("Enter an integer value between 0 and 255 "
                    "(or -1 which means wildcard)."),
        validators=[utils_validators.validate_ip_protocol],
        widget=forms.TextInput(attrs={
            'class': 'switched',
            'data-switch-on': 'rule_menu',
            'data-rule_menu-custom': _('IP Protocol')}))

    port_or_range = forms.ChoiceField(
        label=_('Open Port'),
        choices=[('port', _('Port')),
                 ('range', _('Port Range'))],
        widget=forms.Select(attrs={
            'class': 'switchable switched',
            'data-slug': 'range',
            'data-switch-on': 'rule_menu',
            'data-rule_menu-tcp': _('Open Port'),
            'data-rule_menu-udp': _('Open Port')}))

    port = forms.IntegerField(label=_("Port"),
                              required=False,
                              help_text=_("Enter an integer value "
                                          "between 1 and 65535."),
                              widget=forms.TextInput(attrs={
                                  'class': 'switched',
                                  'data-switch-on': 'range',
                                  'data-range-port': _('Port')}),
                              validators=[
                                  utils_validators.validate_port_range])

    from_port = forms.IntegerField(label=_("From Port"),
                                   required=False,
                                   help_text=_("Enter an integer value "
                                               "between 1 and 65535."),
                                   widget=forms.TextInput(attrs={
                                       'class': 'switched',
                                       'data-switch-on': 'range',
                                       'data-range-range': _('From Port')}),
                                   validators=[
                                       utils_validators.validate_port_range])

    to_port = forms.IntegerField(label=_("To Port"),
                                 required=False,
                                 help_text=_("Enter an integer value "
                                             "between 1 and 65535."),
                                 widget=forms.TextInput(attrs={
                                     'class': 'switched',
                                     'data-switch-on': 'range',
                                     'data-range-range': _('To Port')}),
                                 validators=[
                                     utils_validators.validate_port_range])

    icmp_type = forms.IntegerField(label=_("Type"),
                                   required=False,
                                   help_text=_("Enter a value for ICMP type "
                                               "in the range (-1: 255)"),
                                   widget=forms.TextInput(attrs={
                                       'class': 'switched',
                                       'data-switch-on': 'rule_menu',
                                       'data-rule_menu-icmp': _('Type')}),
                                   validators=[
                                       utils_validators.validate_port_range])

    icmp_code = forms.IntegerField(label=_("Code"),
                                   required=False,
                                   help_text=_("Enter a value for ICMP code "
                                               "in the range (-1: 255)"),
                                   widget=forms.TextInput(attrs={
                                       'class': 'switched',
                                       'data-switch-on': 'rule_menu',
                                       'data-rule_menu-icmp': _('Code')}),
                                   validators=[
                                       utils_validators.validate_port_range])

    remote = forms.ChoiceField(label=_('Remote'),
                               choices=[('cidr', _('CIDR')),
                                        ('sg', _('Security Group'))],
                               help_text=_('To specify an allowed IP '
                                           'range, select "CIDR". To '
                                           'allow access from all '
                                           'members of another security '
                                           'group select "Security '
                                           'Group".'),
                               widget=forms.Select(attrs={
                                   'class': 'switchable',
                                   'data-slug': 'remote'}))

    cidr = fields.IPField(label=_("CIDR"),
                          required=False,
                          initial="0.0.0.0/0",
                          help_text=_("Classless Inter-Domain Routing "
                                      "(e.g. 192.168.0.0/24)"),
                          version=fields.IPv4 | fields.IPv6,
                          mask=True,
                          widget=forms.TextInput(
                              attrs={'class': 'switched',
                                     'data-switch-on': 'remote',
                                     'data-remote-cidr': _('CIDR')}))

    security_group = forms.ChoiceField(label=_('Security Group'),
                                       required=False,
                                       widget=forms.Select(attrs={
                                           'class': 'switched',
                                           'data-switch-on': 'remote',
                                           'data-remote-sg': _('Security '
                                                               'Group')}))
    # When cidr is used ethertype is determined from IP version of cidr.
    # When source group, ethertype needs to be specified explicitly.
    ethertype = forms.ChoiceField(label=_('Ether Type'),
                                  required=False,
                                  choices=[('IPv4', _('IPv4')),
                                           ('IPv6', _('IPv6'))],
                                  widget=forms.Select(attrs={
                                      'class': 'switched',
                                      'data-slug': 'ethertype',
                                      'data-switch-on': 'remote',
                                      'data-remote-sg': _('Ether Type')}))

    def __init__(self, *args, **kwargs):
        sg_list = kwargs.pop('sg_list', [])
        super(AddRule, self).__init__(*args, **kwargs)
        # Determine if there are security groups available for the
        # remote group option; add the choices and enable the option if so.
        if sg_list:
            security_groups_choices = sg_list
        else:
            security_groups_choices = [("", _("No security groups available"))]
        self.fields['security_group'].choices = security_groups_choices

        backend = api.network.security_group_backend(self.request)

        rules_dict = getattr(settings, 'SECURITY_GROUP_RULES', [])
        common_rules = [(k, _(rules_dict[k]['name']))
                        for k in rules_dict
                        if rules_dict[k].get('backend', backend) == backend]
        common_rules.sort()
        custom_rules = [('tcp', _('Custom TCP Rule')),
                        ('udp', _('Custom UDP Rule')),
                        ('icmp', _('Custom ICMP Rule'))]
        if backend == 'neutron':
            custom_rules.append(('custom', _('Other Protocol')))
        self.fields['rule_menu'].choices = custom_rules + common_rules
        self.rules = rules_dict

        if backend == 'neutron':
            self.fields['direction'].choices = [('ingress', _('Ingress')),
                                                ('egress', _('Egress'))]
        else:
            # direction and ethertype are not supported in Nova secgroup.
            self.fields['direction'].widget = forms.HiddenInput()
            self.fields['ethertype'].widget = forms.HiddenInput()
            # ip_protocol field is to specify arbitrary protocol number
            # and it is available only for neutron security group.
            self.fields['ip_protocol'].widget = forms.HiddenInput()

    def clean(self):
        cleaned_data = super(AddRule, self).clean()

        def update_cleaned_data(key, value):
            cleaned_data[key] = value
            self.errors.pop(key, None)

        rule_menu = cleaned_data.get('rule_menu')
        port_or_range = cleaned_data.get("port_or_range")
        remote = cleaned_data.get("remote")

        icmp_type = cleaned_data.get("icmp_type", None)
        icmp_code = cleaned_data.get("icmp_code", None)

        from_port = cleaned_data.get("from_port", None)
        to_port = cleaned_data.get("to_port", None)
        port = cleaned_data.get("port", None)

        if rule_menu == 'icmp':
            update_cleaned_data('ip_protocol', rule_menu)
            if icmp_type is None:
                msg = _('The ICMP type is invalid.')
                raise ValidationError(msg)
            if icmp_code is None:
                msg = _('The ICMP code is invalid.')
                raise ValidationError(msg)
            if icmp_type not in range(-1, 256):
                msg = _('The ICMP type not in range (-1, 255)')
                raise ValidationError(msg)
            if icmp_code not in range(-1, 256):
                msg = _('The ICMP code not in range (-1, 255)')
                raise ValidationError(msg)
            update_cleaned_data('from_port', icmp_type)
            update_cleaned_data('to_port', icmp_code)
            update_cleaned_data('port', None)
        elif rule_menu == 'tcp' or rule_menu == 'udp':
            update_cleaned_data('ip_protocol', rule_menu)
            update_cleaned_data('icmp_code', None)
            update_cleaned_data('icmp_type', None)
            if port_or_range == "port":
                update_cleaned_data('from_port', port)
                update_cleaned_data('to_port', port)
                if port is None:
                    msg = _('The specified port is invalid.')
                    raise ValidationError(msg)
            else:
                update_cleaned_data('port', None)
                if from_port is None:
                    msg = _('The "from" port number is invalid.')
                    raise ValidationError(msg)
                if to_port is None:
                    msg = _('The "to" port number is invalid.')
                    raise ValidationError(msg)
                if to_port < from_port:
                    msg = _('The "to" port number must be greater than '
                            'or equal to the "from" port number.')
                    raise ValidationError(msg)
        elif rule_menu == 'custom':
            pass
        else:
            cleaned_data['ip_protocol'] = self.rules[rule_menu]['ip_protocol']
            cleaned_data['from_port'] = int(self.rules[rule_menu]['from_port'])
            cleaned_data['to_port'] = int(self.rules[rule_menu]['to_port'])
            if rule_menu not in ['all_tcp', 'all_udp', 'all_icmp']:
                direction = self.rules[rule_menu].get('direction')
                cleaned_data['direction'] = direction

        # NOTE(amotoki): There are two cases where cleaned_data['direction']
        # is empty: (1) Nova Security Group is used. Since "direction" is
        # HiddenInput, direction field exists but its value is ''.
        # (2) Template except all_* is used. In this case, the default value
        # is None. To make sure 'direction' field has 'ingress' or 'egress',
        # fill this field here if it is not specified.
        if not cleaned_data['direction']:
            cleaned_data['direction'] = 'ingress'

        if remote == "cidr":
            update_cleaned_data('security_group', None)
        else:
            update_cleaned_data('cidr', None)

        # If cleaned_data does not contain cidr, cidr is already marked
        # as invalid, so skip the further validation for cidr.
        # In addition cleaned_data['cidr'] is None means source_group is used.
        if 'cidr' in cleaned_data and cleaned_data['cidr'] is not None:
            cidr = cleaned_data['cidr']
            if not cidr:
                msg = _('CIDR must be specified.')
                self._errors['cidr'] = self.error_class([msg])
            else:
                # If cidr is specified, ethertype is determined from IP address
                # version. It is used only when Neutron is enabled.
                ip_ver = netaddr.IPNetwork(cidr).version
                cleaned_data['ethertype'] = 'IPv6' if ip_ver == 6 else 'IPv4'

        return cleaned_data

    def handle(self, request, data):
        try:
            rule = api.network.security_group_rule_create(
                request,
                filters.get_int_or_uuid(data['id']),
                data['direction'],
                data['ethertype'],
                data['ip_protocol'],
                data['from_port'],
                data['to_port'],
                data['cidr'],
                data['security_group'])
            messages.success(request,
                             _('Successfully added rule: %s') % unicode(rule))
            return rule
        except Exception:
            redirect = reverse("horizon:project:access_and_security:"
                               "security_groups:detail", args=[data['id']])
            exceptions.handle(request,
                              _('Unable to add rule to security group.'),
                              redirect=redirect)
