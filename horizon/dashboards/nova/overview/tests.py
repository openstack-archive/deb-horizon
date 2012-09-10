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

import datetime

from django import http
from django.core.urlresolvers import reverse
from django.utils import timezone
from mox import IsA, Func

from horizon import api
from horizon import test
from horizon import usage


INDEX_URL = reverse('horizon:nova:overview:index')


class UsageViewTests(test.TestCase):
    def test_usage(self):
        now = timezone.now()
        usage_obj = api.nova.Usage(self.usages.first())
        self.mox.StubOutWithMock(api, 'usage_get')
        api.usage_get(IsA(http.HttpRequest), self.tenant.id,
                      datetime.datetime(now.year, now.month, 1, 0, 0, 0),
                      Func(usage.almost_now)) \
                      .AndReturn(usage_obj)
        self.mox.ReplayAll()

        res = self.client.get(reverse('horizon:nova:overview:index'))
        self.assertTemplateUsed(res, 'nova/overview/usage.html')
        self.assertTrue(isinstance(res.context['usage'], usage.TenantUsage))
        self.assertContains(res, 'form-horizontal')

    def test_unauthorized(self):
        exc = self.exceptions.keystone_unauthorized
        now = timezone.now()
        self.mox.StubOutWithMock(api, 'usage_get')
        api.usage_get(IsA(http.HttpRequest), self.tenant.id,
                      datetime.datetime(now.year, now.month, 1, 0, 0, 0),
                      Func(usage.almost_now)) \
                      .AndRaise(exc)
        self.mox.ReplayAll()

        url = reverse('horizon:nova:overview:index')
        res = self.client.get(url)
        self.assertRedirects(res, reverse("login") + "?next=" + url)

    def test_usage_csv(self):
        now = timezone.now()
        usage_obj = api.nova.Usage(self.usages.first())
        self.mox.StubOutWithMock(api, 'usage_get')
        timestamp = datetime.datetime(now.year, now.month, 1, 0, 0, 0)
        api.usage_get(IsA(http.HttpRequest),
                      self.tenant.id,
                      timestamp,
                      Func(usage.almost_now)) \
                      .AndReturn(usage_obj)

        self.mox.ReplayAll()
        res = self.client.get(reverse('horizon:nova:overview:index') +
                              "?format=csv")
        self.assertTemplateUsed(res, 'nova/overview/usage.csv')
        self.assertTrue(isinstance(res.context['usage'], usage.TenantUsage))

    def test_usage_exception(self):
        now = timezone.now()
        self.mox.StubOutWithMock(api, 'usage_get')
        timestamp = datetime.datetime(now.year, now.month, 1, 0, 0, 0)
        api.usage_get(IsA(http.HttpRequest),
                      self.tenant.id,
                      timestamp,
                      Func(usage.almost_now)) \
                      .AndRaise(self.exceptions.nova)
        self.mox.ReplayAll()

        res = self.client.get(reverse('horizon:nova:overview:index'))
        self.assertTemplateUsed(res, 'nova/overview/usage.html')
        self.assertEqual(res.context['usage'].usage_list, [])

    def test_usage_default_tenant(self):
        now = timezone.now()
        usage_obj = api.nova.Usage(self.usages.first())
        self.mox.StubOutWithMock(api, 'usage_get')
        timestamp = datetime.datetime(now.year, now.month, 1, 0, 0, 0)
        api.usage_get(IsA(http.HttpRequest),
                      self.tenant.id,
                      timestamp,
                      Func(usage.almost_now)) \
                      .AndReturn(usage_obj)
        self.mox.ReplayAll()

        res = self.client.get(reverse('horizon:nova:overview:index'))
        self.assertTemplateUsed(res, 'nova/overview/usage.html')
        self.assertTrue(isinstance(res.context['usage'], usage.TenantUsage))
