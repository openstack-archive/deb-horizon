# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2013, Mirantis Inc
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
# @author: Tatiana Mazur

from mox import IsA  # noqa

from django.core.urlresolvers import reverse  # noqa
from django.core.urlresolvers import reverse_lazy  # noqa
from django import http

from horizon.workflows import views

from openstack_dashboard import api
from openstack_dashboard.test import helpers as test

from openstack_dashboard.dashboards.project.vpn import workflows


class VPNTests(test.TestCase):
    class AttributeDict(dict):
        def __getattr__(self, attr):
            return self[attr]

        def __setattr__(self, attr, value):
            self[attr] = value

    DASHBOARD = 'project'
    INDEX_URL = reverse_lazy('horizon:%s:vpn:index' % DASHBOARD)

    ADDIKEPOLICY_PATH = 'horizon:%s:vpn:addikepolicy' % DASHBOARD
    ADDIPSECPOLICY_PATH = 'horizon:%s:vpn:addipsecpolicy' % DASHBOARD
    ADDVPNSERVICE_PATH = 'horizon:%s:vpn:addvpnservice' % DASHBOARD
    ADDVPNCONNECTION_PATH = 'horizon:%s:vpn:addipsecsiteconnection' % DASHBOARD

    IKEPOLICY_DETAIL_PATH = 'horizon:%s:vpn:ikepolicydetails' % DASHBOARD
    IPSECPOLICY_DETAIL_PATH = 'horizon:%s:vpn:ipsecpolicydetails' % DASHBOARD
    VPNSERVICE_DETAIL_PATH = 'horizon:%s:vpn:vpnservicedetails' % DASHBOARD
    VPNCONNECTION_DETAIL_PATH = 'horizon:%s:vpn:ipsecsiteconnectiondetails' %\
        DASHBOARD

    def set_up_expect(self):
        # retrieves vpnservices
        vpnservice1, vpnservice2 = self.vpnservices.list()[:2]

        api.vpn.vpnservices_get(
            IsA(http.HttpRequest)).AndReturn(self.vpnservices.list())

        api.vpn.vpnservice_get(
            IsA(http.HttpRequest), vpnservice1.id).AndReturn(vpnservice1)
        api.vpn.vpnservice_get(
            IsA(http.HttpRequest), vpnservice2.id).AndReturn(vpnservice2)

        # retrieves ikepolicies
        api.vpn.ikepolicies_get(
            IsA(http.HttpRequest)).AndReturn(self.ikepolicies.list())

        ikepolicy1, ikepolicy2 = self.ikepolicies.list()[:2]

        api.vpn.ikepolicy_get(
            IsA(http.HttpRequest), ikepolicy1.id).AndReturn(ikepolicy1)
        api.vpn.ikepolicy_get(
            IsA(http.HttpRequest), ikepolicy2.id).AndReturn(ikepolicy2)

        # retrieves ipsecpolicies
        api.vpn.ipsecpolicies_get(
            IsA(http.HttpRequest)).AndReturn(self.ipsecpolicies.list())

        ipsecpolicy1, ipsecpolicy2 = self.ipsecpolicies.list()[:2]

        api.vpn.ipsecpolicy_get(
            IsA(http.HttpRequest), ipsecpolicy1.id).AndReturn(ipsecpolicy1)
        api.vpn.ipsecpolicy_get(
            IsA(http.HttpRequest), ipsecpolicy2.id).AndReturn(ipsecpolicy2)

        # retrieves ipsecsiteconnections
        api.vpn.ipsecsiteconnections_get(
            IsA(http.HttpRequest)).AndReturn(self.ipsecsiteconnections.list())

    def set_up_expect_with_exception(self):
        api.vpn.vpnservices_get(
            IsA(http.HttpRequest)).AndRaise(self.exceptions.neutron)
        api.vpn.ikepolicies_get(
            IsA(http.HttpRequest)).AndRaise(self.exceptions.neutron)
        api.vpn.ipsecpolicies_get(
            IsA(http.HttpRequest)).AndRaise(self.exceptions.neutron)
        api.vpn.ipsecsiteconnections_get(
            IsA(http.HttpRequest)).AndRaise(self.exceptions.neutron)

    @test.create_stubs({api.vpn: ('ikepolicies_get', 'ipsecpolicies_get',
                                  'vpnservices_get',
                                  'ipsecsiteconnections_get', 'ikepolicy_get',
                                  'ipsecpolicy_get', 'vpnservice_get',
                                  'ipsecsiteconnection_get')})
    def test_index_vpnservices(self):
        self.set_up_expect()

        self.mox.ReplayAll()

        res = self.client.get(self.INDEX_URL)

        self.assertTemplateUsed(res, '%s/vpn/index.html'
                                % self.DASHBOARD)
        self.assertTemplateUsed(res, 'horizon/common/_detail_table.html')
        self.assertEqual(len(res.context['table'].data),
                         len(self.vpnservices.list()))

    @test.create_stubs({api.vpn: ('ikepolicies_get', 'ipsecpolicies_get',
                                  'vpnservices_get',
                                  'ipsecsiteconnections_get', 'ikepolicy_get',
                                  'ipsecpolicy_get', 'vpnservice_get',
                                  'ipsecsiteconnection_get')})
    def test_index_ikepolicies(self):
        self.set_up_expect()

        self.mox.ReplayAll()

        res = self.client.get(self.INDEX_URL + '?tab=vpntabs__ikepolicies')

        self.assertTemplateUsed(res, '%s/vpn/index.html'
                                % self.DASHBOARD)
        self.assertTemplateUsed(res, 'horizon/common/_detail_table.html')
        self.assertEqual(len(res.context['ikepoliciestable_table'].data),
                         len(self.ikepolicies.list()))

    @test.create_stubs({api.vpn: ('ikepolicies_get', 'ipsecpolicies_get',
                                  'vpnservices_get',
                                  'ipsecsiteconnections_get', 'ikepolicy_get',
                                  'ipsecpolicy_get', 'vpnservice_get',
                                  'ipsecsiteconnection_get')})
    def test_index_ipsecpolicies(self):
        self.set_up_expect()

        self.mox.ReplayAll()

        res = self.client.get(self.INDEX_URL + '?tab=vpntabs__ipsecpolicies')

        self.assertTemplateUsed(res, '%s/vpn/index.html'
                                % self.DASHBOARD)
        self.assertTemplateUsed(res, 'horizon/common/_detail_table.html')
        self.assertEqual(len(res.context['ipsecpoliciestable_table'].data),
                         len(self.ipsecpolicies.list()))

    @test.create_stubs({api.vpn: ('ikepolicies_get', 'ipsecpolicies_get',
                                  'vpnservices_get',
                                  'ipsecsiteconnections_get', 'ikepolicy_get',
                                  'ipsecpolicy_get', 'vpnservice_get',
                                  'ipsecsiteconnection_get')})
    def test_index_ipsecsiteconnections(self):
        self.set_up_expect()

        self.mox.ReplayAll()

        res = self.client.get(
            self.INDEX_URL + '?tab=vpntabs__ipsecsiteconnections')

        self.assertTemplateUsed(res, '%s/vpn/index.html'
                                % self.DASHBOARD)
        self.assertTemplateUsed(res, 'horizon/common/_detail_table.html')
        self.assertEqual(
            len(res.context['ipsecsiteconnectionstable_table'].data),
            len(self.ipsecsiteconnections.list()))

    @test.create_stubs({api.vpn: ('ikepolicies_get', 'ipsecpolicies_get',
                                  'vpnservices_get',
                                  'ipsecsiteconnections_get')})
    def test_index_exception_vpnservices(self):
        self.set_up_expect_with_exception()

        self.mox.ReplayAll()

        res = self.client.get(self.INDEX_URL)

        self.assertTemplateUsed(res, '%s/vpn/index.html'
                                % self.DASHBOARD)
        self.assertTemplateUsed(res,
                                'horizon/common/_detail_table.html')
        self.assertEqual(len(res.context['table'].data), 0)

    @test.create_stubs({api.vpn: ('ikepolicies_get', 'ipsecpolicies_get',
                                  'vpnservices_get',
                                  'ipsecsiteconnections_get')})
    def test_index_exception_ikepolicies(self):
        self.set_up_expect_with_exception()

        self.mox.ReplayAll()

        res = self.client.get(self.INDEX_URL + '?tab=vpntabs__ikepolicies')

        self.assertTemplateUsed(res, '%s/vpn/index.html'
                                % self.DASHBOARD)
        self.assertTemplateUsed(res,
                                'horizon/common/_detail_table.html')
        self.assertEqual(len(res.context['table'].data), 0)

    @test.create_stubs({api.vpn: ('ikepolicies_get', 'ipsecpolicies_get',
                                  'vpnservices_get',
                                  'ipsecsiteconnections_get')})
    def test_index_exception_ipsecpolicies(self):
        self.set_up_expect_with_exception()

        self.mox.ReplayAll()

        res = self.client.get(self.INDEX_URL + '?tab=vpntabs__ipsecpolicies')

        self.assertTemplateUsed(res, '%s/vpn/index.html'
                                % self.DASHBOARD)
        self.assertTemplateUsed(res,
                                'horizon/common/_detail_table.html')
        self.assertEqual(len(res.context['table'].data), 0)

    @test.create_stubs({api.vpn: ('ikepolicies_get', 'ipsecpolicies_get',
                                  'vpnservices_get',
                                  'ipsecsiteconnections_get')})
    def test_index_exception_ipsecsiteconnections(self):
        self.set_up_expect_with_exception()

        self.mox.ReplayAll()

        res = self.client.get(
            self.INDEX_URL + '?tab=vpntabs__ipsecsiteconnections')

        self.assertTemplateUsed(res, '%s/vpn/index.html'
                                % self.DASHBOARD)
        self.assertTemplateUsed(res,
                                'horizon/common/_detail_table.html')
        self.assertEqual(len(res.context['table'].data), 0)

    @test.create_stubs({api.neutron: ('network_list_for_tenant',
                                      'router_list')})
    def test_add_vpnservice_get(self):
        subnet = self.subnets.first()

        networks = [{'subnets': [subnet, ]}, ]

        api.neutron.network_list_for_tenant(
            IsA(http.HttpRequest), subnet.tenant_id).AndReturn(networks)

        routers = self.routers.list()

        api.neutron.router_list(
            IsA(http.HttpRequest)).AndReturn(routers)

        self.mox.ReplayAll()

        res = self.client.get(reverse(self.ADDVPNSERVICE_PATH))

        workflow = res.context['workflow']
        self.assertTemplateUsed(res, views.WorkflowView.template_name)
        self.assertEqual(workflow.name, workflows.AddVPNService.name)

        expected_objs = ['<AddVPNServiceStep: addvpnserviceaction>', ]
        self.assertQuerysetEqual(workflow.steps, expected_objs)

    @test.create_stubs({api.neutron: ('router_list',
                                      'network_list_for_tenant'),
                        api.vpn: ('vpnservice_create', )})
    def test_add_vpnservice_post(self):
        vpnservice = self.vpnservices.first()

        routers = self.routers.list()

        api.neutron.router_list(
            IsA(http.HttpRequest)).AndReturn(routers)

        subnet = self.subnets.first()
        networks = [{'subnets': [subnet, ]}, ]

        api.neutron.network_list_for_tenant(
            IsA(http.HttpRequest), subnet.tenant_id).AndReturn(networks)

        api.vpn.vpnservice_create(
            IsA(http.HttpRequest),
            name=vpnservice.name,
            description=vpnservice.description,
            subnet_id=vpnservice.subnet_id,
            router_id=vpnservice.router_id,
            admin_state_up=vpnservice.admin_state_up).AndReturn(
                api.vpn.VPNService(vpnservice))

        self.mox.ReplayAll()

        form_data = {'name': vpnservice['name'],
                     'description': vpnservice['description'],
                     'subnet_id': vpnservice['subnet_id'],
                     'router_id': vpnservice['router_id'],
                     'admin_state_up': vpnservice['admin_state_up']}

        res = self.client.post(reverse(self.ADDVPNSERVICE_PATH), form_data)

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, str(self.INDEX_URL))

    @test.create_stubs({api.neutron: ('router_list',
                                      'network_list_for_tenant')})
    def test_add_vpnservice_post_error(self):
        vpnservice = self.vpnservices.first()

        routers = self.routers.list()

        api.neutron.router_list(
            IsA(http.HttpRequest)).AndReturn(routers)

        subnet = self.subnets.first()
        networks = [{'subnets': [subnet, ]}, ]

        api.neutron.network_list_for_tenant(
            IsA(http.HttpRequest), subnet.tenant_id).AndReturn(networks)

        self.mox.ReplayAll()

        form_data = {'name': vpnservice['name'],
                     'description': vpnservice['description'],
                     'subnet_id': '',
                     'router_id': '',
                     'admin_state_up': vpnservice['admin_state_up']}

        res = self.client.post(reverse(self.ADDVPNSERVICE_PATH), form_data)

        self.assertFormErrors(res, 2)

    def test_add_ikepolicy_get(self):
        res = self.client.get(reverse(self.ADDIKEPOLICY_PATH))

        workflow = res.context['workflow']
        self.assertTemplateUsed(res, views.WorkflowView.template_name)
        self.assertEqual(workflow.name, workflows.AddIKEPolicy.name)

        expected_objs = ['<AddIKEPolicyStep: addikepolicyaction>', ]
        self.assertQuerysetEqual(workflow.steps, expected_objs)

    @test.create_stubs({api.vpn: ('ikepolicy_create', )})
    def test_add_ikepolicy_post(self):
        ikepolicy = self.ikepolicies.first()

        api.vpn.ikepolicy_create(
            IsA(http.HttpRequest),
            name=ikepolicy.name,
            description=ikepolicy.description,
            auth_algorithm=ikepolicy.auth_algorithm,
            encryption_algorithm=ikepolicy.encryption_algorithm,
            ike_version=ikepolicy.ike_version,
            lifetime=ikepolicy.lifetime,
            phase1_negotiation_mode=ikepolicy.phase1_negotiation_mode,
            pfs=ikepolicy.pfs).AndReturn(
                api.vpn.IKEPolicy(ikepolicy))

        self.mox.ReplayAll()

        form_data = {'name': ikepolicy['name'],
                     'description': ikepolicy['description'],
                     'auth_algorithm': ikepolicy['auth_algorithm'],
                     'encryption_algorithm': ikepolicy[
                         'encryption_algorithm'],
                     'ike_version': ikepolicy['ike_version'],
                     'lifetime_units': ikepolicy['lifetime']['units'],
                     'lifetime_value': ikepolicy['lifetime']['value'],
                     'phase1_negotiation_mode': ikepolicy[
                         'phase1_negotiation_mode'],
                     'pfs': ikepolicy['pfs']}

        res = self.client.post(reverse(self.ADDIKEPOLICY_PATH), form_data)

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, str(self.INDEX_URL))

    def test_add_ikepolicy_post_error(self):
        ikepolicy = self.ikepolicies.first()

        form_data = {'name': ikepolicy['name'],
                     'description': ikepolicy['description'],
                     'auth_algorithm': ikepolicy['auth_algorithm'],
                     'encryption_algorithm': ikepolicy[
                         'encryption_algorithm'],
                     'ike_version': ikepolicy['ike_version'],
                     'lifetime_units': ikepolicy['lifetime']['units'],
                     'lifetime_value': 10,
                     'phase1_negotiation_mode': ikepolicy[
                         'phase1_negotiation_mode'],
                     'pfs': ikepolicy['pfs']}

        res = self.client.post(reverse(self.ADDIKEPOLICY_PATH), form_data)

        self.assertFormErrors(res, 1)

    def test_add_ipsecpolicy_get(self):
        res = self.client.get(reverse(self.ADDIPSECPOLICY_PATH))

        workflow = res.context['workflow']
        self.assertTemplateUsed(res, views.WorkflowView.template_name)
        self.assertEqual(workflow.name, workflows.AddIPSecPolicy.name)

        expected_objs = ['<AddIPSecPolicyStep: addipsecpolicyaction>', ]
        self.assertQuerysetEqual(workflow.steps, expected_objs)

    @test.create_stubs({api.vpn: ('ipsecpolicy_create', )})
    def test_add_ipsecpolicy_post(self):
        ipsecpolicy = self.ipsecpolicies.first()

        api.vpn.ipsecpolicy_create(
            IsA(http.HttpRequest),
            name=ipsecpolicy.name,
            description=ipsecpolicy.description,
            auth_algorithm=ipsecpolicy.auth_algorithm,
            encryption_algorithm=ipsecpolicy.encryption_algorithm,
            encapsulation_mode=ipsecpolicy.encapsulation_mode,
            lifetime=ipsecpolicy.lifetime,
            pfs=ipsecpolicy.pfs,
            transform_protocol=ipsecpolicy.transform_protocol).AndReturn(
                api.vpn.IPSecPolicy(ipsecpolicy))

        self.mox.ReplayAll()

        form_data = {'name': ipsecpolicy['name'],
                     'description': ipsecpolicy['description'],
                     'auth_algorithm': ipsecpolicy['auth_algorithm'],
                     'encryption_algorithm': ipsecpolicy[
                         'encryption_algorithm'],
                     'encapsulation_mode': ipsecpolicy[
                         'encapsulation_mode'],
                     'lifetime_units': ipsecpolicy['lifetime']['units'],
                     'lifetime_value': ipsecpolicy['lifetime']['value'],
                     'pfs': ipsecpolicy['pfs'],
                     'transform_protocol': ipsecpolicy[
                         'transform_protocol']}

        res = self.client.post(reverse(self.ADDIPSECPOLICY_PATH), form_data)

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, str(self.INDEX_URL))

    def test_add_ipsecpolicy_post_error(self):
        ipsecpolicy = self.ipsecpolicies.first()

        form_data = {'name': ipsecpolicy['name'],
                     'description': ipsecpolicy['description'],
                     'auth_algorithm': ipsecpolicy['auth_algorithm'],
                     'encryption_algorithm': ipsecpolicy[
                         'encryption_algorithm'],
                     'encapsulation_mode': ipsecpolicy[
                         'encapsulation_mode'],
                     'lifetime_units': ipsecpolicy['lifetime']['units'],
                     'lifetime_value': 10,
                     'pfs': ipsecpolicy['pfs'],
                     'transform_protocol': ipsecpolicy[
                         'transform_protocol']}

        res = self.client.post(reverse(self.ADDIPSECPOLICY_PATH), form_data)

        self.assertFormErrors(res, 1)

    @test.create_stubs({api.vpn: ('ikepolicies_get', 'ipsecpolicies_get',
                                  'vpnservices_get')})
    def test_add_ipsecsiteconnection_get(self):
        ikepolicies = self.ikepolicies.list()

        api.vpn.ikepolicies_get(
            IsA(http.HttpRequest)).AndReturn(ikepolicies)

        ipsecpolicies = self.ipsecpolicies.list()

        api.vpn.ipsecpolicies_get(
            IsA(http.HttpRequest)).AndReturn(ipsecpolicies)

        vpnservices = self.vpnservices.list()

        api.vpn.vpnservices_get(
            IsA(http.HttpRequest)).AndReturn(vpnservices)

        self.mox.ReplayAll()

        res = self.client.get(reverse(self.ADDVPNCONNECTION_PATH))

        workflow = res.context['workflow']
        self.assertTemplateUsed(res, views.WorkflowView.template_name)
        self.assertEqual(workflow.name, workflows.AddIPSecSiteConnection.name)

        expected_objs = ['<AddIPSecSiteConnectionStep: '
                         'addipsecsiteconnectionaction>',
                         '<AddIPSecSiteConnectionOptionalStep: '
                         'addipsecsiteconnectionoptionalaction>', ]
        self.assertQuerysetEqual(workflow.steps, expected_objs)

    @test.create_stubs({api.vpn: ('ikepolicies_get', 'ipsecpolicies_get',
                                  'vpnservices_get',
                                  'ipsecsiteconnection_create')})
    def test_add_ipsecsiteconnection_post(self):
        ipsecsiteconnection = self.ipsecsiteconnections.first()

        ikepolicies = self.ikepolicies.list()

        api.vpn.ikepolicies_get(
            IsA(http.HttpRequest)).AndReturn(ikepolicies)

        ipsecpolicies = self.ipsecpolicies.list()

        api.vpn.ipsecpolicies_get(
            IsA(http.HttpRequest)).AndReturn(ipsecpolicies)

        vpnservices = self.vpnservices.list()

        api.vpn.vpnservices_get(
            IsA(http.HttpRequest)).AndReturn(vpnservices)

        api.vpn.ipsecsiteconnection_create(
            IsA(http.HttpRequest),
            name=ipsecsiteconnection.name,
            description=ipsecsiteconnection.description,
            dpd=ipsecsiteconnection.dpd,
            ikepolicy_id=ipsecsiteconnection.ikepolicy_id,
            initiator=ipsecsiteconnection.initiator,
            ipsecpolicy_id=ipsecsiteconnection.ipsecpolicy_id,
            mtu=ipsecsiteconnection.mtu,
            peer_address=ipsecsiteconnection.peer_address,
            peer_cidrs=ipsecsiteconnection.peer_cidrs,
            peer_id=ipsecsiteconnection.peer_id,
            psk=ipsecsiteconnection.psk,
            vpnservice_id=ipsecsiteconnection.vpnservice_id,
            admin_state_up=ipsecsiteconnection.admin_state_up).AndReturn(
                api.vpn.IPSecSiteConnection(ipsecsiteconnection))

        self.mox.ReplayAll()

        form_data = {'name': ipsecsiteconnection['name'],
                     'description': ipsecsiteconnection['description'],
                     'dpd_action': ipsecsiteconnection['dpd']['action'],
                     'dpd_interval': ipsecsiteconnection['dpd']['interval'],
                     'dpd_timeout': ipsecsiteconnection['dpd']['timeout'],
                     'ikepolicy_id': ipsecsiteconnection['ikepolicy_id'],
                     'initiator': ipsecsiteconnection['initiator'],
                     'ipsecpolicy_id': ipsecsiteconnection[
                         'ipsecpolicy_id'],
                     'mtu': ipsecsiteconnection['mtu'],
                     'peer_address': ipsecsiteconnection['peer_address'],
                     'peer_cidrs': ipsecsiteconnection['peer_cidrs'],
                     'peer_id': ipsecsiteconnection['peer_id'],
                     'psk': ipsecsiteconnection['psk'],
                     'vpnservice_id': ipsecsiteconnection['vpnservice_id'],
                     'admin_state_up': ipsecsiteconnection[
                         'admin_state_up']}

        res = self.client.post(reverse(self.ADDVPNCONNECTION_PATH), form_data)

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, str(self.INDEX_URL))

    @test.create_stubs({api.vpn: ('ikepolicies_get', 'ipsecpolicies_get',
                                  'vpnservices_get',
                                  'ipsecsiteconnection_create')})
    def test_add_ipsecsiteconnection_post_error(self):
        ipsecsiteconnection = self.ipsecsiteconnections.first()

        ikepolicies = self.ikepolicies.list()

        api.vpn.ikepolicies_get(
            IsA(http.HttpRequest)).AndReturn(ikepolicies)

        ipsecpolicies = self.ipsecpolicies.list()

        api.vpn.ipsecpolicies_get(
            IsA(http.HttpRequest)).AndReturn(ipsecpolicies)

        vpnservices = self.vpnservices.list()

        api.vpn.vpnservices_get(
            IsA(http.HttpRequest)).AndReturn(vpnservices)

        self.mox.ReplayAll()

        form_data = {'name': ipsecsiteconnection['name'],
                     'description': ipsecsiteconnection['description'],
                     'dpd_action': ipsecsiteconnection['dpd']['action'],
                     'dpd_interval': ipsecsiteconnection['dpd']['interval'],
                     'dpd_timeout': ipsecsiteconnection['dpd']['timeout'],
                     'ikepolicy_id': '',
                     'initiator': ipsecsiteconnection['initiator'],
                     'ipsecpolicy_id': '',
                     'mtu': ipsecsiteconnection['mtu'],
                     'peer_address': ipsecsiteconnection['peer_address'],
                     'peer_cidrs': ipsecsiteconnection['peer_cidrs'],
                     'peer_id': ipsecsiteconnection['peer_id'],
                     'psk': ipsecsiteconnection['psk'],
                     'vpnservice_id': '',
                     'admin_state_up': ipsecsiteconnection[
                         'admin_state_up']}

        res = self.client.post(reverse(self.ADDVPNCONNECTION_PATH), form_data)

        self.assertFormErrors(res, 3)
