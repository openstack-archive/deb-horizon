# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2013 Hewlett-Packard Development Company, L.P.
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

from mox import IgnoreArg, IsA

from openstack_dashboard import api
from openstack_dashboard.test import helpers as test

from .constants import GROUPS_INDEX_VIEW_TEMPLATE, \
    GROUPS_MANAGE_VIEW_TEMPLATE, \
    GROUPS_INDEX_URL as index_url, \
    GROUPS_CREATE_URL as create_url, \
    GROUPS_UPDATE_URL as update_url, \
    GROUPS_MANAGE_URL as manage_url, \
    GROUPS_ADD_MEMBER_URL as add_member_url


GROUPS_INDEX_URL = reverse(index_url)
GROUP_CREATE_URL = reverse(create_url)
GROUP_UPDATE_URL = reverse(update_url, args=[1])
GROUP_MANAGE_URL = reverse(manage_url, args=[1])
GROUP_ADD_MEMBER_URL = reverse(add_member_url, args=[1])


class GroupsViewTests(test.BaseAdminViewTests):
    @test.create_stubs({api.keystone: ('group_list',)})
    def test_index(self):
        api.keystone.group_list(IgnoreArg()).AndReturn(self.groups.list())

        self.mox.ReplayAll()

        res = self.client.get(GROUPS_INDEX_URL)

        self.assertTemplateUsed(res, GROUPS_INDEX_VIEW_TEMPLATE)
        self.assertItemsEqual(res.context['table'].data, self.groups.list())

        self.assertContains(res, 'Create Group')
        self.assertContains(res, 'Edit')
        self.assertContains(res, 'Delete Group')

    @test.create_stubs({api.keystone: ('group_list',
                                       'keystone_can_edit_group')})
    def test_index_with_keystone_can_edit_group_false(self):
        api.keystone.group_list(IgnoreArg()).AndReturn(self.groups.list())
        api.keystone.keystone_can_edit_group() \
            .MultipleTimes().AndReturn(False)

        self.mox.ReplayAll()

        res = self.client.get(GROUPS_INDEX_URL)

        self.assertTemplateUsed(res, GROUPS_INDEX_VIEW_TEMPLATE)
        self.assertItemsEqual(res.context['table'].data, self.groups.list())

        self.assertNotContains(res, 'Create Group')
        self.assertNotContains(res, 'Edit')
        self.assertNotContains(res, 'Delete Group')

    @test.create_stubs({api.keystone: ('group_create', )})
    def test_create(self):
        group = self.groups.get(id="1")

        api.keystone.group_create(IsA(http.HttpRequest),
                                  description=group.description,
                                  domain_id=None,
                                  name=group.name).AndReturn(group)

        self.mox.ReplayAll()

        formData = {'method': 'CreateGroupForm',
                    'name': group.name,
                    'description': group.description}
        res = self.client.post(GROUP_CREATE_URL, formData)

        self.assertNoFormErrors(res)
        self.assertMessageCount(success=1)

    @test.create_stubs({api.keystone: ('group_get',
                                       'group_update')})
    def test_update(self):
        group = self.groups.get(id="1")
        test_description = 'updated description'

        api.keystone.group_get(IsA(http.HttpRequest), '1').AndReturn(group)
        api.keystone.group_update(IsA(http.HttpRequest),
                                  description=test_description,
                                  group_id=group.id,
                                  name=group.name).AndReturn(None)

        self.mox.ReplayAll()

        formData = {'method': 'UpdateGroupForm',
                    'group_id': group.id,
                    'name': group.name,
                    'description': test_description}

        res = self.client.post(GROUP_UPDATE_URL, formData)

        self.assertNoFormErrors(res)

    @test.create_stubs({api.keystone: ('group_list',
                                       'group_delete')})
    def test_delete_group(self):
        group = self.groups.get(id="2")

        api.keystone.group_list(IgnoreArg()).AndReturn(self.groups.list())
        api.keystone.group_delete(IgnoreArg(), group.id)

        self.mox.ReplayAll()

        formData = {'action': 'groups__delete__%s' % group.id}
        res = self.client.post(GROUPS_INDEX_URL, formData)

        self.assertRedirectsNoFollow(res, GROUPS_INDEX_URL)

    @test.create_stubs({api.keystone: ('group_get',
                                       'user_list',)})
    def test_manage(self):
        group = self.groups.get(id="1")
        group_members = self.users.list()

        api.keystone.group_get(IsA(http.HttpRequest), group.id).\
            AndReturn(group)
        api.keystone.user_list(IgnoreArg(),
                               group=group.id).\
            AndReturn(group_members)
        self.mox.ReplayAll()

        res = self.client.get(GROUP_MANAGE_URL)

        self.assertTemplateUsed(res, GROUPS_MANAGE_VIEW_TEMPLATE)
        self.assertItemsEqual(res.context['table'].data, group_members)

    @test.create_stubs({api.keystone: ('user_list',
                                       'remove_group_user')})
    def test_remove_user(self):
        group = self.groups.get(id="1")
        user = self.users.get(id="2")

        api.keystone.user_list(IgnoreArg(),
                               group=group.id).\
            AndReturn(self.users.list())
        api.keystone.remove_group_user(IgnoreArg(),
                                       group_id=group.id,
                                       user_id=user.id)
        self.mox.ReplayAll()

        formData = {'action': 'group_members__removeGroupMember__%s' % user.id}
        res = self.client.post(GROUP_MANAGE_URL, formData)

        self.assertRedirectsNoFollow(res, GROUP_MANAGE_URL)
        self.assertMessageCount(success=1)

    @test.create_stubs({api.keystone: ('group_get',
                                       'user_list',
                                       'add_group_user')})
    def test_add_user(self):
        group = self.groups.get(id="1")
        user = self.users.get(id="2")

        api.keystone.group_get(IsA(http.HttpRequest), group.id).\
            AndReturn(group)
        api.keystone.user_list(IgnoreArg(),
                               domain=group.domain_id).\
            AndReturn(self.users.list())
        api.keystone.user_list(IgnoreArg(),
                               group=group.id).\
            AndReturn(self.users.list()[2:])

        api.keystone.add_group_user(IgnoreArg(),
                                    group_id=group.id,
                                    user_id=user.id)

        self.mox.ReplayAll()

        formData = {'action': 'group_non_members__addMember__%s' % user.id}
        res = self.client.post(GROUP_ADD_MEMBER_URL, formData)

        self.assertRedirectsNoFollow(res, GROUP_MANAGE_URL)
        self.assertMessageCount(success=1)
