# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
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

from django import http
from django.core.urlresolvers import reverse
from django.utils.html import escape

from mox import IsA
import netaddr

from openstack_dashboard import api
from openstack_dashboard.test import helpers as test
from .workflows import CreateNetwork


INDEX_URL = reverse('horizon:project:networks:index')


def form_data_subnet(subnet,
                     name=None, cidr=None, ip_version=None,
                     gateway_ip='', enable_dhcp=None,
                     allocation_pools=None,
                     dns_nameservers=None,
                     host_routes=None):
    def get_value(value, default):
        return default if value is None else value

    data = {}
    data['subnet_name'] = get_value(name, subnet.name)
    data['cidr'] = get_value(cidr, subnet.cidr)
    data['ip_version'] = get_value(ip_version, subnet.ip_version)

    gateway_ip = subnet.gateway_ip if gateway_ip == '' else gateway_ip
    data['gateway_ip'] = gateway_ip or ''
    data['no_gateway'] = (gateway_ip is None)

    data['enable_dhcp'] = get_value(enable_dhcp, subnet.enable_dhcp)

    pools = get_value(allocation_pools, subnet.allocation_pools)
    data['allocation_pools'] = _str_allocation_pools(pools)
    nameservers = get_value(dns_nameservers, subnet.dns_nameservers)
    data['dns_nameservers'] = _str_dns_nameservers(nameservers)
    routes = get_value(host_routes, subnet.host_routes)
    data['host_routes'] = _str_host_routes(routes)

    return data


def form_data_no_subnet():
    return {'subnet_name': '',
            'cidr': '',
            'ip_version': 4,
            'gateway_ip': '',
            'no_gateway': False,
            'enable_dhcp': True,
            'allocation_pools': '',
            'dns_nameservers': '',
            'host_routes': ''}


def _str_allocation_pools(allocation_pools):
    if isinstance(allocation_pools, str):
        return allocation_pools
    return '\n'.join(['%s,%s' % (pool['start'], pool['end'])
                      for pool in allocation_pools])


def _str_dns_nameservers(dns_nameservers):
    if isinstance(dns_nameservers, str):
        return dns_nameservers
    return '\n'.join(dns_nameservers)


def _str_host_routes(host_routes):
    if isinstance(host_routes, str):
        return host_routes
    return '\n'.join(['%s,%s' % (route['destination'], route['nexthop'])
                      for route in host_routes])


class NetworkTests(test.TestCase):

    @test.create_stubs({api.quantum: ('network_list',)})
    def test_index(self):
        api.quantum.network_list(
            IsA(http.HttpRequest),
            tenant_id=self.tenant.id,
            shared=False).AndReturn(self.networks.list())
        api.quantum.network_list(
            IsA(http.HttpRequest),
            shared=True).AndReturn([])

        self.mox.ReplayAll()

        res = self.client.get(INDEX_URL)

        self.assertTemplateUsed(res, 'project/networks/index.html')
        networks = res.context['networks_table'].data
        self.assertItemsEqual(networks, self.networks.list())

    @test.create_stubs({api.quantum: ('network_list',)})
    def test_index_network_list_exception(self):
        api.quantum.network_list(
            IsA(http.HttpRequest),
            tenant_id=self.tenant.id,
            shared=False).AndRaise(self.exceptions.quantum)
        self.mox.ReplayAll()

        res = self.client.get(INDEX_URL)

        self.assertTemplateUsed(res, 'project/networks/index.html')
        self.assertEqual(len(res.context['networks_table'].data), 0)
        self.assertMessageCount(res, error=1)

    @test.create_stubs({api.quantum: ('network_get',
                                      'subnet_list',
                                      'port_list',)})
    def test_network_detail(self):
        network_id = self.networks.first().id
        api.quantum.network_get(IsA(http.HttpRequest), network_id)\
            .AndReturn(self.networks.first())
        api.quantum.subnet_list(IsA(http.HttpRequest), network_id=network_id)\
            .AndReturn([self.subnets.first()])
        api.quantum.port_list(IsA(http.HttpRequest), network_id=network_id)\
            .AndReturn([self.ports.first()])
        api.quantum.network_get(IsA(http.HttpRequest), network_id)\
            .AndReturn(self.networks.first())

        self.mox.ReplayAll()

        res = self.client.get(reverse('horizon:project:networks:detail',
                                      args=[network_id]))

        self.assertTemplateUsed(res, 'project/networks/detail.html')
        subnets = res.context['subnets_table'].data
        ports = res.context['ports_table'].data
        self.assertItemsEqual(subnets, [self.subnets.first()])
        self.assertItemsEqual(ports, [self.ports.first()])

    @test.create_stubs({api.quantum: ('network_get',
                                      'subnet_list',
                                      'port_list',)})
    def test_network_detail_network_exception(self):
        network_id = self.networks.first().id
        api.quantum.network_get(IsA(http.HttpRequest), network_id)\
            .AndRaise(self.exceptions.quantum)
        self.mox.ReplayAll()

        url = reverse('horizon:project:networks:detail', args=[network_id])
        res = self.client.get(url)

        redir_url = INDEX_URL
        self.assertRedirectsNoFollow(res, redir_url)

    @test.create_stubs({api.quantum: ('network_get',
                                      'subnet_list',
                                      'port_list',)})
    def test_network_detail_subnet_exception(self):
        network_id = self.networks.first().id
        api.quantum.network_get(IsA(http.HttpRequest), network_id).\
            AndReturn(self.networks.first())
        api.quantum.subnet_list(IsA(http.HttpRequest), network_id=network_id).\
            AndRaise(self.exceptions.quantum)
        api.quantum.port_list(IsA(http.HttpRequest), network_id=network_id).\
            AndReturn([self.ports.first()])
        # Called from SubnetTable
        api.quantum.network_get(IsA(http.HttpRequest), network_id).\
            AndReturn(self.networks.first())

        self.mox.ReplayAll()

        res = self.client.get(reverse('horizon:project:networks:detail',
                                      args=[network_id]))

        self.assertTemplateUsed(res, 'project/networks/detail.html')
        subnets = res.context['subnets_table'].data
        ports = res.context['ports_table'].data
        self.assertEqual(len(subnets), 0)
        self.assertItemsEqual(ports, [self.ports.first()])

    @test.create_stubs({api.quantum: ('network_get',
                                      'subnet_list',
                                      'port_list',)})
    def test_network_detail_port_exception(self):
        network_id = self.networks.first().id
        api.quantum.network_get(IsA(http.HttpRequest), network_id).\
            AndReturn(self.networks.first())
        api.quantum.subnet_list(IsA(http.HttpRequest), network_id=network_id).\
            AndReturn([self.subnets.first()])
        api.quantum.port_list(IsA(http.HttpRequest), network_id=network_id).\
            AndRaise(self.exceptions.quantum)
        # Called from SubnetTable
        api.quantum.network_get(IsA(http.HttpRequest), network_id).\
            AndReturn(self.networks.first())

        self.mox.ReplayAll()

        res = self.client.get(reverse('horizon:project:networks:detail',
                                      args=[network_id]))

        self.assertTemplateUsed(res, 'project/networks/detail.html')
        subnets = res.context['subnets_table'].data
        ports = res.context['ports_table'].data
        self.assertItemsEqual(subnets, [self.subnets.first()])
        self.assertEqual(len(ports), 0)

    def test_network_create_get(self):
        # no api methods are called.
        self.mox.ReplayAll()

        url = reverse('horizon:project:networks:create')
        res = self.client.get(url)

        workflow = res.context['workflow']
        self.assertTemplateUsed(res, 'project/networks/create.html')
        self.assertEqual(workflow.name, CreateNetwork.name)
        expected_objs = ['<CreateNetworkInfo: createnetworkinfoaction>',
                         '<CreateSubnetInfo: createsubnetinfoaction>',
                         '<CreateSubnetDetail: createsubnetdetailaction>']
        self.assertQuerysetEqual(workflow.steps, expected_objs)

    @test.create_stubs({api.quantum: ('network_create',)})
    def test_network_create_post(self):
        network = self.networks.first()
        api.quantum.network_create(IsA(http.HttpRequest), name=network.name,
                                   admin_state_up=network.admin_state_up)\
            .AndReturn(network)
        self.mox.ReplayAll()

        form_data = {'net_name': network.name,
                     'admin_state': network.admin_state_up,
                     # subnet
                     'with_subnet': False}
        form_data.update(form_data_no_subnet())
        url = reverse('horizon:project:networks:create')
        res = self.client.post(url, form_data)

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({api.quantum: ('network_create',
                                      'subnet_create',)})
    def test_network_create_post_with_subnet(self):
        network = self.networks.first()
        subnet = self.subnets.first()
        api.quantum.network_create(IsA(http.HttpRequest), name=network.name,
                                   admin_state_up=network.admin_state_up)\
            .AndReturn(network)
        api.quantum.subnet_create(IsA(http.HttpRequest),
                                  network_id=network.id,
                                  name=subnet.name,
                                  cidr=subnet.cidr,
                                  ip_version=subnet.ip_version,
                                  gateway_ip=subnet.gateway_ip,
                                  enable_dhcp=subnet.enable_dhcp)\
            .AndReturn(subnet)
        self.mox.ReplayAll()

        form_data = {'net_name': network.name,
                     'admin_state': network.admin_state_up,
                     'with_subnet': True}
        form_data.update(form_data_subnet(subnet, allocation_pools=[]))
        url = reverse('horizon:project:networks:create')
        res = self.client.post(url, form_data)

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({api.quantum: ('network_create',)})
    def test_network_create_post_network_exception(self):
        network = self.networks.first()
        api.quantum.network_create(IsA(http.HttpRequest), name=network.name,
                                   admin_state_up=network.admin_state_up)\
            .AndRaise(self.exceptions.quantum)
        self.mox.ReplayAll()

        form_data = {'net_name': network.name,
                     'admin_state': network.admin_state_up,
                     # subnet
                     'with_subnet': False}
        form_data.update(form_data_no_subnet())
        url = reverse('horizon:project:networks:create')
        res = self.client.post(url, form_data)

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({api.quantum: ('network_create',)})
    def test_network_create_post_with_subnet_network_exception(self):
        network = self.networks.first()
        subnet = self.subnets.first()
        api.quantum.network_create(IsA(http.HttpRequest), name=network.name,
                                   admin_state_up=network.admin_state_up)\
            .AndRaise(self.exceptions.quantum)
        self.mox.ReplayAll()

        form_data = {'net_name': network.name,
                     'admin_state': network.admin_state_up,
                     'with_subnet': True}
        form_data.update(form_data_subnet(subnet, allocation_pools=[]))
        url = reverse('horizon:project:networks:create')
        res = self.client.post(url, form_data)

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({api.quantum: ('network_create',
                                      'network_delete',
                                      'subnet_create',)})
    def test_network_create_post_with_subnet_subnet_exception(self):
        network = self.networks.first()
        subnet = self.subnets.first()
        api.quantum.network_create(IsA(http.HttpRequest), name=network.name,
                                   admin_state_up=network.admin_state_up)\
            .AndReturn(network)
        api.quantum.subnet_create(IsA(http.HttpRequest),
                                  network_id=network.id,
                                  name=subnet.name,
                                  cidr=subnet.cidr,
                                  ip_version=subnet.ip_version,
                                  gateway_ip=subnet.gateway_ip,
                                  enable_dhcp=subnet.enable_dhcp)\
            .AndRaise(self.exceptions.quantum)
        api.quantum.network_delete(IsA(http.HttpRequest),
                                   network.id)
        self.mox.ReplayAll()

        form_data = {'net_name': network.name,
                     'admin_state': network.admin_state_up,
                     'with_subnet': True}
        form_data.update(form_data_subnet(subnet, allocation_pools=[]))
        url = reverse('horizon:project:networks:create')
        res = self.client.post(url, form_data)

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    def test_network_create_post_with_subnet_nocidr(self):
        network = self.networks.first()
        subnet = self.subnets.first()
        self.mox.ReplayAll()

        form_data = {'net_name': network.name,
                     'admin_state': network.admin_state_up,
                     'with_subnet': True}
        form_data.update(form_data_subnet(subnet, cidr='',
                                          allocation_pools=[]))
        url = reverse('horizon:project:networks:create')
        res = self.client.post(url, form_data)

        self.assertContains(res, escape('Specify "Network Address" or '
                                        'clear "Create Subnet" checkbox.'))

    def test_network_create_post_with_subnet_cidr_without_mask(self):
        network = self.networks.first()
        subnet = self.subnets.first()

        form_data = {'net_name': network.name,
                     'admin_state': network.admin_state_up,
                     'with_subnet': True}
        form_data.update(form_data_subnet(subnet, cidr='10.0.0.0',
                                          allocation_pools=[]))
        url = reverse('horizon:project:networks:create')
        res = self.client.post(url, form_data)

        expected_msg = "The subnet in the Network Address is too small (/32)."
        self.assertContains(res, expected_msg)

    def test_network_create_post_with_subnet_cidr_inconsistent(self):
        network = self.networks.first()
        subnet = self.subnets.first()
        self.mox.ReplayAll()

        # dummy IPv6 address
        cidr = '2001:0DB8:0:CD30:123:4567:89AB:CDEF/60'
        form_data = {'net_name': network.name,
                     'admin_state': network.admin_state_up,
                     'with_subnet': True}
        form_data.update(form_data_subnet(subnet, cidr=cidr,
                                          allocation_pools=[]))
        url = reverse('horizon:project:networks:create')
        res = self.client.post(url, form_data)

        expected_msg = 'Network Address and IP version are inconsistent.'
        self.assertContains(res, expected_msg)

    def test_network_create_post_with_subnet_gw_inconsistent(self):
        network = self.networks.first()
        subnet = self.subnets.first()
        self.mox.ReplayAll()

        # dummy IPv6 address
        gateway_ip = '2001:0DB8:0:CD30:123:4567:89AB:CDEF'
        form_data = {'net_name': network.name,
                     'admin_state': network.admin_state_up,
                     'with_subnet': True}
        form_data.update(form_data_subnet(subnet, gateway_ip=gateway_ip,
                                          allocation_pools=[]))
        url = reverse('horizon:project:networks:create')
        res = self.client.post(url, form_data)

        self.assertContains(res, 'Gateway IP and IP version are inconsistent.')

    @test.create_stubs({api.quantum: ('network_get',)})
    def test_network_update_get(self):
        network = self.networks.first()
        api.quantum.network_get(IsA(http.HttpRequest), network.id)\
            .AndReturn(network)

        self.mox.ReplayAll()

        url = reverse('horizon:project:networks:update', args=[network.id])
        res = self.client.get(url)

        self.assertTemplateUsed(res, 'project/networks/update.html')

    @test.create_stubs({api.quantum: ('network_get',)})
    def test_network_update_get_exception(self):
        network = self.networks.first()
        api.quantum.network_get(IsA(http.HttpRequest), network.id)\
            .AndRaise(self.exceptions.quantum)

        self.mox.ReplayAll()

        url = reverse('horizon:project:networks:update', args=[network.id])
        res = self.client.get(url)

        redir_url = INDEX_URL
        self.assertRedirectsNoFollow(res, redir_url)

    @test.create_stubs({api.quantum: ('network_modify',
                                      'network_get',)})
    def test_network_update_post(self):
        network = self.networks.first()
        api.quantum.network_modify(IsA(http.HttpRequest), network.id,
                                   name=network.name,
                                   admin_state_up=network.admin_state_up)\
            .AndReturn(network)
        api.quantum.network_get(IsA(http.HttpRequest), network.id)\
            .AndReturn(network)
        self.mox.ReplayAll()

        form_data = {'network_id': network.id,
                     'name': network.name,
                     'admin_state': network.admin_state_up,
                     'tenant_id': network.tenant_id}
        url = reverse('horizon:project:networks:update', args=[network.id])
        res = self.client.post(url, form_data)

        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({api.quantum: ('network_modify',
                                      'network_get',)})
    def test_network_update_post_exception(self):
        network = self.networks.first()
        api.quantum.network_modify(IsA(http.HttpRequest), network.id,
                                   name=network.name,
                                   admin_state_up=network.admin_state_up)\
            .AndRaise(self.exceptions.quantum)
        api.quantum.network_get(IsA(http.HttpRequest), network.id)\
            .AndReturn(network)
        self.mox.ReplayAll()

        form_data = {'network_id': network.id,
                     'name': network.name,
                     'admin_state': network.admin_state_up,
                     'tenant_id': network.tenant_id}
        url = reverse('horizon:project:networks:update', args=[network.id])
        res = self.client.post(url, form_data)

        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({api.quantum: ('network_list',
                                      'subnet_list',
                                      'network_delete')})
    def test_delete_network_no_subnet(self):
        network = self.networks.first()
        api.quantum.network_list(IsA(http.HttpRequest),
                                 tenant_id=network.tenant_id,
                                 shared=False)\
            .AndReturn([network])
        api.quantum.network_list(IsA(http.HttpRequest),
                                 shared=True)\
            .AndReturn([])
        api.quantum.subnet_list(IsA(http.HttpRequest), network_id=network.id)\
            .AndReturn([])
        api.quantum.network_delete(IsA(http.HttpRequest), network.id)

        self.mox.ReplayAll()

        form_data = {'action': 'networks__delete__%s' % network.id}
        res = self.client.post(INDEX_URL, form_data)

        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({api.quantum: ('network_list',
                                      'subnet_list',
                                      'network_delete',
                                      'subnet_delete')})
    def test_delete_network_with_subnet(self):
        network = self.networks.first()
        subnet = self.subnets.first()
        api.quantum.network_list(IsA(http.HttpRequest),
                                 tenant_id=network.tenant_id,
                                 shared=False)\
            .AndReturn([network])
        api.quantum.network_list(IsA(http.HttpRequest), shared=True)\
            .AndReturn([])
        api.quantum.subnet_list(IsA(http.HttpRequest), network_id=network.id)\
            .AndReturn([subnet])
        api.quantum.subnet_delete(IsA(http.HttpRequest), subnet.id)
        api.quantum.network_delete(IsA(http.HttpRequest), network.id)

        self.mox.ReplayAll()

        form_data = {'action': 'networks__delete__%s' % network.id}
        res = self.client.post(INDEX_URL, form_data)

        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({api.quantum: ('network_list',
                                      'subnet_list',
                                      'network_delete',
                                      'subnet_delete')})
    def test_delete_network_exception(self):
        network = self.networks.first()
        subnet = self.subnets.first()
        api.quantum.network_list(IsA(http.HttpRequest),
                                 tenant_id=network.tenant_id,
                                 shared=False)\
            .AndReturn([network])
        api.quantum.network_list(IsA(http.HttpRequest),
                                 shared=True)\
            .AndReturn([])
        api.quantum.subnet_list(IsA(http.HttpRequest), network_id=network.id)\
            .AndReturn([subnet])
        api.quantum.subnet_delete(IsA(http.HttpRequest), subnet.id)
        api.quantum.network_delete(IsA(http.HttpRequest), network.id)\
            .AndRaise(self.exceptions.quantum)

        self.mox.ReplayAll()

        form_data = {'action': 'networks__delete__%s' % network.id}
        res = self.client.post(INDEX_URL, form_data)

        self.assertRedirectsNoFollow(res, INDEX_URL)


class NetworkSubnetTests(test.TestCase):

    @test.create_stubs({api.quantum: ('subnet_get',)})
    def test_subnet_detail(self):
        subnet = self.subnets.first()
        api.quantum.subnet_get(IsA(http.HttpRequest), subnet.id)\
            .AndReturn(self.subnets.first())

        self.mox.ReplayAll()

        url = reverse('horizon:project:networks:subnets:detail',
                      args=[subnet.id])
        res = self.client.get(url)

        self.assertTemplateUsed(res, 'project/networks/subnets/detail.html')
        self.assertEqual(res.context['subnet'].id, subnet.id)

    @test.create_stubs({api.quantum: ('subnet_get',)})
    def test_subnet_detail_exception(self):
        subnet = self.subnets.first()
        api.quantum.subnet_get(IsA(http.HttpRequest), subnet.id)\
            .AndRaise(self.exceptions.quantum)

        self.mox.ReplayAll()

        url = reverse('horizon:project:networks:subnets:detail',
                      args=[subnet.id])
        res = self.client.get(url)

        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({api.quantum: ('network_get',)})
    def test_subnet_create_get(self):
        network = self.networks.first()
        api.quantum.network_get(IsA(http.HttpRequest),
                                network.id)\
            .AndReturn(self.networks.first())
        self.mox.ReplayAll()

        url = reverse('horizon:project:networks:addsubnet',
                      args=[network.id])
        res = self.client.get(url)

        self.assertTemplateUsed(res, 'project/networks/subnets/create.html')

    @test.create_stubs({api.quantum: ('network_get',
                                      'subnet_create',)})
    def test_subnet_create_post(self):
        network = self.networks.first()
        subnet = self.subnets.first()
        api.quantum.network_get(IsA(http.HttpRequest),
                                network.id)\
            .AndReturn(self.networks.first())
        api.quantum.subnet_create(IsA(http.HttpRequest),
                                  network_id=network.id,
                                  name=subnet.name,
                                  cidr=subnet.cidr,
                                  ip_version=subnet.ip_version,
                                  gateway_ip=subnet.gateway_ip,
                                  enable_dhcp=subnet.enable_dhcp,
                                  allocation_pools=subnet.allocation_pools)\
            .AndReturn(subnet)
        self.mox.ReplayAll()

        form_data = form_data_subnet(subnet)
        url = reverse('horizon:project:networks:addsubnet',
                      args=[subnet.network_id])
        res = self.client.post(url, form_data)

        self.assertNoFormErrors(res)
        redir_url = reverse('horizon:project:networks:detail',
                            args=[subnet.network_id])
        self.assertRedirectsNoFollow(res, redir_url)

    @test.create_stubs({api.quantum: ('network_get',
                                      'subnet_create',)})
    def test_subnet_create_post_with_additional_attributes(self):
        network = self.networks.list()[1]
        subnet = self.subnets.list()[1]
        api.quantum.network_get(IsA(http.HttpRequest),
                                network.id)\
            .AndReturn(self.networks.first())
        api.quantum.subnet_create(IsA(http.HttpRequest),
                                  network_id=network.id,
                                  name=subnet.name,
                                  cidr=subnet.cidr,
                                  ip_version=subnet.ip_version,
                                  gateway_ip=subnet.gateway_ip,
                                  enable_dhcp=subnet.enable_dhcp,
                                  allocation_pools=subnet.allocation_pools,
                                  dns_nameservers=subnet.dns_nameservers,
                                  host_routes=subnet.host_routes)\
            .AndReturn(subnet)
        self.mox.ReplayAll()

        form_data = form_data_subnet(subnet)
        url = reverse('horizon:project:networks:addsubnet',
                      args=[subnet.network_id])
        res = self.client.post(url, form_data)

        self.assertNoFormErrors(res)
        redir_url = reverse('horizon:project:networks:detail',
                            args=[subnet.network_id])
        self.assertRedirectsNoFollow(res, redir_url)

    @test.create_stubs({api.quantum: ('network_get',
                                      'subnet_create',)})
    def test_subnet_create_post_with_additional_attributes(self):
        network = self.networks.first()
        subnet = self.subnets.first()
        api.quantum.network_get(IsA(http.HttpRequest),
                                network.id)\
            .AndReturn(self.networks.first())
        api.quantum.subnet_create(IsA(http.HttpRequest),
                                  network_id=network.id,
                                  name=subnet.name,
                                  cidr=subnet.cidr,
                                  ip_version=subnet.ip_version,
                                  gateway_ip=None,
                                  enable_dhcp=subnet.enable_dhcp,
                                  allocation_pools=subnet.allocation_pools)\
            .AndReturn(subnet)
        self.mox.ReplayAll()

        form_data = form_data_subnet(subnet, gateway_ip=None)
        url = reverse('horizon:project:networks:addsubnet',
                      args=[subnet.network_id])
        res = self.client.post(url, form_data)

        self.assertNoFormErrors(res)
        redir_url = reverse('horizon:project:networks:detail',
                            args=[subnet.network_id])
        self.assertRedirectsNoFollow(res, redir_url)

    @test.create_stubs({api.quantum: ('network_get',
                                      'subnet_create',)})
    def test_subnet_create_post_network_exception(self):
        network = self.networks.first()
        subnet = self.subnets.first()
        api.quantum.network_get(IsA(http.HttpRequest),
                                network.id)\
            .AndRaise(self.exceptions.quantum)
        self.mox.ReplayAll()

        form_data = form_data_subnet(subnet,
                                     allocation_pools=[])
        url = reverse('horizon:project:networks:addsubnet',
                      args=[subnet.network_id])
        res = self.client.post(url, form_data)

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({api.quantum: ('network_get',
                                      'subnet_create',)})
    def test_subnet_create_post_subnet_exception(self):
        network = self.networks.first()
        subnet = self.subnets.first()
        api.quantum.network_get(IsA(http.HttpRequest),
                                network.id)\
            .AndReturn(self.networks.first())
        api.quantum.subnet_create(IsA(http.HttpRequest),
                                  network_id=network.id,
                                  name=subnet.name,
                                  cidr=subnet.cidr,
                                  ip_version=subnet.ip_version,
                                  gateway_ip=subnet.gateway_ip,
                                  enable_dhcp=subnet.enable_dhcp)\
            .AndRaise(self.exceptions.quantum)
        self.mox.ReplayAll()

        form_data = form_data_subnet(subnet,
                                     allocation_pools=[])
        url = reverse('horizon:project:networks:addsubnet',
                      args=[subnet.network_id])
        res = self.client.post(url, form_data)

        redir_url = reverse('horizon:project:networks:detail',
                            args=[subnet.network_id])
        self.assertRedirectsNoFollow(res, redir_url)

    @test.create_stubs({api.quantum: ('network_get',)})
    def test_subnet_create_post_cidr_inconsistent(self):
        network = self.networks.first()
        subnet = self.subnets.first()
        api.quantum.network_get(IsA(http.HttpRequest),
                                network.id)\
            .AndReturn(self.networks.first())
        self.mox.ReplayAll()

        # dummy IPv6 address
        cidr = '2001:0DB8:0:CD30:123:4567:89AB:CDEF/60'
        form_data = form_data_subnet(subnet, cidr=cidr,
                                     allocation_pools=[])
        url = reverse('horizon:project:networks:addsubnet',
                      args=[subnet.network_id])
        res = self.client.post(url, form_data)

        expected_msg = 'Network Address and IP version are inconsistent.'
        self.assertFormErrors(res, 1, expected_msg)
        self.assertTemplateUsed(res,
                                'project/networks/subnets/create.html')

    @test.create_stubs({api.quantum: ('network_get',)})
    def test_subnet_create_post_gw_inconsistent(self):
        network = self.networks.first()
        subnet = self.subnets.first()
        api.quantum.network_get(IsA(http.HttpRequest),
                                network.id)\
            .AndReturn(self.networks.first())
        self.mox.ReplayAll()

        # dummy IPv6 address
        gateway_ip = '2001:0DB8:0:CD30:123:4567:89AB:CDEF'
        form_data = form_data_subnet(subnet, gateway_ip=gateway_ip,
                                     allocation_pools=[])
        url = reverse('horizon:project:networks:addsubnet',
                      args=[subnet.network_id])
        res = self.client.post(url, form_data)

        self.assertContains(res, 'Gateway IP and IP version are inconsistent.')

    @test.create_stubs({api.quantum: ('network_get',)})
    def test_subnet_create_post_invalid_pools_start_only(self):
        network = self.networks.first()
        subnet = self.subnets.first()
        api.quantum.network_get(IsA(http.HttpRequest),
                                network.id).AndReturn(network)
        self.mox.ReplayAll()

        # Start only allocation_pools
        allocation_pools = '10.0.0.2'
        form_data = form_data_subnet(subnet,
                                     allocation_pools=allocation_pools)
        url = reverse('horizon:project:networks:addsubnet',
                      args=[subnet.network_id])
        res = self.client.post(url, form_data)

        self.assertContains(res,
                            'Start and end addresses must be specified '
                            '(value=%s)' % allocation_pools)

    @test.create_stubs({api.quantum: ('network_get',)})
    def test_subnet_create_post_invalid_pools_three_entries(self):
        network = self.networks.first()
        subnet = self.subnets.first()
        api.quantum.network_get(IsA(http.HttpRequest),
                                network.id).AndReturn(network)
        self.mox.ReplayAll()

        # pool with three entries
        allocation_pools = '10.0.0.2,10.0.0.3,10.0.0.4'
        form_data = form_data_subnet(subnet,
                                     allocation_pools=allocation_pools)
        url = reverse('horizon:project:networks:addsubnet',
                      args=[subnet.network_id])
        res = self.client.post(url, form_data)

        self.assertContains(res,
                            'Start and end addresses must be specified '
                            '(value=%s)' % allocation_pools)

    @test.create_stubs({api.quantum: ('network_get',)})
    def test_subnet_create_post_invalid_pools_invalid_address(self):
        network = self.networks.first()
        subnet = self.subnets.first()
        api.quantum.network_get(IsA(http.HttpRequest),
                                network.id).AndReturn(network)
        self.mox.ReplayAll()

        # end address is not a valid IP address
        allocation_pools = '10.0.0.2,invalid_address'
        form_data = form_data_subnet(subnet,
                                     allocation_pools=allocation_pools)
        url = reverse('horizon:project:networks:addsubnet',
                      args=[subnet.network_id])
        res = self.client.post(url, form_data)

        self.assertContains(res,
                            'allocation_pools: Invalid IP address '
                            '(value=%s)' % allocation_pools.split(',')[1])

    @test.create_stubs({api.quantum: ('network_get',)})
    def test_subnet_create_post_invalid_pools_ip_network(self):
        network = self.networks.first()
        subnet = self.subnets.first()
        api.quantum.network_get(IsA(http.HttpRequest),
                                network.id).AndReturn(network)
        self.mox.ReplayAll()

        # start address is CIDR
        allocation_pools = '10.0.0.2/24,10.0.0.5'
        form_data = form_data_subnet(subnet,
                                     allocation_pools=allocation_pools)
        url = reverse('horizon:project:networks:addsubnet',
                      args=[subnet.network_id])
        res = self.client.post(url, form_data)

        self.assertContains(res,
                            'allocation_pools: Invalid IP address '
                            '(value=%s)' % allocation_pools.split(',')[0])

    @test.create_stubs({api.quantum: ('network_get',)})
    def test_subnet_create_post_invalid_pools_start_larger_than_end(self):
        network = self.networks.first()
        subnet = self.subnets.first()
        api.quantum.network_get(IsA(http.HttpRequest),
                                network.id).AndReturn(network)
        self.mox.ReplayAll()

        # start address is larger than end address
        allocation_pools = '10.0.0.254,10.0.0.2'
        form_data = form_data_subnet(subnet,
                                     allocation_pools=allocation_pools)
        url = reverse('horizon:project:networks:addsubnet',
                      args=[subnet.network_id])
        res = self.client.post(url, form_data)

        self.assertContains(res,
                            'Start address is larger than end address '
                            '(value=%s)' % allocation_pools)

    @test.create_stubs({api.quantum: ('network_get',)})
    def test_subnet_create_post_invalid_nameservers(self):
        network = self.networks.first()
        subnet = self.subnets.first()
        api.quantum.network_get(IsA(http.HttpRequest),
                                network.id).AndReturn(network)
        self.mox.ReplayAll()

        # invalid DNS server address
        dns_nameservers = ['192.168.0.2', 'invalid_address']
        form_data = form_data_subnet(subnet, dns_nameservers=dns_nameservers,
                                     allocation_pools=[])
        url = reverse('horizon:project:networks:addsubnet',
                      args=[subnet.network_id])
        res = self.client.post(url, form_data)

        self.assertContains(res,
                            'dns_nameservers: Invalid IP address '
                            '(value=%s)' % dns_nameservers[1])

    @test.create_stubs({api.quantum: ('network_get',)})
    def test_subnet_create_post_invalid_routes_destination_only(self):
        network = self.networks.first()
        subnet = self.subnets.first()
        api.quantum.network_get(IsA(http.HttpRequest),
                                network.id).AndReturn(network)
        self.mox.ReplayAll()

        # Start only host_route
        host_routes = '192.168.0.0/24'
        form_data = form_data_subnet(subnet,
                                     allocation_pools=[],
                                     host_routes=host_routes)
        url = reverse('horizon:project:networks:addsubnet',
                      args=[subnet.network_id])
        res = self.client.post(url, form_data)

        self.assertContains(res,
                            'Host Routes format error: '
                            'Destination CIDR and nexthop must be specified '
                            '(value=%s)' % host_routes)

    @test.create_stubs({api.quantum: ('network_get',)})
    def test_subnet_create_post_invalid_routes_three_entries(self):
        network = self.networks.first()
        subnet = self.subnets.first()
        api.quantum.network_get(IsA(http.HttpRequest),
                                network.id).AndReturn(network)
        self.mox.ReplayAll()

        # host_route with three entries
        host_routes = 'aaaa,bbbb,cccc'
        form_data = form_data_subnet(subnet,
                                     allocation_pools=[],
                                     host_routes=host_routes)
        url = reverse('horizon:project:networks:addsubnet',
                      args=[subnet.network_id])
        res = self.client.post(url, form_data)

        self.assertContains(res,
                            'Host Routes format error: '
                            'Destination CIDR and nexthop must be specified '
                            '(value=%s)' % host_routes)

    @test.create_stubs({api.quantum: ('network_get',)})
    def test_subnet_create_post_invalid_routes_invalid_destination(self):
        network = self.networks.first()
        subnet = self.subnets.first()
        api.quantum.network_get(IsA(http.HttpRequest),
                                network.id).AndReturn(network)
        self.mox.ReplayAll()

        # invalid destination network
        host_routes = '172.16.0.0/64,10.0.0.253'
        form_data = form_data_subnet(subnet,
                                     host_routes=host_routes,
                                     allocation_pools=[])
        url = reverse('horizon:project:networks:addsubnet',
                      args=[subnet.network_id])
        res = self.client.post(url, form_data)

        self.assertContains(res,
                            'host_routes: Invalid IP address '
                            '(value=%s)' % host_routes.split(',')[0])

    @test.create_stubs({api.quantum: ('network_get',)})
    def test_subnet_create_post_invalid_routes_nexthop_ip_network(self):
        network = self.networks.first()
        subnet = self.subnets.first()
        api.quantum.network_get(IsA(http.HttpRequest),
                                network.id).AndReturn(network)
        self.mox.ReplayAll()

        # nexthop is not an IP address
        host_routes = '172.16.0.0/24,10.0.0.253/24'
        form_data = form_data_subnet(subnet,
                                     host_routes=host_routes,
                                     allocation_pools=[])
        url = reverse('horizon:project:networks:addsubnet',
                      args=[subnet.network_id])
        res = self.client.post(url, form_data)

        self.assertContains(res,
                            'host_routes: Invalid IP address '
                            '(value=%s)' % host_routes.split(',')[1])

    @test.create_stubs({api.quantum: ('subnet_modify',
                                      'subnet_get',)})
    def test_subnet_update_post(self):
        subnet = self.subnets.first()
        api.quantum.subnet_get(IsA(http.HttpRequest), subnet.id)\
            .AndReturn(subnet)
        api.quantum.subnet_modify(IsA(http.HttpRequest), subnet.id,
                                  name=subnet.name,
                                  gateway_ip=subnet.gateway_ip,
                                  enable_dhcp=subnet.enable_dhcp)\
            .AndReturn(subnet)
        self.mox.ReplayAll()

        form_data = form_data_subnet(subnet,
                                     allocation_pools=[])
        url = reverse('horizon:project:networks:editsubnet',
                      args=[subnet.network_id, subnet.id])
        res = self.client.post(url, form_data)

        redir_url = reverse('horizon:project:networks:detail',
                            args=[subnet.network_id])
        self.assertRedirectsNoFollow(res, redir_url)

    @test.create_stubs({api.quantum: ('subnet_modify',
                                      'subnet_get',)})
    def test_subnet_update_post(self):
        subnet = self.subnets.first()
        api.quantum.subnet_get(IsA(http.HttpRequest), subnet.id)\
            .AndReturn(subnet)
        api.quantum.subnet_modify(IsA(http.HttpRequest), subnet.id,
                                  name=subnet.name,
                                  gateway_ip=subnet.gateway_ip,
                                  enable_dhcp=subnet.enable_dhcp,
                                  dns_nameservers=[],
                                  host_routes=[])\
            .AndReturn(subnet)
        self.mox.ReplayAll()

        form_data = form_data_subnet(subnet,
                                     allocation_pools=[])
        url = reverse('horizon:project:networks:editsubnet',
                      args=[subnet.network_id, subnet.id])
        res = self.client.post(url, form_data)

        redir_url = reverse('horizon:project:networks:detail',
                            args=[subnet.network_id])
        self.assertRedirectsNoFollow(res, redir_url)

    @test.create_stubs({api.quantum: ('subnet_modify',
                                      'subnet_get',)})
    def test_subnet_update_post_no_gateway(self):
        subnet = self.subnets.first()
        api.quantum.subnet_get(IsA(http.HttpRequest), subnet.id)\
            .AndReturn(subnet)
        api.quantum.subnet_modify(IsA(http.HttpRequest), subnet.id,
                                  name=subnet.name,
                                  gateway_ip=None,
                                  enable_dhcp=subnet.enable_dhcp,
                                  dns_nameservers=[],
                                  host_routes=[])\
            .AndReturn(subnet)
        self.mox.ReplayAll()

        form_data = form_data_subnet(subnet,
                                     gateway_ip=None,
                                     allocation_pools=[])
        url = reverse('horizon:project:networks:editsubnet',
                      args=[subnet.network_id, subnet.id])
        res = self.client.post(url, form_data)

        redir_url = reverse('horizon:project:networks:detail',
                            args=[subnet.network_id])
        self.assertRedirectsNoFollow(res, redir_url)

    @test.create_stubs({api.quantum: ('subnet_modify',
                                      'subnet_get',)})
    def test_subnet_update_post_with_additional_attributes(self):
        subnet = self.subnets.list()[1]
        api.quantum.subnet_get(IsA(http.HttpRequest), subnet.id)\
            .AndReturn(subnet)
        api.quantum.subnet_modify(IsA(http.HttpRequest), subnet.id,
                                  name=subnet.name,
                                  gateway_ip=subnet.gateway_ip,
                                  enable_dhcp=False,
                                  dns_nameservers=subnet.dns_nameservers,
                                  host_routes=subnet.host_routes)\
            .AndReturn(subnet)
        self.mox.ReplayAll()

        form_data = form_data_subnet(subnet,
                                     enable_dhcp=False)
        url = reverse('horizon:project:networks:editsubnet',
                      args=[subnet.network_id, subnet.id])
        res = self.client.post(url, form_data)

        redir_url = reverse('horizon:project:networks:detail',
                            args=[subnet.network_id])
        self.assertRedirectsNoFollow(res, redir_url)

    @test.create_stubs({api.quantum: ('subnet_modify',
                                      'subnet_get',)})
    def test_subnet_update_post_gw_inconsistent(self):
        subnet = self.subnets.first()
        api.quantum.subnet_get(IsA(http.HttpRequest), subnet.id)\
            .AndReturn(subnet)
        self.mox.ReplayAll()

        # dummy IPv6 address
        gateway_ip = '2001:0DB8:0:CD30:123:4567:89AB:CDEF'
        form_data = form_data_subnet(subnet, gateway_ip=gateway_ip,
                                     allocation_pools=[])
        url = reverse('horizon:project:networks:editsubnet',
                      args=[subnet.network_id, subnet.id])
        res = self.client.post(url, form_data)

        self.assertContains(res, 'Gateway IP and IP version are inconsistent.')

    @test.create_stubs({api.quantum: ('subnet_modify',
                                      'subnet_get',)})
    def test_subnet_update_post_invalid_nameservers(self):
        subnet = self.subnets.first()
        api.quantum.subnet_get(IsA(http.HttpRequest), subnet.id)\
            .AndReturn(subnet)
        self.mox.ReplayAll()

        # invalid DNS server address
        dns_nameservers = ['192.168.0.2', 'invalid_address']
        form_data = form_data_subnet(subnet, dns_nameservers=dns_nameservers,
                                     allocation_pools=[])
        url = reverse('horizon:project:networks:editsubnet',
                      args=[subnet.network_id, subnet.id])
        res = self.client.post(url, form_data)

        self.assertContains(res,
                            'dns_nameservers: Invalid IP address '
                            '(value=%s)' % dns_nameservers[1])

    @test.create_stubs({api.quantum: ('subnet_modify',
                                      'subnet_get',)})
    def test_subnet_update_post_invalid_routes_destination_only(self):
        subnet = self.subnets.first()
        api.quantum.subnet_get(IsA(http.HttpRequest), subnet.id)\
            .AndReturn(subnet)
        self.mox.ReplayAll()

        # Start only host_route
        host_routes = '192.168.0.0/24'
        form_data = form_data_subnet(subnet,
                                     allocation_pools=[],
                                     host_routes=host_routes)
        url = reverse('horizon:project:networks:editsubnet',
                      args=[subnet.network_id, subnet.id])
        res = self.client.post(url, form_data)

        self.assertContains(res,
                            'Host Routes format error: '
                            'Destination CIDR and nexthop must be specified '
                            '(value=%s)' % host_routes)

    @test.create_stubs({api.quantum: ('subnet_modify',
                                      'subnet_get',)})
    def test_subnet_update_post_invalid_routes_three_entries(self):
        subnet = self.subnets.first()
        api.quantum.subnet_get(IsA(http.HttpRequest), subnet.id)\
            .AndReturn(subnet)
        self.mox.ReplayAll()

        # host_route with three entries
        host_routes = 'aaaa,bbbb,cccc'
        form_data = form_data_subnet(subnet,
                                     allocation_pools=[],
                                     host_routes=host_routes)
        url = reverse('horizon:project:networks:editsubnet',
                      args=[subnet.network_id, subnet.id])
        res = self.client.post(url, form_data)

        self.assertContains(res,
                            'Host Routes format error: '
                            'Destination CIDR and nexthop must be specified '
                            '(value=%s)' % host_routes)

    @test.create_stubs({api.quantum: ('subnet_modify',
                                      'subnet_get',)})
    def test_subnet_update_post_invalid_routes_invalid_destination(self):
        subnet = self.subnets.first()
        api.quantum.subnet_get(IsA(http.HttpRequest), subnet.id)\
            .AndReturn(subnet)
        self.mox.ReplayAll()

        # invalid destination network
        host_routes = '172.16.0.0/64,10.0.0.253'
        form_data = form_data_subnet(subnet,
                                     host_routes=host_routes,
                                     allocation_pools=[])
        url = reverse('horizon:project:networks:editsubnet',
                      args=[subnet.network_id, subnet.id])
        res = self.client.post(url, form_data)

        self.assertContains(res,
                            'host_routes: Invalid IP address '
                            '(value=%s)' % host_routes.split(',')[0])

    @test.create_stubs({api.quantum: ('subnet_modify',
                                      'subnet_get',)})
    def test_subnet_update_post_invalid_routes_nexthop_ip_network(self):
        subnet = self.subnets.first()
        api.quantum.subnet_get(IsA(http.HttpRequest), subnet.id)\
            .AndReturn(subnet)
        self.mox.ReplayAll()

        # nexthop is not an IP address
        host_routes = '172.16.0.0/24,10.0.0.253/24'
        form_data = form_data_subnet(subnet,
                                     host_routes=host_routes,
                                     allocation_pools=[])
        url = reverse('horizon:project:networks:editsubnet',
                      args=[subnet.network_id, subnet.id])
        res = self.client.post(url, form_data)

        self.assertContains(res,
                            'host_routes: Invalid IP address '
                            '(value=%s)' % host_routes.split(',')[1])

    @test.create_stubs({api.quantum: ('subnet_delete',
                                      'subnet_list',
                                      'network_get',
                                      'port_list',)})
    def test_subnet_delete(self):
        subnet = self.subnets.first()
        network_id = subnet.network_id
        api.quantum.subnet_delete(IsA(http.HttpRequest), subnet.id)
        api.quantum.subnet_list(IsA(http.HttpRequest), network_id=network_id)\
            .AndReturn([self.subnets.first()])
        api.quantum.network_get(IsA(http.HttpRequest), network_id)\
            .AndReturn(self.networks.first())
        api.quantum.port_list(IsA(http.HttpRequest), network_id=network_id)\
            .AndReturn([self.ports.first()])
        # Called from SubnetTable
        api.quantum.network_get(IsA(http.HttpRequest), network_id)\
            .AndReturn(self.networks.first())
        self.mox.ReplayAll()

        form_data = {'action': 'subnets__delete__%s' % subnet.id}
        url = reverse('horizon:project:networks:detail',
                      args=[network_id])
        res = self.client.post(url, form_data)

        self.assertRedirectsNoFollow(res, url)

    @test.create_stubs({api.quantum: ('subnet_delete',
                                      'subnet_list',
                                      'network_get',
                                      'port_list',)})
    def test_subnet_delete_excceeption(self):
        subnet = self.subnets.first()
        network_id = subnet.network_id
        api.quantum.subnet_delete(IsA(http.HttpRequest), subnet.id)\
            .AndRaise(self.exceptions.quantum)
        api.quantum.subnet_list(IsA(http.HttpRequest), network_id=network_id)\
            .AndReturn([self.subnets.first()])
        api.quantum.network_get(IsA(http.HttpRequest), network_id)\
            .AndReturn(self.networks.first())
        api.quantum.port_list(IsA(http.HttpRequest), network_id=network_id)\
            .AndReturn([self.ports.first()])
        # Called from SubnetTable
        api.quantum.network_get(IsA(http.HttpRequest), network_id)\
            .AndReturn(self.networks.first())
        self.mox.ReplayAll()

        form_data = {'action': 'subnets__delete__%s' % subnet.id}
        url = reverse('horizon:project:networks:detail',
                      args=[network_id])
        res = self.client.post(url, form_data)

        self.assertRedirectsNoFollow(res, url)


class NetworkPortTests(test.TestCase):

    @test.create_stubs({api.quantum: ('port_get',)})
    def test_port_detail(self):
        port = self.ports.first()
        api.quantum.port_get(IsA(http.HttpRequest), port.id)\
            .AndReturn(self.ports.first())

        self.mox.ReplayAll()

        res = self.client.get(reverse('horizon:project:networks:ports:detail',
                                      args=[port.id]))

        self.assertTemplateUsed(res, 'project/networks/ports/detail.html')
        self.assertEqual(res.context['port'].id, port.id)

    @test.create_stubs({api.quantum: ('port_get',)})
    def test_port_detail_exception(self):
        port = self.ports.first()
        api.quantum.port_get(IsA(http.HttpRequest), port.id)\
            .AndRaise(self.exceptions.quantum)

        self.mox.ReplayAll()

        res = self.client.get(reverse('horizon:project:networks:ports:detail',
                                      args=[port.id]))

        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({api.quantum: ('port_get',)})
    def test_port_update_get(self):
        port = self.ports.first()
        api.quantum.port_get(IsA(http.HttpRequest),
                             port.id)\
            .AndReturn(port)
        self.mox.ReplayAll()

        url = reverse('horizon:project:networks:editport',
                      args=[port.network_id, port.id])
        res = self.client.get(url)

        self.assertTemplateUsed(res, 'project/networks/ports/update.html')

    @test.create_stubs({api.quantum: ('port_get',
                                      'port_modify')})
    def test_port_update_post(self):
        port = self.ports.first()
        api.quantum.port_get(IsA(http.HttpRequest), port.id)\
            .AndReturn(port)
        api.quantum.port_modify(IsA(http.HttpRequest), port.id,
                                name=port.name,
                                admin_state_up=port.admin_state_up)\
            .AndReturn(port)
        self.mox.ReplayAll()

        form_data = {'network_id': port.network_id,
                     'port_id': port.id,
                     'name': port.name,
                     'admin_state': port.admin_state_up}
        url = reverse('horizon:project:networks:editport',
                      args=[port.network_id, port.id])
        res = self.client.post(url, form_data)

        redir_url = reverse('horizon:project:networks:detail',
                            args=[port.network_id])
        self.assertRedirectsNoFollow(res, redir_url)

    @test.create_stubs({api.quantum: ('port_get',
                                      'port_modify')})
    def test_port_update_post_exception(self):
        port = self.ports.first()
        api.quantum.port_get(IsA(http.HttpRequest), port.id)\
            .AndReturn(port)
        api.quantum.port_modify(IsA(http.HttpRequest), port.id,
                                name=port.name,
                                admin_state_up=port.admin_state_up)\
            .AndRaise(self.exceptions.quantum)
        self.mox.ReplayAll()

        form_data = {'network_id': port.network_id,
                     'port_id': port.id,
                     'name': port.name,
                     'admin_state': port.admin_state_up}
        url = reverse('horizon:project:networks:editport',
                      args=[port.network_id, port.id])
        res = self.client.post(url, form_data)

        redir_url = reverse('horizon:project:networks:detail',
                            args=[port.network_id])
        self.assertRedirectsNoFollow(res, redir_url)
