# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2011 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
# Copyright 2011 Nebula, Inc.
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

from django.core.urlresolvers import reverse
from django import http
from mox import IsA  # noqa

from openstack_dashboard import api
from openstack_dashboard.api import cinder
from openstack_dashboard.test import helpers as test
from openstack_dashboard.usage import quotas


INDEX_URL = reverse('horizon:project:images_and_snapshots:index')


class VolumeSnapshotsViewTests(test.TestCase):
    @test.create_stubs({cinder: ('volume_get',),
                        quotas: ('tenant_limit_usages',)})
    def test_create_snapshot_get(self):
        volume = self.volumes.first()
        cinder.volume_get(IsA(http.HttpRequest), volume.id) \
            .AndReturn(volume)
        usage_limit = {'maxTotalVolumeGigabytes': 250,
                       'gigabytesUsed': 20,
                       'volumesUsed': len(self.volumes.list()),
                       'maxTotalVolumes': 6}
        quotas.tenant_limit_usages(IsA(http.HttpRequest)).\
            AndReturn(usage_limit)
        self.mox.ReplayAll()

        url = reverse('horizon:project:volumes:create_snapshot',
                      args=[volume.id])
        res = self.client.get(url)

        self.assertTemplateUsed(res, 'project/volumes/create_snapshot.html')

    @test.create_stubs({cinder: ('volume_get',
                                 'volume_snapshot_create',)})
    def test_create_snapshot_post(self):
        volume = self.volumes.first()
        snapshot = self.volume_snapshots.first()

        cinder.volume_get(IsA(http.HttpRequest), volume.id) \
            .AndReturn(volume)
        cinder.volume_snapshot_create(IsA(http.HttpRequest),
                                      volume.id,
                                      snapshot.display_name,
                                      snapshot.display_description,
                                      force=False) \
            .AndReturn(snapshot)
        self.mox.ReplayAll()

        formData = {'method': 'CreateSnapshotForm',
                    'tenant_id': self.tenant.id,
                    'volume_id': volume.id,
                    'name': snapshot.display_name,
                    'description': snapshot.display_description}
        url = reverse('horizon:project:volumes:create_snapshot',
                      args=[volume.id])
        res = self.client.post(url, formData)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({cinder: ('volume_get',
                                 'volume_snapshot_create',)})
    def test_force_create_snapshot(self):
        volume = self.volumes.get(name='my_volume')
        snapshot = self.volume_snapshots.first()

        cinder.volume_get(IsA(http.HttpRequest), volume.id) \
            .AndReturn(volume)
        cinder.volume_snapshot_create(IsA(http.HttpRequest),
                                      volume.id,
                                      snapshot.display_name,
                                      snapshot.display_description,
                                      force=True) \
            .AndReturn(snapshot)
        self.mox.ReplayAll()

        formData = {'method': 'CreateSnapshotForm',
                    'tenant_id': self.tenant.id,
                    'volume_id': volume.id,
                    'name': snapshot.display_name,
                    'description': snapshot.display_description}
        url = reverse('horizon:project:volumes:create_snapshot',
                      args=[volume.id])
        res = self.client.post(url, formData)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({api.glance: ('image_list_detailed',),
                        api.cinder: ('volume_snapshot_list',
                                     'volume_list',
                                     'volume_snapshot_delete')})
    def test_delete_volume_snapshot(self):
        vol_snapshots = self.volume_snapshots.list()
        volumes = self.volumes.list()
        snapshot = self.volume_snapshots.first()

        api.glance.image_list_detailed(IsA(http.HttpRequest),
                                       marker=None).AndReturn(([], False))
        api.cinder.volume_snapshot_list(IsA(http.HttpRequest)). \
            AndReturn(vol_snapshots)
        api.cinder.volume_list(IsA(http.HttpRequest)) \
            .AndReturn(volumes)

        api.cinder.volume_snapshot_delete(IsA(http.HttpRequest), snapshot.id)
        api.glance.image_list_detailed(IsA(http.HttpRequest),
                                       marker=None).AndReturn(([], False))
        api.cinder.volume_snapshot_list(IsA(http.HttpRequest)). \
            AndReturn([])
        api.cinder.volume_list(IsA(http.HttpRequest)) \
            .AndReturn(volumes)
        self.mox.ReplayAll()

        formData = {'action':
                    'volume_snapshots__delete__%s' % snapshot.id}
        res = self.client.post(INDEX_URL, formData, follow=True)

        self.assertIn("Scheduled deletion of Volume Snapshot: test snapshot",
                      [m.message for m in res.context['messages']])

    @test.create_stubs({api.cinder: ('volume_snapshot_get', 'volume_get')})
    def test_volume_snapshot_detail_get(self):
        volume = self.volumes.first()
        snapshot = self.volume_snapshots.first()

        api.cinder.volume_get(IsA(http.HttpRequest), volume.id). \
            AndReturn(volume)
        api.cinder.volume_snapshot_get(IsA(http.HttpRequest), snapshot.id). \
            AndReturn(snapshot)

        self.mox.ReplayAll()

        url = reverse('horizon:project:images_and_snapshots:detail',
                      args=[snapshot.id])
        res = self.client.get(url)

        self.assertContains(res,
                            "<h2>Volume Snapshot Details: %s</h2>" %
                            snapshot.display_name,
                            1, 200)
        self.assertContains(res, "<dd>test snapshot</dd>", 1, 200)
        self.assertContains(res,
                            "<dd>40f3fabf-3613-4f5e-90e5-6c9a08333fc3</dd>",
                            1,
                            200)
        self.assertContains(res, "<dd>Available</dd>", 1, 200)

    @test.create_stubs({api.cinder: ('volume_snapshot_get',)})
    def test_volume_snapshot_detail_get_with_exception(self):
        # Test to verify redirect if get volume snapshot fails
        snapshot = self.volume_snapshots.first()

        api.cinder.volume_snapshot_get(IsA(http.HttpRequest), snapshot.id).\
            AndRaise(self.exceptions.cinder)
        self.mox.ReplayAll()

        url = reverse('horizon:project:images_and_snapshots:detail',
                      args=[snapshot.id])
        res = self.client.get(url)

        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({api.cinder: ('volume_snapshot_get', 'volume_get')})
    def test_volume_snapshot_detail_with_volume_get_exception(self):
        # Test to verify redirect if get volume fails
        volume = self.volumes.first()
        snapshot = self.volume_snapshots.first()

        api.cinder.volume_get(IsA(http.HttpRequest), volume.id). \
            AndRaise(self.exceptions.cinder)
        api.cinder.volume_snapshot_get(IsA(http.HttpRequest), snapshot.id). \
            AndReturn(snapshot)

        self.mox.ReplayAll()

        url = reverse('horizon:project:images_and_snapshots:detail',
                      args=[snapshot.id])
        res = self.client.get(url)

        self.assertRedirectsNoFollow(res, INDEX_URL)
