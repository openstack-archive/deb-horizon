# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
# Copyright 2012 Openstack, LLC
# Copyright 2012 Nebula, Inc.
# Copyright (c) 2012 X.commerce, a business unit of eBay Inc.
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

from __future__ import absolute_import

import logging

from django.conf import settings
from django.utils.translation import ugettext as _

from novaclient.v1_1 import client as nova_client
from novaclient.v1_1 import security_group_rules as nova_rules
from novaclient.v1_1.security_groups import SecurityGroup as NovaSecurityGroup
from novaclient.v1_1.servers import REBOOT_HARD, REBOOT_SOFT

from horizon.conf import HORIZON_CONFIG
from horizon.utils.memoized import memoized

from openstack_dashboard.api.base import (APIResourceWrapper, QuotaSet,
                                          APIDictWrapper, url_for)
from openstack_dashboard.api import network


LOG = logging.getLogger(__name__)


# API static values
INSTANCE_ACTIVE_STATE = 'ACTIVE'
VOLUME_STATE_AVAILABLE = "available"


class VNCConsole(APIDictWrapper):
    """Wrapper for the "console" dictionary returned by the
    novaclient.servers.get_vnc_console method.
    """
    _attrs = ['url', 'type']


class SPICEConsole(APIDictWrapper):
    """Wrapper for the "console" dictionary returned by the
    novaclient.servers.get_spice_console method.
    """
    _attrs = ['url', 'type']


class Server(APIResourceWrapper):
    """Simple wrapper around novaclient.server.Server

       Preserves the request info so image name can later be retrieved

    """
    _attrs = ['addresses', 'attrs', 'id', 'image', 'links',
             'metadata', 'name', 'private_ip', 'public_ip', 'status', 'uuid',
             'image_name', 'VirtualInterfaces', 'flavor', 'key_name',
             'tenant_id', 'user_id', 'OS-EXT-STS:power_state',
             'OS-EXT-STS:task_state', 'OS-EXT-SRV-ATTR:instance_name',
             'OS-EXT-SRV-ATTR:host']

    def __init__(self, apiresource, request):
        super(Server, self).__init__(apiresource)
        self.request = request

    @property
    def image_name(self):
        import glanceclient.exc as glance_exceptions
        from openstack_dashboard.api import glance
        try:
            image = glance.image_get(self.request, self.image['id'])
            return image.name
        except glance_exceptions.ClientException:
            return "(not found)"

    @property
    def internal_name(self):
        return getattr(self, 'OS-EXT-SRV-ATTR:instance_name', "")

    def reboot(self, hardness=REBOOT_HARD):
        novaclient(self.request).servers.reboot(self.id, hardness)


class NovaUsage(APIResourceWrapper):
    """Simple wrapper around contrib/simple_usage.py."""
    _attrs = ['start', 'server_usages', 'stop', 'tenant_id',
             'total_local_gb_usage', 'total_memory_mb_usage',
             'total_vcpus_usage', 'total_hours']

    def get_summary(self):
        return {'instances': self.total_active_instances,
                'memory_mb': self.memory_mb,
                'vcpus': getattr(self, "total_vcpus_usage", 0),
                'vcpu_hours': self.vcpu_hours,
                'local_gb': self.local_gb,
                'disk_gb_hours': self.disk_gb_hours}

    @property
    def total_active_instances(self):
        return sum(1 for s in self.server_usages if s['ended_at'] is None)

    @property
    def vcpus(self):
        return sum(s['vcpus'] for s in self.server_usages
                   if s['ended_at'] is None)

    @property
    def vcpu_hours(self):
        return getattr(self, "total_hours", 0)

    @property
    def local_gb(self):
        return sum(s['local_gb'] for s in self.server_usages
                   if s['ended_at'] is None)

    @property
    def memory_mb(self):
        return sum(s['memory_mb'] for s in self.server_usages
                   if s['ended_at'] is None)

    @property
    def disk_gb_hours(self):
        return getattr(self, "total_local_gb_usage", 0)


class SecurityGroup(APIResourceWrapper):
    """Wrapper around novaclient.security_groups.SecurityGroup which wraps its
    rules in SecurityGroupRule objects and allows access to them.
    """
    _attrs = ['id', 'name', 'description', 'tenant_id']

    @property
    def rules(self):
        """Wraps transmitted rule info in the novaclient rule class."""
        if "_rules" not in self.__dict__:
            manager = nova_rules.SecurityGroupRuleManager(None)
            self._rules = [nova_rules.SecurityGroupRule(manager, rule)
                           for rule in self._apiresource.rules]
        return self.__dict__['_rules']

    @rules.setter
    def rules(self, value):
        self._rules = value


class SecurityGroupRule(APIResourceWrapper):
    """ Wrapper for individual rules in a SecurityGroup. """
    _attrs = ['id', 'ip_protocol', 'from_port', 'to_port', 'ip_range', 'group']

    def __unicode__(self):
        if 'name' in self.group:
            vals = {'from': self.from_port,
                    'to': self.to_port,
                    'group': self.group['name']}
            return _('ALLOW %(from)s:%(to)s from %(group)s') % vals
        else:
            vals = {'from': self.from_port,
                    'to': self.to_port,
                    'cidr': self.ip_range['cidr']}
            return _('ALLOW %(from)s:%(to)s from %(cidr)s') % vals


class FlavorExtraSpec(object):
    def __init__(self, flavor_id, key, val):
        self.flavor_id = flavor_id
        self.id = key
        self.key = key
        self.value = val


class FloatingIp(APIResourceWrapper):
    _attrs = ['id', 'ip', 'fixed_ip', 'port_id', 'instance_id', 'pool']

    def __init__(self, fip):
        fip.__setattr__('port_id', fip.instance_id)
        super(FloatingIp, self).__init__(fip)


class FloatingIpPool(APIDictWrapper):
    def __init__(self, pool):
        pool_dict = {'id': pool.name,
                     'name': pool.name}
        super(FloatingIpPool, self).__init__(pool_dict)


class FloatingIpTarget(APIDictWrapper):
    def __init__(self, server):
        server_dict = {'name': '%s (%s)' % (server.name, server.id),
                       'id': server.id}
        super(FloatingIpTarget, self).__init__(server_dict)


class FloatingIpManager(network.FloatingIpManager):
    def __init__(self, request):
        self.request = request
        self.client = novaclient(request)

    def list_pools(self):
        return [FloatingIpPool(pool)
                for pool in self.client.floating_ip_pools.list()]

    def list(self):
        return [FloatingIp(fip)
                for fip in self.client.floating_ips.list()]

    def get(self, floating_ip_id):
        return FloatingIp(self.client.floating_ips.get(floating_ip_id))

    def allocate(self, pool):
        return FloatingIp(self.client.floating_ips.create(pool=pool))

    def release(self, floating_ip_id):
        self.client.floating_ips.delete(floating_ip_id)

    def associate(self, floating_ip_id, port_id):
        # In Nova implied port_id is instance_id
        server = self.client.servers.get(port_id)
        fip = self.client.floating_ips.get(floating_ip_id)
        self.client.servers.add_floating_ip(server.id, fip.ip)

    def disassociate(self, floating_ip_id, port_id):
        fip = self.client.floating_ips.get(floating_ip_id)
        server = self.client.servers.get(fip.instance_id)
        self.client.servers.remove_floating_ip(server.id, fip.ip)

    def list_targets(self):
        return [FloatingIpTarget(s) for s in self.client.servers.list()]

    def get_target_id_by_instance(self, instance_id):
        return instance_id

    def is_simple_associate_supported(self):
        return HORIZON_CONFIG["simple_ip_management"]


def novaclient(request):
    insecure = getattr(settings, 'OPENSTACK_SSL_NO_VERIFY', False)
    LOG.debug('novaclient connection created using token "%s" and url "%s"' %
              (request.user.token.id, url_for(request, 'compute')))
    c = nova_client.Client(request.user.username,
                           request.user.token.id,
                           project_id=request.user.tenant_id,
                           auth_url=url_for(request, 'compute'),
                           insecure=insecure,
                           http_log_debug=settings.DEBUG)
    c.client.auth_token = request.user.token.id
    c.client.management_url = url_for(request, 'compute')
    return c


def server_vnc_console(request, instance_id, console_type='novnc'):
    return VNCConsole(novaclient(request).servers.get_vnc_console(instance_id,
                                                  console_type)['console'])


def server_spice_console(request, instance_id, console_type='spice-html5'):
    return SPICEConsole(novaclient(request).servers.get_spice_console(
            instance_id, console_type)['console'])


def flavor_create(request, name, memory, vcpu, disk, ephemeral=0, swap=0,
                  metadata=None):
    flavor = novaclient(request).flavors.create(name, memory, vcpu, disk,
                                                ephemeral=ephemeral,
                                                swap=swap)
    if (metadata):
        flavor_extra_set(request, flavor.id, metadata)
    return flavor


def flavor_delete(request, flavor_id):
    novaclient(request).flavors.delete(flavor_id)


def flavor_get(request, flavor_id):
    return novaclient(request).flavors.get(flavor_id)


@memoized
def flavor_list(request):
    """Get the list of available instance sizes (flavors)."""
    return novaclient(request).flavors.list()


def flavor_get_extras(request, flavor_id, raw=False):
    """Get flavor extra specs."""
    flavor = novaclient(request).flavors.get(flavor_id)
    extras = flavor.get_keys()
    if raw:
        return extras
    return [FlavorExtraSpec(flavor_id, key, value) for
            key, value in extras.items()]


def flavor_extra_delete(request, flavor_id, keys):
    """Unset the flavor extra spec keys."""
    flavor = novaclient(request).flavors.get(flavor_id)
    return flavor.unset_keys(keys)


def flavor_extra_set(request, flavor_id, metadata):
    """Set the flavor extra spec keys."""
    flavor = novaclient(request).flavors.get(flavor_id)
    if (not metadata):  # not a way to delete keys
        return None
    return flavor.set_keys(metadata)


def snapshot_create(request, instance_id, name):
    return novaclient(request).servers.create_image(instance_id, name)


def keypair_create(request, name):
    return novaclient(request).keypairs.create(name)


def keypair_import(request, name, public_key):
    return novaclient(request).keypairs.create(name, public_key)


def keypair_delete(request, keypair_id):
    novaclient(request).keypairs.delete(keypair_id)


def keypair_list(request):
    return novaclient(request).keypairs.list()


def server_create(request, name, image, flavor, key_name, user_data,
                  security_groups, block_device_mapping, nics=None,
                  instance_count=1):
    return Server(novaclient(request).servers.create(
            name, image, flavor, userdata=user_data,
            security_groups=security_groups,
            key_name=key_name, block_device_mapping=block_device_mapping,
            nics=nics,
            min_count=instance_count), request)


def server_delete(request, instance):
    novaclient(request).servers.delete(instance)


def server_get(request, instance_id):
    return Server(novaclient(request).servers.get(instance_id), request)


def server_list(request, search_opts=None, all_tenants=False):
    if search_opts is None:
        search_opts = {}
    if all_tenants:
        search_opts['all_tenants'] = True
    else:
        search_opts['project_id'] = request.user.tenant_id
    return [Server(s, request)
            for s in novaclient(request).servers.list(True, search_opts)]


def server_console_output(request, instance_id, tail_length=None):
    """Gets console output of an instance."""
    return novaclient(request).servers.get_console_output(instance_id,
                                                          length=tail_length)


def server_security_groups(request, instance_id):
    """Gets security groups of an instance."""
    # TODO(gabriel): This needs to be moved up to novaclient, and should
    # be removed once novaclient supports this call.
    security_groups = []
    nclient = novaclient(request)
    resp, body = nclient.client.get('/servers/%s/os-security-groups'
                                    % instance_id)
    if body:
        # Wrap data in SG objects as novaclient would.
        sg_objs = [NovaSecurityGroup(nclient.security_groups, sg, loaded=True)
                   for sg in body.get('security_groups', [])]
        # Then wrap novaclient's object with our own. Yes, sadly wrapping
        # with two layers of objects is necessary.
        security_groups = [SecurityGroup(sg) for sg in sg_objs]
        # Package up the rules, as well.
        for sg in security_groups:
            rule_objects = [SecurityGroupRule(rule) for rule in sg.rules]
            sg.rules = rule_objects
    return security_groups


def server_add_security_group(request, instance_id, security_group_name):
    return novaclient(request).servers.add_security_group(instance_id,
                                                          security_group_name)


def server_remove_security_group(request, instance_id, security_group_name):
    return novaclient(request).servers.remove_security_group(
                instance_id,
                security_group_name)


def server_pause(request, instance_id):
    novaclient(request).servers.pause(instance_id)


def server_unpause(request, instance_id):
    novaclient(request).servers.unpause(instance_id)


def server_suspend(request, instance_id):
    novaclient(request).servers.suspend(instance_id)


def server_resume(request, instance_id):
    novaclient(request).servers.resume(instance_id)


def server_reboot(request, instance_id, hardness=REBOOT_HARD):
    server = server_get(request, instance_id)
    server.reboot(hardness)


def server_update(request, instance_id, name):
    response = novaclient(request).servers.update(instance_id, name=name)
    # TODO(gabriel): servers.update method doesn't return anything. :-(
    if response is None:
        return True
    else:
        return response


def server_migrate(request, instance_id):
    novaclient(request).servers.migrate(instance_id)


def server_confirm_resize(request, instance_id):
    novaclient(request).servers.confirm_resize(instance_id)


def server_revert_resize(request, instance_id):
    novaclient(request).servers.revert_resize(instance_id)


def tenant_quota_get(request, tenant_id):
    return QuotaSet(novaclient(request).quotas.get(tenant_id))


def tenant_quota_update(request, tenant_id, **kwargs):
    novaclient(request).quotas.update(tenant_id, **kwargs)


def default_quota_get(request, tenant_id):
    return QuotaSet(novaclient(request).quotas.defaults(tenant_id))


def usage_get(request, tenant_id, start, end):
    return NovaUsage(novaclient(request).usage.get(tenant_id, start, end))


def usage_list(request, start, end):
    return [NovaUsage(u) for u in
            novaclient(request).usage.list(start, end, True)]


def security_group_list(request):
    return [SecurityGroup(g) for g
            in novaclient(request).security_groups.list()]


def security_group_get(request, sg_id):
    return SecurityGroup(novaclient(request).security_groups.get(sg_id))


def security_group_create(request, name, desc):
    return SecurityGroup(novaclient(request).security_groups.create(name,
                                                                    desc))


def security_group_delete(request, security_group_id):
    novaclient(request).security_groups.delete(security_group_id)


def security_group_rule_create(request, parent_group_id, ip_protocol=None,
                               from_port=None, to_port=None, cidr=None,
                               group_id=None):
    sg = novaclient(request).security_group_rules.create(parent_group_id,
                                                         ip_protocol,
                                                         from_port,
                                                         to_port,
                                                         cidr,
                                                         group_id)
    return SecurityGroupRule(sg)


def security_group_rule_delete(request, security_group_rule_id):
    novaclient(request).security_group_rules.delete(security_group_rule_id)


def virtual_interfaces_list(request, instance_id):
    return novaclient(request).virtual_interfaces.list(instance_id)


def get_x509_credentials(request):
    return novaclient(request).certs.create()


def get_x509_root_certificate(request):
    return novaclient(request).certs.get()


def instance_volume_attach(request, volume_id, instance_id, device):
    return novaclient(request).volumes.create_server_volume(instance_id,
                                                              volume_id,
                                                              device)


def instance_volume_detach(request, instance_id, att_id):
    return novaclient(request).volumes.delete_server_volume(instance_id,
                                                              att_id)


def instance_volumes_list(request, instance_id):
    from openstack_dashboard.api.cinder import cinderclient

    volumes = novaclient(request).volumes.get_server_volumes(instance_id)

    for volume in volumes:
        volume_data = cinderclient(request).volumes.get(volume.id)
        volume.name = volume_data.display_name

    return volumes


def tenant_absolute_limits(request, reserved=False):
    limits = novaclient(request).limits.get(reserved=reserved).absolute
    limits_dict = {}
    for limit in limits:
        # -1 is used to represent unlimited quotas
        if limit.value == -1:
            limits_dict[limit.name] = float("inf")
        else:
            limits_dict[limit.name] = limit.value
    return limits_dict
