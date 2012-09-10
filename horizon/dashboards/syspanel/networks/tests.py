# vim: tabstop=4 shiftwidth=4 softtabstop=4

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

from horizon import api
from horizon import test


INDEX_URL = reverse('horizon:syspanel:networks:index')


class NetworkTests(test.BaseAdminViewTests):
    @test.create_stubs({api.quantum: ('network_list',),
                        api.keystone: ('tenant_list',)})
    def test_index(self):
        tenants = self.tenants.list()
        api.quantum.network_list(IsA(http.HttpRequest)) \
            .AndReturn(self.networks.list())
        api.keystone.tenant_list(IsA(http.HttpRequest), admin=True)\
            .AndReturn(tenants)

        self.mox.ReplayAll()

        res = self.client.get(INDEX_URL)

        self.assertTemplateUsed(res, 'syspanel/networks/index.html')
        networks = res.context['networks_table'].data
        self.assertItemsEqual(networks, self.networks.list())

    @test.create_stubs({api.quantum: ('network_list',)})
    def test_index_network_list_exception(self):
        api.quantum.network_list(IsA(http.HttpRequest)) \
            .AndRaise(self.exceptions.quantum)

        self.mox.ReplayAll()

        res = self.client.get(INDEX_URL)

        self.assertTemplateUsed(res, 'syspanel/networks/index.html')
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

        self.mox.ReplayAll()

        res = self.client.get(reverse('horizon:syspanel:networks:detail',
                                      args=[network_id]))

        self.assertTemplateUsed(res, 'nova/networks/detail.html')
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
        api.quantum.subnet_list(IsA(http.HttpRequest), network_id=network_id)\
            .AndReturn([self.subnets.first()])
        api.quantum.port_list(IsA(http.HttpRequest), network_id=network_id)\
            .AndReturn([self.ports.first()])

        self.mox.ReplayAll()

        url = reverse('horizon:syspanel:networks:detail', args=[network_id])
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

        self.mox.ReplayAll()

        res = self.client.get(reverse('horizon:syspanel:networks:detail',
                                      args=[network_id]))

        self.assertTemplateUsed(res, 'nova/networks/detail.html')
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

        self.mox.ReplayAll()

        res = self.client.get(reverse('horizon:syspanel:networks:detail',
                                      args=[network_id]))

        self.assertTemplateUsed(res, 'nova/networks/detail.html')
        subnets = res.context['subnets_table'].data
        ports = res.context['ports_table'].data
        self.assertItemsEqual(subnets, [self.subnets.first()])
        self.assertEqual(len(ports), 0)

    @test.create_stubs({api.keystone: ('tenant_list',)})
    def test_network_create_get(self):
        tenants = self.tenants.list()
        api.keystone.tenant_list(IsA(http.HttpRequest), admin=True)\
            .AndReturn(tenants)
        self.mox.ReplayAll()

        url = reverse('horizon:syspanel:networks:create')
        res = self.client.get(url)

        self.assertTemplateUsed(res, 'syspanel/networks/create.html')

    @test.create_stubs({api.quantum: ('network_create',),
                        api.keystone: ('tenant_list',)})
    def test_network_create_post(self):
        tenants = self.tenants.list()
        tenant_id = self.tenants.first().id
        network = self.networks.first()
        api.keystone.tenant_list(IsA(http.HttpRequest), admin=True)\
            .AndReturn(tenants)
        api.quantum.network_create(IsA(http.HttpRequest), name=network.name,
                                   tenant_id=tenant_id)\
            .AndReturn(network)
        self.mox.ReplayAll()

        form_data = {'tenant_id': tenant_id,
                     'name': network.name}
        url = reverse('horizon:syspanel:networks:create')
        res = self.client.post(url, form_data)

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({api.quantum: ('network_create',),
                        api.keystone: ('tenant_list',)})
    def test_network_create_post_network_exception(self):
        tenants = self.tenants.list()
        tenant_id = self.tenants.first().id
        network = self.networks.first()
        api.keystone.tenant_list(IsA(http.HttpRequest), admin=True)\
            .AndReturn(tenants)
        api.quantum.network_create(IsA(http.HttpRequest), name=network.name,
                                   tenant_id=tenant_id)\
            .AndRaise(self.exceptions.quantum)
        self.mox.ReplayAll()

        form_data = {'tenant_id': tenant_id,
                     'name': network.name}
        url = reverse('horizon:syspanel:networks:create')
        res = self.client.post(url, form_data)

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({api.quantum: ('network_get',)})
    def test_network_update_get(self):
        network = self.networks.first()
        api.quantum.network_get(IsA(http.HttpRequest), network.id)\
            .AndReturn(network)

        self.mox.ReplayAll()

        url = reverse('horizon:syspanel:networks:update', args=[network.id])
        res = self.client.get(url)

        self.assertTemplateUsed(res, 'syspanel/networks/update.html')

    @test.create_stubs({api.quantum: ('network_get',)})
    def test_network_update_get_exception(self):
        network = self.networks.first()
        api.quantum.network_get(IsA(http.HttpRequest), network.id)\
            .AndRaise(self.exceptions.quantum)

        self.mox.ReplayAll()

        url = reverse('horizon:syspanel:networks:update', args=[network.id])
        res = self.client.get(url)

        redir_url = INDEX_URL
        self.assertRedirectsNoFollow(res, redir_url)

    @test.create_stubs({api.quantum: ('network_modify',
                                      'network_get',)})
    def test_network_update_post(self):
        network = self.networks.first()
        api.quantum.network_modify(IsA(http.HttpRequest), network.id,
                                   name=network.name)\
            .AndReturn(network)
        api.quantum.network_get(IsA(http.HttpRequest), network.id)\
            .AndReturn(network)
        self.mox.ReplayAll()

        formData = {'network_id': network.id,
                    'name': network.name,
                    'tenant_id': network.tenant_id}
        url = reverse('horizon:syspanel:networks:update', args=[network.id])
        res = self.client.post(url, formData)

        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({api.quantum: ('network_modify',
                                      'network_get',)})
    def test_network_update_post_exception(self):
        network = self.networks.first()
        api.quantum.network_modify(IsA(http.HttpRequest), network.id,
                                   name=network.name)\
            .AndRaise(self.exceptions.quantum)
        api.quantum.network_get(IsA(http.HttpRequest), network.id)\
            .AndReturn(network)
        self.mox.ReplayAll()

        form_data = {'network_id': network.id,
                     'name': network.name,
                     'tenant_id': network.tenant_id}
        url = reverse('horizon:syspanel:networks:update', args=[network.id])
        res = self.client.post(url, form_data)

        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({api.quantum: ('network_list',
                                      'network_delete'),
                        api.keystone: ('tenant_list',)})
    def test_delete_network(self):
        tenants = self.tenants.list()
        network = self.networks.first()
        api.keystone.tenant_list(IsA(http.HttpRequest), admin=True)\
            .AndReturn(tenants)
        api.quantum.network_list(IsA(http.HttpRequest))\
            .AndReturn([network])
        api.quantum.network_delete(IsA(http.HttpRequest), network.id)

        self.mox.ReplayAll()

        form_data = {'action': 'networks__delete__%s' % network.id}
        res = self.client.post(INDEX_URL, form_data)

        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({api.quantum: ('network_list',
                                      'network_delete'),
                        api.keystone: ('tenant_list',)})
    def test_delete_network_exception(self):
        tenants = self.tenants.list()
        network = self.networks.first()
        api.keystone.tenant_list(IsA(http.HttpRequest), admin=True)\
            .AndReturn(tenants)
        api.quantum.network_list(IsA(http.HttpRequest))\
            .AndReturn([network])
        api.quantum.network_delete(IsA(http.HttpRequest), network.id)\
            .AndRaise(self.exceptions.quantum)

        self.mox.ReplayAll()

        form_data = {'action': 'networks__delete__%s' % network.id}
        res = self.client.post(INDEX_URL, form_data)

        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({api.quantum: ('subnet_get',)})
    def test_subnet_detail(self):
        subnet = self.subnets.first()
        api.quantum.subnet_get(IsA(http.HttpRequest), subnet.id)\
            .AndReturn(self.subnets.first())

        self.mox.ReplayAll()

        url = reverse('horizon:syspanel:networks:subnets:detail',
                      args=[subnet.id])
        res = self.client.get(url)

        self.assertTemplateUsed(res, 'nova/networks/subnets/detail.html')
        self.assertEqual(res.context['subnet'].id, subnet.id)

    @test.create_stubs({api.quantum: ('subnet_get',)})
    def test_subnet_detail_exception(self):
        subnet = self.subnets.first()
        api.quantum.subnet_get(IsA(http.HttpRequest), subnet.id)\
            .AndRaise(self.exceptions.quantum)

        self.mox.ReplayAll()

        url = reverse('horizon:syspanel:networks:subnets:detail',
                                      args=[subnet.id])
        res = self.client.get(url)

        # syspanel DetailView is shared with userpanel one, so
        # redirection URL on error is userpanel index.
        redir_url = reverse('horizon:nova:networks:index')
        self.assertRedirectsNoFollow(res, redir_url)

    @test.create_stubs({api.quantum: ('network_get',)})
    def test_subnet_create_get(self):
        network = self.networks.first()
        api.quantum.network_get(IsA(http.HttpRequest),
                                network.id)\
            .AndReturn(self.networks.first())
        self.mox.ReplayAll()

        url = reverse('horizon:syspanel:networks:addsubnet',
                      args=[network.id])
        res = self.client.get(url)

        self.assertTemplateUsed(res, 'syspanel/networks/subnets/create.html')

    @test.create_stubs({api.quantum: ('network_get',
                                      'subnet_create',)})
    def test_subnet_create_post(self):
        network = self.networks.first()
        subnet = self.subnets.first()
        api.quantum.network_get(IsA(http.HttpRequest),
                                network.id)\
            .AndReturn(self.networks.first())
        api.quantum.network_get(IsA(http.HttpRequest),
                                network.id)\
            .AndReturn(self.networks.first())
        api.quantum.subnet_create(IsA(http.HttpRequest),
                                  network_id=network.id,
                                  network_name=network.name,
                                  name=subnet.name,
                                  cidr=subnet.cidr,
                                  ip_version=subnet.ip_version,
                                  gateway_ip=subnet.gateway_ip,
                                  tenant_id=subnet.tenant_id)\
            .AndReturn(subnet)
        self.mox.ReplayAll()

        form_data = {'network_id': subnet.network_id,
                     'network_name': network.name,
                     'name': subnet.name,
                     'cidr': subnet.cidr,
                     'ip_version': subnet.ip_version,
                     'gateway_ip': subnet.gateway_ip}
        url = reverse('horizon:syspanel:networks:addsubnet',
                      args=[subnet.network_id])
        res = self.client.post(url, form_data)

        self.assertNoFormErrors(res)
        redir_url = reverse('horizon:syspanel:networks:detail',
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

        form_data = {'network_id': subnet.network_id,
                     'network_name': network.name,
                     'name': subnet.name,
                     'cidr': subnet.cidr,
                     'ip_version': subnet.ip_version,
                     'gateway_ip': subnet.gateway_ip}
        url = reverse('horizon:syspanel:networks:addsubnet',
                      args=[subnet.network_id])
        res = self.client.post(url, form_data)

        self.assertNoFormErrors(res)
        # syspanel DetailView is shared with userpanel one, so
        # redirection URL on error is userpanel index.
        redir_url = reverse('horizon:nova:networks:index')
        self.assertRedirectsNoFollow(res, redir_url)

    @test.create_stubs({api.quantum: ('network_get',
                                      'subnet_create',)})
    def test_subnet_create_post_subnet_exception(self):
        network = self.networks.first()
        subnet = self.subnets.first()
        api.quantum.network_get(IsA(http.HttpRequest),
                                network.id)\
            .AndReturn(self.networks.first())
        api.quantum.network_get(IsA(http.HttpRequest),
                                network.id)\
            .AndReturn(self.networks.first())
        api.quantum.subnet_create(IsA(http.HttpRequest),
                                  network_id=network.id,
                                  network_name=network.name,
                                  name=subnet.name,
                                  cidr=subnet.cidr,
                                  ip_version=subnet.ip_version,
                                  gateway_ip=subnet.gateway_ip,
                                  tenant_id=subnet.tenant_id)\
            .AndRaise(self.exceptions.quantum)
        self.mox.ReplayAll()

        form_data = {'network_id': subnet.network_id,
                     'network_name': network.name,
                     'name': subnet.name,
                     'cidr': subnet.cidr,
                     'ip_version': subnet.ip_version,
                     'gateway_ip': subnet.gateway_ip}
        url = reverse('horizon:syspanel:networks:addsubnet',
                      args=[subnet.network_id])
        res = self.client.post(url, form_data)

        redir_url = reverse('horizon:syspanel:networks:detail',
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
        form_data = {'network_id': subnet.network_id,
                     'network_name': network.name,
                     'name': subnet.name,
                     'cidr': cidr,
                     'ip_version': subnet.ip_version,
                     'gateway_ip': subnet.gateway_ip}
        url = reverse('horizon:syspanel:networks:addsubnet',
                      args=[subnet.network_id])
        res = self.client.post(url, form_data)

        expected_msg = 'Network Address and IP version are inconsistent.'
        self.assertContains(res, expected_msg)

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
        form_data = {'network_id': subnet.network_id,
                     'network_name': network.name,
                     'name': subnet.name,
                     'cidr': subnet.cidr,
                     'ip_version': subnet.ip_version,
                     'gateway_ip': gateway_ip}
        url = reverse('horizon:syspanel:networks:addsubnet',
                      args=[subnet.network_id])
        res = self.client.post(url, form_data)

        self.assertContains(res, 'Gateway IP and IP version are inconsistent.')

    @test.create_stubs({api.quantum: ('subnet_modify',
                                      'subnet_get',)})
    def test_subnet_update_post(self):
        subnet = self.subnets.first()
        api.quantum.subnet_get(IsA(http.HttpRequest), subnet.id)\
            .AndReturn(subnet)
        api.quantum.subnet_modify(IsA(http.HttpRequest), subnet.id,
                                  name=subnet.name,
                                  gateway_ip=subnet.gateway_ip)\
            .AndReturn(subnet)
        self.mox.ReplayAll()

        formData = {'network_id': subnet.network_id,
                    'tenant_id': subnet.tenant_id,
                    'subnet_id': subnet.id,
                    'name': subnet.name,
                    'cidr': subnet.cidr,
                    'ip_version': subnet.ip_version,
                    'gateway_ip': subnet.gateway_ip}
        url = reverse('horizon:syspanel:networks:editsubnet',
                      args=[subnet.network_id, subnet.id])
        res = self.client.post(url, formData)

        redir_url = reverse('horizon:syspanel:networks:detail',
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
        formData = {'network_id': subnet.network_id,
                    'tenant_id': subnet.tenant_id,
                    'subnet_id': subnet.id,
                    'name': subnet.name,
                    'cidr': subnet.cidr,
                    'ip_version': subnet.ip_version,
                    'gateway_ip': gateway_ip}
        url = reverse('horizon:syspanel:networks:editsubnet',
                      args=[subnet.network_id, subnet.id])
        res = self.client.post(url, formData)

        self.assertContains(res, 'Gateway IP and IP version are inconsistent.')

    @test.create_stubs({api.quantum: ('subnet_delete',
                                      'subnet_list',
                                      'port_list',)})
    def test_subnet_delete(self):
        subnet = self.subnets.first()
        network_id = subnet.network_id
        api.quantum.subnet_delete(IsA(http.HttpRequest), subnet.id)
        api.quantum.subnet_list(IsA(http.HttpRequest), network_id=network_id)\
            .AndReturn([self.subnets.first()])
        api.quantum.port_list(IsA(http.HttpRequest), network_id=network_id)\
            .AndReturn([self.ports.first()])
        self.mox.ReplayAll()

        formData = {'action': 'subnets__delete__%s' % subnet.id}
        url = reverse('horizon:syspanel:networks:detail',
                      args=[network_id])
        res = self.client.post(url, formData)

        self.assertRedirectsNoFollow(res, url)

    @test.create_stubs({api.quantum: ('subnet_delete',
                                      'subnet_list',
                                      'port_list',)})
    def test_subnet_delete_exception(self):
        subnet = self.subnets.first()
        network_id = subnet.network_id
        api.quantum.subnet_delete(IsA(http.HttpRequest), subnet.id)\
            .AndRaise(self.exceptions.quantum)
        api.quantum.subnet_list(IsA(http.HttpRequest), network_id=network_id)\
            .AndReturn([self.subnets.first()])
        api.quantum.port_list(IsA(http.HttpRequest), network_id=network_id)\
            .AndReturn([self.ports.first()])
        self.mox.ReplayAll()

        formData = {'action': 'subnets__delete__%s' % subnet.id}
        url = reverse('horizon:syspanel:networks:detail',
                      args=[network_id])
        res = self.client.post(url, formData)

        self.assertRedirectsNoFollow(res, url)

    @test.create_stubs({api.quantum: ('port_get',)})
    def test_port_detail(self):
        port = self.ports.first()
        api.quantum.port_get(IsA(http.HttpRequest), port.id)\
            .AndReturn(self.ports.first())

        self.mox.ReplayAll()

        res = self.client.get(reverse('horizon:syspanel:networks:ports:detail',
                                      args=[port.id]))

        self.assertTemplateUsed(res, 'nova/networks/ports/detail.html')
        self.assertEqual(res.context['port'].id, port.id)

    @test.create_stubs({api.quantum: ('port_get',)})
    def test_port_detail_exception(self):
        port = self.ports.first()
        api.quantum.port_get(IsA(http.HttpRequest), port.id)\
            .AndRaise(self.exceptions.quantum)

        self.mox.ReplayAll()

        res = self.client.get(reverse('horizon:syspanel:networks:ports:detail',
                                      args=[port.id]))

        # syspanel DetailView is shared with userpanel one, so
        # redirection URL on error is userpanel index.
        redir_url = reverse('horizon:nova:networks:index')
        self.assertRedirectsNoFollow(res, redir_url)

    @test.create_stubs({api.quantum: ('network_get',)})
    def test_port_create_get(self):
        network = self.networks.first()
        api.quantum.network_get(IsA(http.HttpRequest),
                                network.id)\
            .AndReturn(self.networks.first())
        self.mox.ReplayAll()

        url = reverse('horizon:syspanel:networks:addport',
                      args=[network.id])
        res = self.client.get(url)

        self.assertTemplateUsed(res, 'syspanel/networks/ports/create.html')

    @test.create_stubs({api.quantum: ('network_get',
                                      'port_create')})
    def test_port_create_post(self):
        network = self.networks.first()
        port = self.ports.first()
        api.quantum.network_get(IsA(http.HttpRequest),
                                network.id)\
            .AndReturn(self.networks.first())
        api.quantum.network_get(IsA(http.HttpRequest),
                                network.id)\
            .AndReturn(self.networks.first())
        api.quantum.port_create(IsA(http.HttpRequest),
                                tenant_id=network.tenant_id,
                                network_id=network.id,
                                network_name=network.name,
                                name=port.name,
                                device_id=port.device_id)\
            .AndReturn(port)
        self.mox.ReplayAll()

        form_data = {'network_id': port.network_id,
                     'network_name': network.name,
                     'name': port.name,
                     'device_id': port.device_id}
        url = reverse('horizon:syspanel:networks:addport',
                      args=[port.network_id])
        res = self.client.post(url, form_data)

        self.assertNoFormErrors(res)
        redir_url = reverse('horizon:syspanel:networks:detail',
                            args=[port.network_id])
        self.assertRedirectsNoFollow(res, redir_url)

    @test.create_stubs({api.quantum: ('network_get',
                                      'port_create')})
    def test_port_create_post_exception(self):
        network = self.networks.first()
        port = self.ports.first()
        api.quantum.network_get(IsA(http.HttpRequest),
                                network.id)\
            .AndReturn(self.networks.first())
        api.quantum.network_get(IsA(http.HttpRequest),
                                network.id)\
            .AndReturn(self.networks.first())
        api.quantum.port_create(IsA(http.HttpRequest),
                                tenant_id=network.tenant_id,
                                network_id=network.id,
                                network_name=network.name,
                                name=port.name,
                                device_id=port.device_id)\
            .AndRaise(self.exceptions.quantum)
        self.mox.ReplayAll()

        form_data = {'network_id': port.network_id,
                     'network_name': network.name,
                     'name': port.name,
                     'device_id': port.device_id}
        url = reverse('horizon:syspanel:networks:addport',
                      args=[port.network_id])
        res = self.client.post(url, form_data)

        self.assertNoFormErrors(res)
        redir_url = reverse('horizon:syspanel:networks:detail',
                            args=[port.network_id])
        self.assertRedirectsNoFollow(res, redir_url)

    @test.create_stubs({api.quantum: ('port_get',)})
    def test_port_update_get(self):
        port = self.ports.first()
        api.quantum.port_get(IsA(http.HttpRequest),
                             port.id)\
            .AndReturn(port)
        self.mox.ReplayAll()

        url = reverse('horizon:syspanel:networks:editport',
                      args=[port.network_id, port.id])
        res = self.client.get(url)

        self.assertTemplateUsed(res, 'syspanel/networks/ports/update.html')

    @test.create_stubs({api.quantum: ('port_get',
                                      'port_modify')})
    def test_port_update_post(self):
        port = self.ports.first()
        api.quantum.port_get(IsA(http.HttpRequest), port.id)\
            .AndReturn(port)
        api.quantum.port_modify(IsA(http.HttpRequest), port.id,
                                name=port.name, device_id=port.device_id)\
            .AndReturn(port)
        self.mox.ReplayAll()

        formData = {'tenant_id': port.tenant_id,
                    'network_id': port.network_id,
                    'port_id': port.id,
                    'name': port.name,
                    'device_id': port.device_id}
        url = reverse('horizon:syspanel:networks:editport',
                      args=[port.network_id, port.id])
        res = self.client.post(url, formData)

        redir_url = reverse('horizon:syspanel:networks:detail',
                            args=[port.network_id])
        self.assertRedirectsNoFollow(res, redir_url)

    @test.create_stubs({api.quantum: ('port_get',
                                      'port_modify')})
    def test_port_update_post_exception(self):
        port = self.ports.first()
        api.quantum.port_get(IsA(http.HttpRequest), port.id)\
            .AndReturn(port)
        api.quantum.port_modify(IsA(http.HttpRequest), port.id,
                                name=port.name, device_id=port.device_id)\
            .AndRaise(self.exceptions.quantum)
        self.mox.ReplayAll()

        formData = {'tenant_id': port.tenant_id,
                    'network_id': port.network_id,
                    'port_id': port.id,
                    'name': port.name,
                    'device_id': port.device_id}
        url = reverse('horizon:syspanel:networks:editport',
                      args=[port.network_id, port.id])
        res = self.client.post(url, formData)

        redir_url = reverse('horizon:syspanel:networks:detail',
                            args=[port.network_id])
        self.assertRedirectsNoFollow(res, redir_url)

    @test.create_stubs({api.quantum: ('port_delete',
                                      'subnet_list',
                                      'port_list',)})
    def test_port_delete(self):
        port = self.ports.first()
        network_id = port.network_id
        api.quantum.port_delete(IsA(http.HttpRequest), port.id)
        api.quantum.subnet_list(IsA(http.HttpRequest), network_id=network_id)\
            .AndReturn([self.subnets.first()])
        api.quantum.port_list(IsA(http.HttpRequest), network_id=network_id)\
            .AndReturn([self.ports.first()])
        self.mox.ReplayAll()

        formData = {'action': 'ports__delete__%s' % port.id}
        url = reverse('horizon:syspanel:networks:detail',
                      args=[network_id])
        res = self.client.post(url, formData)

        self.assertRedirectsNoFollow(res, url)

    @test.create_stubs({api.quantum: ('port_delete',
                                      'subnet_list',
                                      'port_list',)})
    def test_port_delete_exception(self):
        port = self.ports.first()
        network_id = port.network_id
        api.quantum.port_delete(IsA(http.HttpRequest), port.id)\
            .AndRaise(self.exceptions.quantum)
        api.quantum.subnet_list(IsA(http.HttpRequest), network_id=network_id)\
            .AndReturn([self.subnets.first()])
        api.quantum.port_list(IsA(http.HttpRequest), network_id=network_id)\
            .AndReturn([self.ports.first()])
        self.mox.ReplayAll()

        formData = {'action': 'ports__delete__%s' % port.id}
        url = reverse('horizon:syspanel:networks:detail',
                      args=[network_id])
        res = self.client.post(url, formData)

        self.assertRedirectsNoFollow(res, url)
