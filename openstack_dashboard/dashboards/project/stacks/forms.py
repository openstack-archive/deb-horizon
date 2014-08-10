# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import json
import logging

from django.utils.translation import ugettext_lazy as _
from django.views.decorators.debug import sensitive_variables  # noqa

from horizon import exceptions
from horizon import forms
from horizon import messages

from openstack_dashboard import api

LOG = logging.getLogger(__name__)


def create_upload_form_attributes(prefix, input_type, name):
    """Creates attribute dicts for the switchable upload form

    :type prefix: str
    :param prefix: prefix (environment, template) of field
    :type input_type: str
    :param input_type: field type (file, raw, url)
    :type name: str
    :param name: translated text label to display to user
    :rtype: dict
    :return: an attribute set to pass to form build
    """
    attributes = {'class': 'switched', 'data-switch-on': prefix + 'source'}
    attributes['data-' + prefix + 'source-' + input_type] = name
    return attributes


class TemplateForm(forms.SelfHandlingForm):

    class Meta:
        name = _('Select Template')
        help_text = _('From here you can select a template to launch '
                      'a stack.')

    choices = [('url', _('URL')),
               ('file', _('File')),
               ('raw', _('Direct Input'))]
    attributes = {'class': 'switchable', 'data-slug': 'templatesource'}
    template_source = forms.ChoiceField(label=_('Template Source'),
                                        choices=choices,
                                        widget=forms.Select(attrs=attributes))

    attributes = create_upload_form_attributes(
        'template',
        'file',
        _('Template File'))
    template_upload = forms.FileField(
        label=_('Template File'),
        help_text=_('A local template to upload.'),
        widget=forms.FileInput(attrs=attributes),
        required=False)

    attributes = create_upload_form_attributes(
        'template',
        'url',
        _('Template URL'))
    template_url = forms.URLField(
        label=_('Template URL'),
        help_text=_('An external (HTTP) URL to load the template from.'),
        widget=forms.TextInput(attrs=attributes),
        required=False)

    attributes = create_upload_form_attributes(
        'template',
        'raw',
        _('Template Data'))
    template_data = forms.CharField(
        label=_('Template Data'),
        help_text=_('The raw contents of the template.'),
        widget=forms.widgets.Textarea(attrs=attributes),
        required=False)

    attributes = {'data-slug': 'envsource', 'class': 'switchable'}
    environment_source = forms.ChoiceField(
        label=_('Environment Source'),
        choices=choices,
        widget=forms.Select(attrs=attributes),
        required=False)

    attributes = create_upload_form_attributes(
        'env',
        'file',
        _('Environment File'))
    environment_upload = forms.FileField(
        label=_('Environment File'),
        help_text=_('A local environment to upload.'),
        widget=forms.FileInput(attrs=attributes),
        required=False)

    attributes = create_upload_form_attributes(
        'env',
        'url',
        _('Environment URL'))
    environment_url = forms.URLField(
        label=_('Environment URL'),
        help_text=_('An external (HTTP) URL to load the environment from.'),
        widget=forms.TextInput(attrs=attributes),
        required=False)

    attributes = create_upload_form_attributes(
        'env',
        'raw',
        _('Environment Data'))
    environment_data = forms.CharField(
        label=_('Environment Data'),
        help_text=_('The raw contents of the environment file.'),
        widget=forms.widgets.Textarea(attrs=attributes),
        required=False)

    def __init__(self, *args, **kwargs):
        self.next_view = kwargs.pop('next_view')
        super(TemplateForm, self).__init__(*args, **kwargs)

    def clean(self):
        cleaned = super(TemplateForm, self).clean()

        files = self.request.FILES
        self.clean_uploaded_files('template', _('template'), cleaned, files)
        self.clean_uploaded_files('environment',
            _('environment'),
            cleaned,
            files)

        # Validate the template and get back the params.
        kwargs = {}
        if cleaned['template_data']:
            kwargs['template'] = cleaned['template_data']
        else:
            kwargs['template_url'] = cleaned['template_url']

        try:
            validated = api.heat.template_validate(self.request, **kwargs)
            cleaned['template_validate'] = validated
        except Exception as e:
            raise forms.ValidationError(unicode(e))

        return cleaned

    def clean_uploaded_files(self, prefix, field_label, cleaned, files):
        """Cleans Template & Environment data from form upload.

        Does some of the crunchy bits for processing uploads vs raw
        data depending on what the user specified. Identical process
        for environment data & template data.

        :type prefix: str
        :param prefix: prefix (environment, template) of field
        :type field_label: str
        :param field_label: translated prefix str for messages
        :type input_type: dict
        :param prefix: existing cleaned fields from form
        :rtype: dict
        :return: cleaned dict including environment & template data
        """

        upload_str = prefix + "_upload"
        data_str = prefix + "_data"
        url = cleaned.get(prefix + '_url')
        data = cleaned.get(prefix + '_data')

        has_upload = upload_str in files
        # Uploaded file handler
        if has_upload and not url:
            log_template_name = files[upload_str].name
            LOG.info('got upload %s' % log_template_name)

            tpl = files[upload_str].read()
            if tpl.startswith('{'):
                try:
                    json.loads(tpl)
                except Exception as e:
                    msg = _('There was a problem parsing the'
                            ' %(prefix)s: %(error)s')
                    msg = msg % {'prefix': prefix, 'error': e}
                    raise forms.ValidationError(msg)
            cleaned[data_str] = tpl

        # URL handler
        elif url and (has_upload or data):
            msg = _('Please specify a %s using only one source method.')
            msg = msg % field_label
            raise forms.ValidationError(msg)

        elif prefix == 'template':
            # Check for raw template input - blank environment allowed
            if not url and not data:
                msg = _('You must specify a template via one of the '
                        'available sources.')
                raise forms.ValidationError(msg)

    def create_kwargs(self, data):
        kwargs = {'parameters': data['template_validate'],
                  'environment_data': data['environment_data'],
                  'environment_url': data['environment_url'],
                  'template_data': data['template_data'],
                  'template_url': data['template_url']}
        if data.get('stack_id'):
            kwargs['stack_id'] = data['stack_id']
        return kwargs

    def handle(self, request, data):
        kwargs = self.create_kwargs(data)
        # NOTE (gabriel): This is a bit of a hack, essentially rewriting this
        # request so that we can chain it as an input to the next view...
        # but hey, it totally works.
        request.method = 'GET'

        return self.next_view.as_view()(request, **kwargs)


class ChangeTemplateForm(TemplateForm):
    class Meta:
        name = _('Edit Template')
        help_text = _('From here you can select a new template to re-launch '
                      'a stack.')
    stack_id = forms.CharField(label=_('Stack ID'),
        widget=forms.widgets.HiddenInput,
        required=True)
    stack_name = forms.CharField(label=_('Stack Name'),
        widget=forms.TextInput(
            attrs={'readonly': 'readonly'}
        ))


class CreateStackForm(forms.SelfHandlingForm):

    param_prefix = '__param_'

    class Meta:
        name = _('Create Stack')

    template_data = forms.CharField(
        widget=forms.widgets.HiddenInput,
        required=False)
    template_url = forms.CharField(
        widget=forms.widgets.HiddenInput,
        required=False)
    environment_data = forms.CharField(
        widget=forms.widgets.HiddenInput,
        required=False)
    environment_url = forms.CharField(
        widget=forms.widgets.HiddenInput,
        required=False)
    parameters = forms.CharField(
        widget=forms.widgets.HiddenInput,
        required=True)
    stack_name = forms.RegexField(
        max_length='255',
        label=_('Stack Name'),
        help_text=_('Name of the stack to create.'),
        regex=r"^[a-zA-Z][a-zA-Z0-9_.-]*$",
        error_messages={'invalid': _('Name must start with a letter and may '
                            'only contain letters, numbers, underscores, '
                            'periods and hyphens.')},
        required=True)
    timeout_mins = forms.IntegerField(
        initial=60,
        label=_('Creation Timeout (minutes)'),
        help_text=_('Stack creation timeout in minutes.'),
        required=True)
    enable_rollback = forms.BooleanField(
        label=_('Rollback On Failure'),
        help_text=_('Enable rollback on create/update failure.'),
        required=False)

    def __init__(self, *args, **kwargs):
        parameters = kwargs.pop('parameters')
        # special case: load template data from API, not passed in params
        if(kwargs.get('validate_me')):
            parameters = kwargs.pop('validate_me')
        super(CreateStackForm, self).__init__(*args, **kwargs)
        self._build_parameter_fields(parameters)

    def _build_parameter_fields(self, template_validate):
        self.fields['password'] = forms.CharField(
            label=_('Password for user "%s"') % self.request.user.username,
            help_text=_('This is required for operations to be performed '
                        'throughout the lifecycle of the stack'),
            required=True,
            widget=forms.PasswordInput())

        self.help_text = template_validate['Description']

        params = template_validate.get('Parameters', {})

        for param_key, param in params.items():
            field_key = self.param_prefix + param_key
            field_args = {
                'initial': param.get('Default', None),
                'label': param_key,
                'help_text': param.get('Description', ''),
                'required': param.get('Default', None) is None
            }

            param_type = param.get('Type', None)

            if 'AllowedValues' in param:
                choices = map(lambda x: (x, x), param['AllowedValues'])
                field_args['choices'] = choices
                field = forms.ChoiceField(**field_args)

            elif param_type in ('CommaDelimitedList', 'String'):
                if 'MinLength' in param:
                    field_args['min_length'] = int(param['MinLength'])
                    field_args['required'] = param.get('MinLength', 0) > 0
                if 'MaxLength' in param:
                    field_args['max_length'] = int(param['MaxLength'])
                field = forms.CharField(**field_args)

            elif param_type == 'Number':
                if 'MinValue' in param:
                    field_args['min_value'] = int(param['MinValue'])
                if 'MaxValue' in param:
                    field_args['max_value'] = int(param['MaxValue'])
                field = forms.IntegerField(**field_args)

            self.fields[field_key] = field

    @sensitive_variables('password')
    def handle(self, request, data):
        prefix_length = len(self.param_prefix)
        params_list = [(k[prefix_length:], v) for (k, v) in data.iteritems()
                       if k.startswith(self.param_prefix)]
        fields = {
            'stack_name': data.get('stack_name'),
            'timeout_mins': data.get('timeout_mins'),
            'disable_rollback': not(data.get('enable_rollback')),
            'parameters': dict(params_list),
            'password': data.get('password')
        }

        if data.get('template_data'):
            fields['template'] = data.get('template_data')
        else:
            fields['template_url'] = data.get('template_url')

        if data.get('environment_data'):
            fields['environment'] = data.get('environment_data')
        elif data.get('environment_url'):
            fields['environment_url'] = data.get('environment_url')

        try:
            api.heat.stack_create(self.request, **fields)
            messages.success(request, _("Stack creation started."))
            return True
        except Exception:
            exceptions.handle(request)


class EditStackForm(CreateStackForm):

    class Meta:
        name = _('Update Stack Parameters')

    stack_id = forms.CharField(label=_('Stack ID'),
        widget=forms.widgets.HiddenInput,
        required=True)
    stack_name = forms.CharField(label=_('Stack Name'),
        widget=forms.TextInput(
            attrs={'readonly': 'readonly'}
        ))

    @sensitive_variables('password')
    def handle(self, request, data):
        prefix_length = len(self.param_prefix)
        params_list = [(k[prefix_length:], v) for (k, v) in data.iteritems()
                       if k.startswith(self.param_prefix)]

        stack_id = data.get('stack_id')
        fields = {
            'stack_name': data.get('stack_name'),
            'timeout_mins': data.get('timeout_mins'),
            'disable_rollback': not(data.get('enable_rollback')),
            'parameters': dict(params_list),
            'password': data.get('password')
        }

        # if the user went directly to this form, resubmit the existing
        # template data. otherwise, submit what they had from the first form
        if data.get('template_data'):
            fields['template'] = data.get('template_data')
        elif data.get('template_url'):
            fields['template_url'] = data.get('template_url')
        elif data.get('parameters'):
            fields['template'] = data.get('parameters')

        try:
            api.heat.stack_update(self.request, stack_id=stack_id, **fields)
            messages.success(request, _("Stack update started."))
            return True
        except Exception:
            exceptions.handle(request)
