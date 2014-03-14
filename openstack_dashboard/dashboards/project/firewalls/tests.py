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

from mox import IsA  # noqa

from django.core.urlresolvers import reverse
from django.core.urlresolvers import reverse_lazy
from django import http

from openstack_dashboard import api
from openstack_dashboard.api import fwaas
from openstack_dashboard.test import helpers as test


class FirewallTests(test.TestCase):
    class AttributeDict(dict):
        def __getattr__(self, attr):
            return self[attr]

        def __setattr__(self, attr, value):
            self[attr] = value

    DASHBOARD = 'project'
    INDEX_URL = reverse_lazy('horizon:%s:firewalls:index' % DASHBOARD)

    ADDRULE_PATH = 'horizon:%s:firewalls:addrule' % DASHBOARD
    ADDPOLICY_PATH = 'horizon:%s:firewalls:addpolicy' % DASHBOARD
    ADDFIREWALL_PATH = 'horizon:%s:firewalls:addfirewall' % DASHBOARD

    RULE_DETAIL_PATH = 'horizon:%s:firewalls:ruledetails' % DASHBOARD
    POLICY_DETAIL_PATH = 'horizon:%s:firewalls:policydetails' % DASHBOARD
    FIREWALL_DETAIL_PATH = 'horizon:%s:firewalls:firewalldetails' % DASHBOARD

    UPDATERULE_PATH = 'horizon:%s:firewalls:updaterule' % DASHBOARD
    UPDATEPOLICY_PATH = 'horizon:%s:firewalls:updatepolicy' % DASHBOARD
    UPDATEFIREWALL_PATH = 'horizon:%s:firewalls:updatefirewall' % DASHBOARD

    INSERTRULE_PATH = 'horizon:%s:firewalls:insertrule' % DASHBOARD
    REMOVERULE_PATH = 'horizon:%s:firewalls:removerule' % DASHBOARD

    def set_up_expect(self):
        # retrieve rules
        tenant_id = self.tenant.id

        api.fwaas.rule_list(
            IsA(http.HttpRequest),
            tenant_id=tenant_id).AndReturn(self.fw_rules.list())

        # retrieves policies
        policies = self.fw_policies.list()
        api.fwaas.policy_list(
            IsA(http.HttpRequest), tenant_id=tenant_id).AndReturn(policies)

        # retrieves firewalls
        firewalls = self.firewalls.list()
        api.fwaas.firewall_list(
            IsA(http.HttpRequest), tenant_id=tenant_id).AndReturn(firewalls)

    def set_up_expect_with_exception(self):
        tenant_id = self.tenant.id

        api.fwaas.rule_list(
            IsA(http.HttpRequest),
            tenant_id=tenant_id).AndRaise(self.exceptions.neutron)
        api.fwaas.policy_list(
            IsA(http.HttpRequest),
            tenant_id=tenant_id).AndRaise(self.exceptions.neutron)
        api.fwaas.firewall_list(
            IsA(http.HttpRequest),
            tenant_id=tenant_id).AndRaise(self.exceptions.neutron)

    @test.create_stubs({api.fwaas: ('firewall_list',
                                    'policy_list',
                                    'rule_list')}, )
    def test_index_firewalls(self):
        self.set_up_expect()

        self.mox.ReplayAll()

        tenant_id = self.tenant.id

        res = self.client.get(self.INDEX_URL, tenant_id=tenant_id)

        self.assertTemplateUsed(res, '%s/firewalls/details_tabs.html'
                                % self.DASHBOARD)
        self.assertTemplateUsed(res, 'horizon/common/_detail_table.html')
        self.assertEqual(len(res.context['table'].data),
                         len(self.firewalls.list()))

    @test.create_stubs({api.fwaas: ('firewall_list',
                                    'policy_list',
                                    'rule_list')}, )
    def test_index_policies(self):
        self.set_up_expect()

        self.mox.ReplayAll()

        tenant_id = self.tenant.id

        res = self.client.get(self.INDEX_URL + '?tab=fwtabs__policies',
                              tenant_id=tenant_id)

        self.assertTemplateUsed(res, '%s/firewalls/details_tabs.html'
                                % self.DASHBOARD)
        self.assertTemplateUsed(res, 'horizon/common/_detail_table.html')
        self.assertEqual(len(res.context['policiestable_table'].data),
                         len(self.fw_policies.list()))

    @test.create_stubs({api.fwaas: ('firewall_list',
                                    'policy_list',
                                    'rule_list')}, )
    def test_index_rules(self):
        self.set_up_expect()

        self.mox.ReplayAll()

        tenant_id = self.tenant.id

        res = self.client.get(self.INDEX_URL + '?tab=fwtabs__rules',
                              tenant_id=tenant_id)

        self.assertTemplateUsed(res, '%s/firewalls/details_tabs.html'
                                % self.DASHBOARD)
        self.assertTemplateUsed(res, 'horizon/common/_detail_table.html')
        self.assertEqual(len(res.context['rulestable_table'].data),
                         len(self.fw_rules.list()))

    @test.create_stubs({api.fwaas: ('firewall_list',
                                    'policy_list',
                                    'rule_list')}, )
    def test_index_exception_firewalls(self):
        self.set_up_expect_with_exception()

        self.mox.ReplayAll()

        tenant_id = self.tenant.id

        res = self.client.get(self.INDEX_URL, tenant_id=tenant_id)

        self.assertTemplateUsed(res,
                                '%s/firewalls/details_tabs.html'
                                % self.DASHBOARD)
        self.assertTemplateUsed(res,
                                'horizon/common/_detail_table.html')
        self.assertEqual(len(res.context['table'].data), 0)

    @test.create_stubs({api.fwaas: ('firewall_list',
                                    'policy_list',
                                    'rule_list')}, )
    def test_index_exception_policies(self):
        self.set_up_expect_with_exception()

        self.mox.ReplayAll()

        tenant_id = self.tenant.id

        res = self.client.get(self.INDEX_URL + '?tab=fwtabs__policies',
                              tenant_id=tenant_id)

        self.assertTemplateUsed(res,
                                '%s/firewalls/details_tabs.html'
                                % self.DASHBOARD)
        self.assertTemplateUsed(res,
                                'horizon/common/_detail_table.html')
        self.assertEqual(len(res.context['policiestable_table'].data), 0)

    @test.create_stubs({api.fwaas: ('firewall_list',
                                    'policy_list',
                                    'rule_list')}, )
    def test_index_exception_rules(self):
        self.set_up_expect_with_exception()

        self.mox.ReplayAll()

        tenant_id = self.tenant.id

        res = self.client.get(self.INDEX_URL + '?tab=fwtabs__rules',
                              tenant_id=tenant_id)

        self.assertTemplateUsed(res,
                                '%s/firewalls/details_tabs.html'
                                % self.DASHBOARD)
        self.assertTemplateUsed(res,
                                'horizon/common/_detail_table.html')
        self.assertEqual(len(res.context['rulestable_table'].data), 0)

    @test.create_stubs({api.fwaas: ('rule_create',), })
    def test_add_rule_post(self):
        rule1 = self.fw_rules.first()

        form_data = {'name': rule1.name,
                     'description': rule1.description,
                     'protocol': rule1.protocol,
                     'action': rule1.action,
                     'source_ip_address': rule1.source_ip_address,
                     'source_port': rule1.source_port,
                     'destination_ip_address': rule1.destination_ip_address,
                     'destination_port': rule1.destination_port,
                     'shared': rule1.shared,
                     'enabled': rule1.enabled
                     }

        api.fwaas.rule_create(
            IsA(http.HttpRequest), **form_data).AndReturn(rule1)

        self.mox.ReplayAll()

        res = self.client.post(reverse(self.ADDRULE_PATH), form_data)

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, str(self.INDEX_URL))

    def test_add_rule_post_with_error(self):
        rule1 = self.fw_rules.first()

        form_data = {'name': rule1.name,
                     'description': rule1.description,
                     'protocol': 'abc',
                     'action': 'pass',
                     'source_ip_address': rule1.source_ip_address,
                     'source_port': rule1.source_port,
                     'destination_ip_address': rule1.destination_ip_address,
                     'destination_port': rule1.destination_port,
                     'shared': rule1.shared,
                     'enabled': rule1.enabled
                     }

        self.mox.ReplayAll()

        res = self.client.post(reverse(self.ADDRULE_PATH), form_data)

        self.assertFormErrors(res, 2)

    @test.create_stubs({api.fwaas: ('policy_create', 'rule_list'), })
    def test_add_policy_post(self):
        policy = self.fw_policies.first()
        rules = self.fw_rules.list()
        tenant_id = self.tenant.id
        form_data = {'name': policy.name,
                     'description': policy.description,
                     'firewall_rules': policy.firewall_rules,
                     'shared': policy.shared,
                     'audited': policy.audited
                     }
        post_data = {'name': policy.name,
                     'description': policy.description,
                     'rule': policy.firewall_rules,
                     'shared': policy.shared,
                     'audited': policy.audited
                     }

        # NOTE: SelectRulesAction.populate_rule_choices() lists rule not
        # associated with any policy. We need to ensure that rules specified
        # in policy.firewall_rules in post_data (above) are not associated
        # with any policy. Test data in neutron_data is data in a stable state,
        # so we need to modify here.
        for rule in rules:
            if rule.id in policy.firewall_rules:
                rule.firewall_policy_id = rule.policy = None
        api.fwaas.rule_list(
            IsA(http.HttpRequest), tenant_id=tenant_id).AndReturn(rules)
        api.fwaas.policy_create(
            IsA(http.HttpRequest), **form_data).AndReturn(policy)

        self.mox.ReplayAll()

        res = self.client.post(reverse(self.ADDPOLICY_PATH), post_data)

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, str(self.INDEX_URL))

    @test.create_stubs({api.fwaas: ('policy_create', 'rule_list'), })
    def test_add_policy_post_with_error(self):
        policy = self.fw_policies.first()
        rules = self.fw_rules.list()
        tenant_id = self.tenant.id
        form_data = {'description': policy.description,
                     'firewall_rules': None,
                     'shared': policy.shared,
                     'audited': policy.audited
                     }
        api.fwaas.rule_list(
            IsA(http.HttpRequest), tenant_id=tenant_id).AndReturn(rules)

        self.mox.ReplayAll()

        res = self.client.post(reverse(self.ADDPOLICY_PATH), form_data)

        self.assertFormErrors(res, 1)

    @test.create_stubs({api.fwaas: ('firewall_create', 'policy_list'), })
    def test_add_firewall_post(self):
        firewall = self.firewalls.first()
        policies = self.fw_policies.list()
        tenant_id = self.tenant.id
        form_data = {'name': firewall.name,
                     'description': firewall.description,
                     'firewall_policy_id': firewall.firewall_policy_id,
                     'shared': firewall.shared,
                     'admin_state_up': firewall.admin_state_up
                     }
        api.fwaas.policy_list(
            IsA(http.HttpRequest), tenant_id=tenant_id).AndReturn(policies)
        api.fwaas.firewall_create(
            IsA(http.HttpRequest), **form_data).AndReturn(firewall)

        self.mox.ReplayAll()

        res = self.client.post(reverse(self.ADDFIREWALL_PATH), form_data)

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, str(self.INDEX_URL))

    @test.create_stubs({api.fwaas: ('firewall_create', 'policy_list'), })
    def test_add_firewall_post_with_error(self):
        firewall = self.firewalls.first()
        policies = self.fw_policies.list()
        tenant_id = self.tenant.id
        form_data = {'name': firewall.name,
                     'description': firewall.description,
                     'firewall_policy_id': None,
                     'shared': firewall.shared,
                     'admin_state_up': firewall.admin_state_up
                     }
        api.fwaas.policy_list(
            IsA(http.HttpRequest), tenant_id=tenant_id).AndReturn(policies)

        self.mox.ReplayAll()

        res = self.client.post(reverse(self.ADDFIREWALL_PATH), form_data)

        self.assertFormErrors(res, 1)

    @test.create_stubs({api.fwaas: ('rule_get',)})
    def test_update_rule_get(self):
        rule = self.fw_rules.first()

        api.fwaas.rule_get(IsA(http.HttpRequest), rule.id).AndReturn(rule)

        self.mox.ReplayAll()

        res = self.client.get(reverse(self.UPDATERULE_PATH, args=(rule.id,)))

        self.assertTemplateUsed(res, 'project/firewalls/updaterule.html')

    @test.create_stubs({api.fwaas: ('rule_get', 'rule_update')})
    def test_update_rule_post(self):
        rule = self.fw_rules.first()

        api.fwaas.rule_get(IsA(http.HttpRequest), rule.id).AndReturn(rule)

        data = {'name': 'new name',
                'description': 'new desc',
                'protocol': 'ICMP',
                'action': 'ALLOW',
                'shared': False,
                'enabled': True,
                'source_ip_address': rule.source_ip_address,
                'destination_ip_address': None,
                'source_port': None,
                'destination_port': rule.destination_port,
                }

        api.fwaas.rule_update(IsA(http.HttpRequest), rule.id, **data)\
            .AndReturn(rule)

        self.mox.ReplayAll()

        form_data = data.copy()
        form_data['destination_ip_address'] = ''
        form_data['source_port'] = ''

        res = self.client.post(
            reverse(self.UPDATERULE_PATH, args=(rule.id,)), form_data)

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, str(self.INDEX_URL))

    @test.create_stubs({api.fwaas: ('policy_get',)})
    def test_update_policy_get(self):
        policy = self.fw_policies.first()

        api.fwaas.policy_get(IsA(http.HttpRequest),
                             policy.id).AndReturn(policy)

        self.mox.ReplayAll()

        res = self.client.get(
            reverse(self.UPDATEPOLICY_PATH, args=(policy.id,)))

        self.assertTemplateUsed(res, 'project/firewalls/updatepolicy.html')

    @test.create_stubs({api.fwaas: ('policy_get', 'policy_update',
                                    'rule_list')})
    def test_update_policy_post(self):
        policy = self.fw_policies.first()

        api.fwaas.policy_get(IsA(http.HttpRequest),
                             policy.id).AndReturn(policy)

        data = {'name': 'new name',
                'description': 'new desc',
                'shared': True,
                'audited': False
                }

        api.fwaas.policy_update(IsA(http.HttpRequest), policy.id, **data)\
            .AndReturn(policy)

        self.mox.ReplayAll()

        res = self.client.post(
            reverse(self.UPDATEPOLICY_PATH, args=(policy.id,)), data)

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, str(self.INDEX_URL))

    @test.create_stubs({api.fwaas: ('firewall_get', 'policy_list')})
    def test_update_firewall_get(self):
        firewall = self.firewalls.first()
        policies = self.fw_policies.list()
        tenant_id = self.tenant.id

        api.fwaas.policy_list(
            IsA(http.HttpRequest), tenant_id=tenant_id).AndReturn(policies)

        api.fwaas.firewall_get(IsA(http.HttpRequest),
                               firewall.id).AndReturn(firewall)

        self.mox.ReplayAll()

        res = self.client.get(
            reverse(self.UPDATEFIREWALL_PATH, args=(firewall.id,)))

        self.assertTemplateUsed(res, 'project/firewalls/updatefirewall.html')

    @test.create_stubs({api.fwaas: ('firewall_get', 'policy_list',
                                    'firewall_update')})
    def test_update_firewall_post(self):
        firewall = self.firewalls.first()
        tenant_id = self.tenant.id
        api.fwaas.firewall_get(IsA(http.HttpRequest),
                               firewall.id).AndReturn(firewall)

        data = {'name': 'new name',
                'description': 'new desc',
                'firewall_policy_id': firewall.firewall_policy_id,
                'admin_state_up': False
                }

        policies = self.fw_policies.list()
        api.fwaas.policy_list(
            IsA(http.HttpRequest), tenant_id=tenant_id).AndReturn(policies)

        api.fwaas.firewall_update(IsA(http.HttpRequest), firewall.id, **data)\
            .AndReturn(firewall)

        self.mox.ReplayAll()

        res = self.client.post(
            reverse(self.UPDATEFIREWALL_PATH, args=(firewall.id,)), data)

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, str(self.INDEX_URL))

    @test.create_stubs({api.fwaas: ('policy_get', 'policy_insert_rule',
                                    'rule_list', 'rule_get')})
    def test_policy_insert_rule(self):
        policy = self.fw_policies.first()
        tenant_id = self.tenant.id
        rules = self.fw_rules.list()

        new_rule_id = rules[2].id

        data = {'firewall_rule_id': new_rule_id,
                'insert_before': rules[1].id,
                'insert_after': rules[0].id}

        api.fwaas.policy_get(IsA(http.HttpRequest),
                             policy.id).AndReturn(policy)

        policy.firewall_rules = [rules[0].id,
                                 new_rule_id,
                                 rules[1].id]

        api.fwaas.rule_list(
            IsA(http.HttpRequest), tenant_id=tenant_id).AndReturn(rules)
        api.fwaas.rule_get(
            IsA(http.HttpRequest), new_rule_id).AndReturn(rules[2])
        api.fwaas.policy_insert_rule(IsA(http.HttpRequest), policy.id, **data)\
            .AndReturn(policy)

        self.mox.ReplayAll()

        res = self.client.post(
            reverse(self.INSERTRULE_PATH, args=(policy.id,)), data)

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, str(self.INDEX_URL))

    @test.create_stubs({api.fwaas: ('policy_get', 'policy_remove_rule',
                                    'rule_list', 'rule_get')})
    def test_policy_remove_rule(self):
        policy = self.fw_policies.first()
        tenant_id = self.tenant.id
        rules = self.fw_rules.list()

        remove_rule_id = policy.firewall_rules[0]
        left_rule_id = policy.firewall_rules[1]

        data = {'firewall_rule_id': remove_rule_id}

        after_remove_policy_dict = {'id': 'abcdef-c3eb-4fee-9763-12de3338041e',
                                    'tenant_id': '1',
                                    'name': 'policy1',
                                    'description': 'policy description',
                                    'firewall_rules': [left_rule_id],
                                    'audited': True,
                                    'shared': True}
        after_remove_policy = fwaas.Policy(after_remove_policy_dict)

        api.fwaas.policy_get(IsA(http.HttpRequest),
                             policy.id).AndReturn(policy)
        api.fwaas.rule_list(
            IsA(http.HttpRequest), tenant_id=tenant_id).AndReturn(rules)
        api.fwaas.rule_get(
            IsA(http.HttpRequest), remove_rule_id).AndReturn(rules[0])
        api.fwaas.policy_remove_rule(IsA(http.HttpRequest), policy.id, **data)\
            .AndReturn(after_remove_policy)

        self.mox.ReplayAll()

        res = self.client.post(
            reverse(self.REMOVERULE_PATH, args=(policy.id,)), data)

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, str(self.INDEX_URL))

    @test.create_stubs({api.fwaas: ('firewall_list',
                                    'policy_list',
                                    'rule_list',
                                    'rule_delete')})
    def test_delete_rule(self):
        self.set_up_expect()
        rule = self.fw_rules.first()
        api.fwaas.rule_delete(IsA(http.HttpRequest), rule.id)
        self.mox.ReplayAll()

        form_data = {"action": "rulestable__deleterule__%s" % rule.id}
        res = self.client.post(self.INDEX_URL, form_data)

        self.assertNoFormErrors(res)

    @test.create_stubs({api.fwaas: ('firewall_list',
                                    'policy_list',
                                    'rule_list',
                                    'policy_delete')})
    def test_delete_policy(self):
        self.set_up_expect()
        policy = self.fw_policies.first()
        api.fwaas.policy_delete(IsA(http.HttpRequest), policy.id)
        self.mox.ReplayAll()

        form_data = {"action": "policiestable__deletepolicy__%s" % policy.id}
        res = self.client.post(self.INDEX_URL, form_data)

        self.assertNoFormErrors(res)

    @test.create_stubs({api.fwaas: ('firewall_list',
                                    'policy_list',
                                    'rule_list',
                                    'firewall_delete')})
    def test_delete_firewall(self):
        self.set_up_expect()
        fwl = self.firewalls.first()
        api.fwaas.firewall_delete(IsA(http.HttpRequest), fwl.id)
        self.mox.ReplayAll()

        form_data = {"action": "firewallstable__deletefirewall__%s" % fwl.id}
        res = self.client.post(self.INDEX_URL, form_data)

        self.assertNoFormErrors(res)
