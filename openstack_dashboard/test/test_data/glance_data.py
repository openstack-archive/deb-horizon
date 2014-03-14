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

from glanceclient.v1 import images

from openstack_dashboard.test.test_data import utils


def data(TEST):
    TEST.images = utils.TestDataContainer()
    TEST.snapshots = utils.TestDataContainer()

    # Snapshots
    snapshot_dict = {'name': u'snapshot',
                     'container_format': u'ami',
                     'id': 3,
                     'status': "active",
                     'owner': TEST.tenant.id,
                     'properties': {'image_type': u'snapshot'},
                     'is_public': False,
                     'protected': False}
    snapshot_dict_no_owner = {'name': u'snapshot 2',
                              'container_format': u'ami',
                              'id': 4,
                              'status': "active",
                              'owner': None,
                              'properties': {'image_type': u'snapshot'},
                              'is_public': False,
                              'protected': False}
    snapshot_dict_queued = {'name': u'snapshot 2',
                            'container_format': u'ami',
                            'id': 5,
                            'status': "queued",
                            'owner': TEST.tenant.id,
                            'properties': {'image_type': u'snapshot'},
                            'is_public': False,
                            'protected': False}
    snapshot = images.Image(images.ImageManager(None), snapshot_dict)
    TEST.snapshots.add(snapshot)
    snapshot = images.Image(images.ImageManager(None), snapshot_dict_no_owner)
    TEST.snapshots.add(snapshot)
    snapshot = images.Image(images.ImageManager(None), snapshot_dict_queued)
    TEST.snapshots.add(snapshot)

    # Images
    image_dict = {'id': '007e7d55-fe1e-4c5c-bf08-44b4a4964822',
                  'name': 'public_image',
                  'status': "active",
                  'size': 20 * 1024 ** 3,
                  'min_disk': 0,
                  'owner': TEST.tenant.id,
                  'container_format': 'novaImage',
                  'properties': {'image_type': u'image'},
                  'is_public': True,
                  'protected': False,
                  'min_ram': 0}
    public_image = images.Image(images.ImageManager(None), image_dict)

    image_dict = {'id': 'a001c047-22f8-47d0-80a1-8ec94a9524fe',
                  'name': 'private_image',
                  'status': "active",
                  'size': 10 * 1024 ** 2,
                  'min_disk': 0,
                  'owner': TEST.tenant.id,
                  'container_format': 'aki',
                  'is_public': False,
                  'protected': False,
                  'min_ram': 0}
    private_image = images.Image(images.ImageManager(None), image_dict)

    image_dict = {'id': 'd6936c86-7fec-474a-85c5-5e467b371c3c',
                  'name': 'protected_images',
                  'status': "active",
                  'owner': TEST.tenant.id,
                  'size': 2 * 1024 ** 3,
                  'min_disk': 30,
                  'container_format': 'novaImage',
                  'properties': {'image_type': u'image'},
                  'is_public': True,
                  'protected': True,
                  'min_ram': 0}
    protected_image = images.Image(images.ImageManager(None), image_dict)

    image_dict = {'id': '278905a6-4b52-4d1e-98f9-8c57bb25ba32',
                  'name': None,
                  'status': "active",
                  'size': 5 * 1024 ** 3,
                  'min_disk': 0,
                  'owner': TEST.tenant.id,
                  'container_format': 'novaImage',
                  'properties': {'image_type': u'image'},
                  'is_public': True,
                  'protected': False,
                  'min_ram': 0}
    public_image2 = images.Image(images.ImageManager(None), image_dict)

    image_dict = {'id': '710a1acf-a3e3-41dd-a32d-5d6b6c86ea10',
                  'name': 'private_image 2',
                  'status': "active",
                  'size': 30 * 1024 ** 3,
                  'min_disk': 0,
                  'owner': TEST.tenant.id,
                  'container_format': 'aki',
                  'is_public': False,
                  'protected': False,
                  'min_ram': 0}
    private_image2 = images.Image(images.ImageManager(None), image_dict)

    image_dict = {'id': '7cd892fd-5652-40f3-a450-547615680132',
                  'name': 'private_image 3',
                  'status': "active",
                  'size': 2 * 1024 ** 3,
                  'min_disk': 0,
                  'owner': TEST.tenant.id,
                  'container_format': 'aki',
                  'is_public': False,
                  'protected': False,
                  'min_ram': 0}
    private_image3 = images.Image(images.ImageManager(None), image_dict)

    # A shared image. Not public and not local tenant.
    image_dict = {'id': 'c8756975-7a3b-4e43-b7f7-433576112849',
                  'name': 'shared_image 1',
                  'status': "active",
                  'size': 8 * 1024 ** 3,
                  'min_disk': 0,
                  'owner': 'someothertenant',
                  'container_format': 'aki',
                  'is_public': False,
                  'protected': False,
                  'min_ram': 0}
    shared_image1 = images.Image(images.ImageManager(None), image_dict)

    # "Official" image. Public and tenant matches an entry
    # in IMAGES_LIST_FILTER_TENANTS.
    image_dict = {'id': 'f448704f-0ce5-4d34-8441-11b6581c6619',
                  'name': 'official_image 1',
                  'status': "active",
                  'size': 2 * 1024 ** 3,
                  'min_disk': 0,
                  'owner': 'officialtenant',
                  'container_format': 'aki',
                  'is_public': True,
                  'protected': False,
                  'min_ram': 0}
    official_image1 = images.Image(images.ImageManager(None), image_dict)

    image_dict = {'id': 'a67e7d45-fe1e-4c5c-bf08-44b4a4964822',
                  'name': 'multi_prop_image',
                  'status': "active",
                  'size': 20 * 1024 ** 3,
                  'min_disk': 0,
                  'owner': TEST.tenant.id,
                  'container_format': 'novaImage',
                  'properties': {'description': u'a multi prop image',
                                 'foo': u'foo val',
                                 'bar': u'bar val'},
                  'is_public': True,
                  'protected': False}
    multi_prop_image = images.Image(images.ImageManager(None), image_dict)

    # An image wihout name being returned based on current api
    image_dict = {'id': 'c8756975-7a3b-4e43-b7f7-433576112849',
                  'status': "active",
                  'size': 8 * 1024 ** 3,
                  'min_disk': 0,
                  'owner': 'someothertenant',
                  'container_format': 'aki',
                  'is_public': False,
                  'protected': False}
    no_name_image = images.Image(images.ImageManager(None), image_dict)

    TEST.images.add(public_image, private_image, protected_image,
                    public_image2, private_image2, private_image3,
                    shared_image1, official_image1, multi_prop_image)

    TEST.empty_name_image = no_name_image
