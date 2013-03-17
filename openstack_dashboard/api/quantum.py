# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
# Copyright 2012 Cisco Systems, Inc.
# Copyright 2012 NEC Corporation
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

from quantumclient.v2_0 import client as quantum_client
from django.utils.datastructures import SortedDict

from horizon.conf import HORIZON_CONFIG

from openstack_dashboard.api.base import APIDictWrapper, url_for
from openstack_dashboard.api import network
from openstack_dashboard.api import nova


LOG = logging.getLogger(__name__)

IP_VERSION_DICT = {4: 'IPv4', 6: 'IPv6'}


class QuantumAPIDictWrapper(APIDictWrapper):

    def set_id_as_name_if_empty(self, length=8):
        try:
            if not self._apidict['name']:
                id = self._apidict['id']
                if length:
                    id = id[:length]
                self._apidict['name'] = '(%s)' % id
        except KeyError:
            pass

    def items(self):
        return self._apidict.items()


class Network(QuantumAPIDictWrapper):
    """Wrapper for quantum Networks"""

    def __init__(self, apiresource):
        apiresource['admin_state'] = \
            'UP' if apiresource['admin_state_up'] else 'DOWN'
        # Django cannot handle a key name with a colon, so remap another key
        for key in apiresource.keys():
            if key.find(':'):
                apiresource['__'.join(key.split(':'))] = apiresource[key]
        super(Network, self).__init__(apiresource)


class Subnet(QuantumAPIDictWrapper):
    """Wrapper for quantum subnets"""

    def __init__(self, apiresource):
        apiresource['ipver_str'] = get_ipver_str(apiresource['ip_version'])
        super(Subnet, self).__init__(apiresource)


class Port(QuantumAPIDictWrapper):
    """Wrapper for quantum ports"""

    def __init__(self, apiresource):
        apiresource['admin_state'] = \
            'UP' if apiresource['admin_state_up'] else 'DOWN'
        super(Port, self).__init__(apiresource)


class Router(QuantumAPIDictWrapper):
    """Wrapper for quantum routers"""

    def __init__(self, apiresource):
        #apiresource['admin_state'] = \
        #    'UP' if apiresource['admin_state_up'] else 'DOWN'
        super(Router, self).__init__(apiresource)


class FloatingIp(APIDictWrapper):
    _attrs = ['id', 'ip', 'fixed_ip', 'port_id', 'instance_id', 'pool']

    def __init__(self, fip):
        fip['ip'] = fip['floating_ip_address']
        fip['fixed_ip'] = fip['fixed_ip_address']
        fip['pool'] = fip['floating_network_id']
        super(FloatingIp, self).__init__(fip)


class FloatingIpPool(APIDictWrapper):
    pass


class FloatingIpTarget(APIDictWrapper):
    pass


class FloatingIpManager(network.FloatingIpManager):
    def __init__(self, request):
        self.request = request
        self.client = quantumclient(request)

    def list_pools(self):
        search_opts = {'router:external': True}
        return [FloatingIpPool(pool) for pool
                in self.client.list_networks(**search_opts).get('networks')]

    def list(self):
        fips = self.client.list_floatingips().get('floatingips')
        # Get port list to add instance_id to floating IP list
        # instance_id is stored in device_id attribute
        ports = port_list(self.request)
        device_id_dict = SortedDict([(p['id'], p['device_id']) for p in ports])
        for fip in fips:
            if fip['port_id']:
                fip['instance_id'] = device_id_dict[fip['port_id']]
            else:
                fip['instance_id'] = None
        return [FloatingIp(fip) for fip in fips]

    def get(self, floating_ip_id):
        fip = self.client.show_floatingip(floating_ip_id).get('floatingip')
        if fip['port_id']:
            fip['instance_id'] = port_get(self.request,
                                          fip['port_id']).device_id
        else:
            fip['instance_id'] = None
        return FloatingIp(fip)

    def allocate(self, pool):
        body = {'floatingip': {'floating_network_id': pool}}
        fip = self.client.create_floatingip(body).get('floatingip')
        fip['instance_id'] = None
        return FloatingIp(fip)

    def release(self, floating_ip_id):
        self.client.delete_floatingip(floating_ip_id)

    def associate(self, floating_ip_id, port_id):
        # NOTE: In Quantum Horizon floating IP support, port_id is
        # "<port_id>_<ip_address>" format to identify multiple ports.
        pid, ip_address = port_id.split('_', 1)
        update_dict = {'port_id': pid,
                       'fixed_ip_address': ip_address}
        self.client.update_floatingip(floating_ip_id,
                                      {'floatingip': update_dict})

    def disassociate(self, floating_ip_id, port_id):
        update_dict = {'port_id': None}
        self.client.update_floatingip(floating_ip_id,
                                      {'floatingip': update_dict})

    def list_targets(self):
        ports = port_list(self.request)
        servers = nova.server_list(self.request)
        server_dict = SortedDict([(s.id, s.name) for s in servers])
        targets = []
        for p in ports:
            # Remove network ports from Floating IP targets
            if p.device_owner.startswith('network:'):
                continue
            port_id = p.id
            server_name = server_dict.get(p.device_id)
            for ip in p.fixed_ips:
                target = {'name': '%s: %s' % (server_name, ip['ip_address']),
                          'id': '%s_%s' % (port_id, ip['ip_address'])}
                targets.append(FloatingIpTarget(target))
        return targets

    def get_target_id_by_instance(self, instance_id):
        # In Quantum one port can have multiple ip addresses, so this method
        # picks up the first one and generate target id.
        if not instance_id:
            return None
        search_opts = {'device_id': instance_id}
        ports = port_list(self.request, **search_opts)
        if not ports:
            return None
        return '%s_%s' % (ports[0].id, ports[0].fixed_ips[0]['ip_address'])

    def is_simple_associate_supported(self):
        # NOTE: There are two reason that simple association support
        # needs more considerations. (1) Quantum does not support the
        # default floating IP pool at the moment. It can be avoided
        # in case where only one floating IP pool exists.
        # (2) Quantum floating IP is associated with each VIF and
        # we need to check whether such VIF is only one for an instance
        # to enable simple association support.
        return False


def get_ipver_str(ip_version):
    """Convert an ip version number to a human-friendly string"""
    return IP_VERSION_DICT.get(ip_version, '')


def quantumclient(request):
    LOG.debug('quantumclient connection created using token "%s" and url "%s"'
              % (request.user.token.id, url_for(request, 'network')))
    LOG.debug('user_id=%(user)s, tenant_id=%(tenant)s' %
              {'user': request.user.id, 'tenant': request.user.tenant_id})
    c = quantum_client.Client(token=request.user.token.id,
                              endpoint_url=url_for(request, 'network'))
    return c


def network_list(request, **params):
    LOG.debug("network_list(): params=%s" % (params))
    networks = quantumclient(request).list_networks(**params).get('networks')
    # Get subnet list to expand subnet info in network list.
    subnets = subnet_list(request)
    subnet_dict = SortedDict([(s['id'], s) for s in subnets])
    # Expand subnet list from subnet_id to values.
    for n in networks:
        n['subnets'] = [subnet_dict.get(s) for s in n.get('subnets', [])]
    return [Network(n) for n in networks]


def network_list_for_tenant(request, tenant_id, **params):
    """Return a network list available for the tenant.
    The list contains networks owned by the tenant and public networks.
    If requested_networks specified, it searches requested_networks only.
    """
    LOG.debug("network_list_for_tenant(): tenant_id=%s, params=%s"
              % (tenant_id, params))

    # If a user has admin role, network list returned by Quantum API
    # contains networks that do not belong to that tenant.
    # So we need to specify tenant_id when calling network_list().
    networks = network_list(request, tenant_id=tenant_id,
                            shared=False, **params)

    # In the current Quantum API, there is no way to retrieve
    # both owner networks and public networks in a single API call.
    networks += network_list(request, shared=True, **params)

    return networks


def network_get(request, network_id, expand_subnet=True, **params):
    LOG.debug("network_get(): netid=%s, params=%s" % (network_id, params))
    network = quantumclient(request).show_network(network_id,
                                                  **params).get('network')
    # Since the number of subnets per network must be small,
    # call subnet_get() for each subnet instead of calling
    # subnet_list() once.
    if expand_subnet:
        network['subnets'] = [subnet_get(request, sid)
                              for sid in network['subnets']]
    return Network(network)


def network_create(request, **kwargs):
    """
    Create a subnet on a specified network.
    :param request: request context
    :param tenant_id: (optional) tenant id of the network created
    :param name: (optional) name of the network created
    :returns: Subnet object
    """
    LOG.debug("network_create(): kwargs = %s" % kwargs)
    body = {'network': kwargs}
    network = quantumclient(request).create_network(body=body).get('network')
    return Network(network)


def network_modify(request, network_id, **kwargs):
    LOG.debug("network_modify(): netid=%s, params=%s" % (network_id, kwargs))
    body = {'network': kwargs}
    network = quantumclient(request).update_network(network_id,
                                                    body=body).get('network')
    return Network(network)


def network_delete(request, network_id):
    LOG.debug("network_delete(): netid=%s" % network_id)
    quantumclient(request).delete_network(network_id)


def subnet_list(request, **params):
    LOG.debug("subnet_list(): params=%s" % (params))
    subnets = quantumclient(request).list_subnets(**params).get('subnets')
    return [Subnet(s) for s in subnets]


def subnet_get(request, subnet_id, **params):
    LOG.debug("subnet_get(): subnetid=%s, params=%s" % (subnet_id, params))
    subnet = quantumclient(request).show_subnet(subnet_id,
                                                **params).get('subnet')
    return Subnet(subnet)


def subnet_create(request, network_id, cidr, ip_version, **kwargs):
    """
    Create a subnet on a specified network.
    :param request: request context
    :param network_id: network id a subnet is created on
    :param cidr: subnet IP address range
    :param ip_version: IP version (4 or 6)
    :param gateway_ip: (optional) IP address of gateway
    :param tenant_id: (optional) tenant id of the subnet created
    :param name: (optional) name of the subnet created
    :returns: Subnet object
    """
    LOG.debug("subnet_create(): netid=%s, cidr=%s, ipver=%d, kwargs=%s"
              % (network_id, cidr, ip_version, kwargs))
    body = {'subnet':
                {'network_id': network_id,
                 'ip_version': ip_version,
                 'cidr': cidr}}
    body['subnet'].update(kwargs)
    subnet = quantumclient(request).create_subnet(body=body).get('subnet')
    return Subnet(subnet)


def subnet_modify(request, subnet_id, **kwargs):
    LOG.debug("subnet_modify(): subnetid=%s, kwargs=%s" % (subnet_id, kwargs))
    body = {'subnet': kwargs}
    subnet = quantumclient(request).update_subnet(subnet_id,
                                                  body=body).get('subnet')
    return Subnet(subnet)


def subnet_delete(request, subnet_id):
    LOG.debug("subnet_delete(): subnetid=%s" % subnet_id)
    quantumclient(request).delete_subnet(subnet_id)


def port_list(request, **params):
    LOG.debug("port_list(): params=%s" % (params))
    ports = quantumclient(request).list_ports(**params).get('ports')
    return [Port(p) for p in ports]


def port_get(request, port_id, **params):
    LOG.debug("port_get(): portid=%s, params=%s" % (port_id, params))
    port = quantumclient(request).show_port(port_id, **params).get('port')
    return Port(port)


def port_create(request, network_id, **kwargs):
    """
    Create a port on a specified network.
    :param request: request context
    :param network_id: network id a subnet is created on
    :param device_id: (optional) device id attached to the port
    :param tenant_id: (optional) tenant id of the port created
    :param name: (optional) name of the port created
    :returns: Port object
    """
    LOG.debug("port_create(): netid=%s, kwargs=%s" % (network_id, kwargs))
    body = {'port': {'network_id': network_id}}
    body['port'].update(kwargs)
    port = quantumclient(request).create_port(body=body).get('port')
    return Port(port)


def port_delete(request, port_id):
    LOG.debug("port_delete(): portid=%s" % port_id)
    quantumclient(request).delete_port(port_id)


def port_modify(request, port_id, **kwargs):
    LOG.debug("port_modify(): portid=%s, kwargs=%s" % (port_id, kwargs))
    body = {'port': kwargs}
    port = quantumclient(request).update_port(port_id, body=body).get('port')
    return Port(port)


def router_create(request, **kwargs):
    LOG.debug("router_create():, kwargs=%s" % kwargs)
    body = {'router': {}}
    body['router'].update(kwargs)
    router = quantumclient(request).create_router(body=body).get('router')
    return Router(router)


def router_get(request, router_id, **params):
    router = quantumclient(request).show_router(router_id,
                                                **params).get('router')
    return Router(router)


def router_list(request, **params):
    routers = quantumclient(request).list_routers(**params).get('routers')
    return [Router(r) for r in routers]


def router_delete(request, router_id):
    quantumclient(request).delete_router(router_id)


def router_add_interface(request, router_id, subnet_id=None, port_id=None):
    body = {}
    if subnet_id:
        body['subnet_id'] = subnet_id
    if port_id:
        body['port_id'] = port_id
    quantumclient(request).add_interface_router(router_id, body)


def router_remove_interface(request, router_id, subnet_id=None, port_id=None):
    body = {}
    if subnet_id:
        body['subnet_id'] = subnet_id
    if port_id:
        body['port_id'] = port_id
    quantumclient(request).remove_interface_router(router_id, body)


def router_add_gateway(request, router_id, network_id):
    body = {'network_id': network_id}
    quantumclient(request).add_gateway_router(router_id, body)


def router_remove_gateway(request, router_id):
    quantumclient(request).remove_gateway_router(router_id)
