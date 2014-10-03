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

import tempfile

from django.core.files.uploadedfile import InMemoryUploadedFile  # noqa
from django.core.urlresolvers import reverse
from django import http
from django.utils import http as utils_http

from mox import IsA  # noqa

from openstack_dashboard import api
from openstack_dashboard.dashboards.project.containers import forms
from openstack_dashboard.dashboards.project.containers import tables
from openstack_dashboard.dashboards.project.containers import views
from openstack_dashboard.test import helpers as test


CONTAINER_NAME_1 = u"container one%\u6346"
CONTAINER_NAME_2 = u"container_two\u6346"
CONTAINER_NAME_1_QUOTED = utils_http.urlquote(CONTAINER_NAME_1)
CONTAINER_NAME_2_QUOTED = utils_http.urlquote(CONTAINER_NAME_2)
CONTAINER_INDEX_URL = reverse('horizon:project:containers:index')


class SwiftTests(test.TestCase):
    @test.create_stubs({api.swift: ('swift_get_containers',)})
    def test_index_no_container_selected(self):
        containers = self.containers.list()
        api.swift.swift_get_containers(IsA(http.HttpRequest), marker=None) \
            .AndReturn((containers, False))
        self.mox.ReplayAll()

        res = self.client.get(CONTAINER_INDEX_URL)

        self.assertTemplateUsed(res, 'project/containers/index.html')
        self.assertIn('table', res.context)
        resp_containers = res.context['table'].data
        self.assertEqual(len(resp_containers), len(containers))

    @test.create_stubs({api.swift: ('swift_delete_container', )})
    def test_delete_container(self):
        for container in self.containers.list():
            self.mox.ResetAll()  # mandatory in a for loop
            api.swift.swift_delete_container(IsA(http.HttpRequest),
                                             container.name)
            self.mox.ReplayAll()

            action_string = u"containers__delete__%s" % container.name
            form_data = {"action": action_string}
            req = self.factory.post(CONTAINER_INDEX_URL, form_data)
            table = tables.ContainersTable(req, self.containers.list())
            handled = table.maybe_handle()
            self.assertEqual(handled['location'], CONTAINER_INDEX_URL)

    @test.create_stubs({api.swift: ('swift_get_objects', )})
    def test_delete_container_nonempty(self):
        container = self.containers.first()
        objects = self.objects.list()
        api.swift.swift_get_objects(IsA(http.HttpRequest),
                                    container.name).AndReturn([objects, False])
        self.mox.ReplayAll()

        action_string = u"containers__delete__%s" % container.name
        form_data = {"action": action_string}
        req = self.factory.post(CONTAINER_INDEX_URL, form_data)
        table = tables.ContainersTable(req, self.containers.list())
        handled = table.maybe_handle()
        self.assertEqual(handled['location'], CONTAINER_INDEX_URL)
        self.assertEqual(unicode(list(req._messages)[0].message),
                         u"The container cannot be deleted "
                         u"since it's not empty.")

    def test_create_container_get(self):
        res = self.client.get(reverse('horizon:project:containers:create'))
        self.assertTemplateUsed(res, 'project/containers/create.html')

    @test.create_stubs({api.swift: ('swift_create_container',)})
    def test_create_container_post(self):
        for container in self.containers.list():
            self.mox.ResetAll()  # mandatory in a for loop
            api.swift.swift_create_container(IsA(http.HttpRequest),
                                             container.name,
                                             metadata=({'is_public': False}))
            self.mox.ReplayAll()

            formData = {'name': container.name,
                        'access': "private",
                        'method': forms.CreateContainer.__name__}
            res = self.client.post(
                reverse('horizon:project:containers:create'), formData)
            args = (utils_http.urlquote(tables.wrap_delimiter(
                container.name)),)
            url = reverse('horizon:project:containers:index', args=args)
            self.assertRedirectsNoFollow(res, url)

    @test.create_stubs({api.swift: ('swift_update_container', )})
    def test_update_container_to_public(self):
        container = self.containers.get(name=u"container one%\u6346")
        api.swift.swift_update_container(IsA(http.HttpRequest),
                                         container.name,
                                         metadata=({'is_public': True}))
        self.mox.ReplayAll()

        action_string = u"containers__make_public__%s" % container.name
        form_data = {"action": action_string}
        req = self.factory.post(CONTAINER_INDEX_URL, form_data)
        table = tables.ContainersTable(req, self.containers.list())
        handled = table.maybe_handle()
        self.assertEqual(handled['location'], CONTAINER_INDEX_URL)

    @test.create_stubs({api.swift: ('swift_update_container', )})
    def test_update_container_to_private(self):
        container = self.containers.get(name=u"container_two\u6346")
        api.swift.swift_update_container(IsA(http.HttpRequest),
                                         container.name,
                                         metadata=({'is_public': False}))
        self.mox.ReplayAll()

        action_string = u"containers__make_private__%s" % container.name
        form_data = {"action": action_string}
        req = self.factory.post(CONTAINER_INDEX_URL, form_data)
        table = tables.ContainersTable(req, self.containers.list())
        handled = table.maybe_handle()
        self.assertEqual(handled['location'], CONTAINER_INDEX_URL)

    @test.create_stubs({api.swift: ('swift_get_containers',
                                    'swift_get_objects')})
    def test_index_container_selected(self):
        containers = (self.containers.list(), False)
        ret = (self.objects.list(), False)
        api.swift.swift_get_containers(IsA(http.HttpRequest),
                                       marker=None).AndReturn(containers)
        api.swift.swift_get_objects(IsA(http.HttpRequest),
                                    self.containers.first().name,
                                    marker=None,
                                    prefix=None).AndReturn(ret)
        self.mox.ReplayAll()

        res = self.client.get(reverse('horizon:project:containers:index',
            args=[tables.wrap_delimiter(self.containers.first().name)]))
        self.assertTemplateUsed(res, 'project/containers/index.html')
        # UTF8 encoding here to ensure there aren't problems with Nose output.
        expected = [obj.name.encode('utf8') for obj in self.objects.list()]
        self.assertQuerysetEqual(res.context['objects_table'].data,
                                 expected,
                                 lambda obj: obj.name.encode('utf8'))
        # Check if the two forms' URL are properly 'urlquote()d'.
        form_action = ' action="%s%s/" ' % (CONTAINER_INDEX_URL,
                                            CONTAINER_NAME_1_QUOTED)
        self.assertContains(res, form_action, count=2)

    @test.create_stubs({api.swift: ('swift_upload_object',)})
    def test_upload(self):
        container = self.containers.first()
        obj = self.objects.first()
        OBJECT_DATA = 'objectData'

        temp_file = tempfile.TemporaryFile()
        temp_file.write(OBJECT_DATA)
        temp_file.flush()
        temp_file.seek(0)

        api.swift.swift_upload_object(IsA(http.HttpRequest),
                                      container.name,
                                      obj.name,
                                      IsA(InMemoryUploadedFile)).AndReturn(obj)
        self.mox.ReplayAll()

        upload_url = reverse('horizon:project:containers:object_upload',
                             args=[container.name])

        res = self.client.get(upload_url)
        self.assertTemplateUsed(res, 'project/containers/upload.html')

        res = self.client.get(upload_url)
        self.assertContains(res, 'enctype="multipart/form-data"')

        formData = {'method': forms.UploadObject.__name__,
                    'container_name': container.name,
                    'name': obj.name,
                    'object_file': temp_file}
        res = self.client.post(upload_url, formData)

        args = (utils_http.urlquote(tables.wrap_delimiter(container.name)),)
        index_url = reverse('horizon:project:containers:index', args=args)
        self.assertRedirectsNoFollow(res, index_url)

    @test.create_stubs({api.swift: ('swift_upload_object',)})
    def test_upload_without_file(self):
        container = self.containers.first()
        obj = self.objects.first()

        api.swift.swift_upload_object(IsA(http.HttpRequest),
                                      container.name,
                                      obj.name,
                                      None).AndReturn(obj)
        self.mox.ReplayAll()

        upload_url = reverse('horizon:project:containers:object_upload',
                             args=[container.name])

        res = self.client.get(upload_url)
        self.assertTemplateUsed(res, 'project/containers/upload.html')

        res = self.client.get(upload_url)
        self.assertContains(res, 'enctype="multipart/form-data"')

        formData = {'method': forms.UploadObject.__name__,
                    'container_name': container.name,
                    'name': obj.name,
                    'object_file': None}
        res = self.client.post(upload_url, formData)

        args = (utils_http.urlquote(tables.wrap_delimiter(container.name)),)
        index_url = reverse('horizon:project:containers:index', args=args)
        self.assertRedirectsNoFollow(res, index_url)

    @test.create_stubs({api.swift: ('swift_create_pseudo_folder',)})
    def test_create_pseudo_folder(self):
        container = self.containers.first()
        obj = self.objects.first()

        api.swift.swift_create_pseudo_folder(IsA(http.HttpRequest),
                                      container.name,
                                      obj.name + "/").AndReturn(obj)
        self.mox.ReplayAll()

        create_pseudo_folder_url = reverse('horizon:project:containers:'
                                           'create_pseudo_folder',
                                           args=[container.name])

        res = self.client.get(create_pseudo_folder_url)
        self.assertTemplateUsed(res,
                                'project/containers/create_pseudo_folder.html')

        formData = {'method': forms.CreatePseudoFolder.__name__,
                    'container_name': container.name,
                    'name': obj.name}
        res = self.client.post(create_pseudo_folder_url, formData)

        index_url = reverse('horizon:project:containers:index',
                            args=[tables.wrap_delimiter(container.name)])

        self.assertRedirectsNoFollow(res, index_url)

    @test.create_stubs({api.swift: ('swift_delete_object',)})
    def test_delete(self):
        container = self.containers.first()
        obj = self.objects.first()
        args = (utils_http.urlquote(tables.wrap_delimiter(container.name)),)
        index_url = reverse('horizon:project:containers:index', args=args)
        api.swift.swift_delete_object(IsA(http.HttpRequest),
                                      container.name,
                                      obj.name)
        self.mox.ReplayAll()

        action_string = "objects__delete_object__%s" % obj.name
        form_data = {"action": action_string}
        req = self.factory.post(index_url, form_data)
        kwargs = {"container_name": container.name}
        table = tables.ObjectsTable(req, self.objects.list(), **kwargs)
        handled = table.maybe_handle()
        self.assertEqual(handled['location'], index_url)

    @test.create_stubs({api.swift: ('swift_delete_object',)})
    def test_delete_pseudo_folder(self):
        container = self.containers.first()
        folder = self.folder.first()
        args = (utils_http.urlquote(tables.wrap_delimiter(container.name)),)
        index_url = reverse('horizon:project:containers:index', args=args)
        api.swift.swift_delete_object(IsA(http.HttpRequest),
                                      container.name,
                                      folder.name + '/')
        self.mox.ReplayAll()

        action_string = "objects__delete_object__%s/%s" % (container.name,
                                                           folder.name)
        form_data = {"action": action_string}
        req = self.factory.post(index_url, form_data)
        kwargs = {"container_name": container.name}
        table = tables.ObjectsTable(req, self.folder.list(), **kwargs)
        handled = table.maybe_handle()
        self.assertEqual(handled['location'], index_url)

    @test.create_stubs({api.swift: ('swift_get_object',)})
    def test_download(self):
        for container in self.containers.list():
            for obj in self.objects.list():
                self.mox.ResetAll()  # mandatory in a for loop
                api.swift.swift_get_object(IsA(http.HttpRequest),
                                           container.name,
                                           obj.name).AndReturn(obj)
                self.mox.ReplayAll()

                download_url = reverse(
                    'horizon:project:containers:object_download',
                    args=[container.name, obj.name])
                res = self.client.get(download_url)
                self.assertEqual(res.content, obj.data)
                self.assertTrue(res.has_header('Content-Disposition'))
                # Check that the returned Content-Disposition filename is well
                # surrounded by double quotes and with commas removed
                expected_name = '"%s"' % obj.name.replace(
                    ',', '').encode('utf-8')
                self.assertEqual(
                    res.get('Content-Disposition'),
                    'attachment; filename=%s' % expected_name
                )

    @test.create_stubs({api.swift: ('swift_get_containers',)})
    def test_copy_index(self):
        ret = (self.containers.list(), False)
        api.swift.swift_get_containers(IsA(http.HttpRequest)).AndReturn(ret)
        self.mox.ReplayAll()

        res = self.client.get(reverse('horizon:project:containers:object_copy',
                                      args=[self.containers.first().name,
                                            self.objects.first().name]))
        self.assertTemplateUsed(res, 'project/containers/copy.html')

    @test.create_stubs({api.swift: ('swift_get_containers',
                                    'swift_copy_object')})
    def test_copy(self):
        container_1 = self.containers.get(name=CONTAINER_NAME_1)
        container_2 = self.containers.get(name=CONTAINER_NAME_2)
        obj = self.objects.first()

        ret = (self.containers.list(), False)
        api.swift.swift_get_containers(IsA(http.HttpRequest)).AndReturn(ret)
        api.swift.swift_copy_object(IsA(http.HttpRequest),
                                    container_1.name,
                                    obj.name,
                                    container_2.name,
                                    obj.name)
        self.mox.ReplayAll()

        formData = {'method': forms.CopyObject.__name__,
                    'new_container_name': container_2.name,
                    'new_object_name': obj.name,
                    'orig_container_name': container_1.name,
                    'orig_object_name': obj.name}
        copy_url = reverse('horizon:project:containers:object_copy',
                           args=[container_1.name, obj.name])
        res = self.client.post(copy_url, formData)
        args = (utils_http.urlquote(tables.wrap_delimiter(container_2.name)),)
        index_url = reverse('horizon:project:containers:index', args=args)
        self.assertRedirectsNoFollow(res, index_url)

    @test.create_stubs({api.swift: ('swift_upload_object',)})
    def test_update_with_file(self):
        container = self.containers.first()
        obj = self.objects.first()
        OBJECT_DATA = 'objectData'

        temp_file = tempfile.TemporaryFile()
        temp_file.write(OBJECT_DATA)
        temp_file.flush()
        temp_file.seek(0)

        api.swift.swift_upload_object(IsA(http.HttpRequest),
                                      container.name,
                                      obj.name,
                                      IsA(InMemoryUploadedFile)).AndReturn(obj)
        self.mox.ReplayAll()

        update_url = reverse('horizon:project:containers:object_update',
                             args=[container.name, obj.name])

        res = self.client.get(update_url)
        self.assertTemplateUsed(res, 'project/containers/update.html')

        res = self.client.get(update_url)
        self.assertContains(res, 'enctype="multipart/form-data"')

        formData = {'method': forms.UpdateObject.__name__,
                    'container_name': container.name,
                    'name': obj.name,
                    'object_file': temp_file}
        res = self.client.post(update_url, formData)

        args = (utils_http.urlquote(tables.wrap_delimiter(container.name)),)
        index_url = reverse('horizon:project:containers:index', args=args)
        self.assertRedirectsNoFollow(res, index_url)

    @test.create_stubs({api.swift: ('swift_upload_object',)})
    def test_update_without_file(self):
        container = self.containers.first()
        obj = self.objects.first()

        self.mox.ReplayAll()

        update_url = reverse('horizon:project:containers:object_update',
                             args=[container.name, obj.name])

        res = self.client.get(update_url)
        self.assertTemplateUsed(res, 'project/containers/update.html')

        res = self.client.get(update_url)
        self.assertContains(res, 'enctype="multipart/form-data"')

        formData = {'method': forms.UpdateObject.__name__,
                    'container_name': container.name,
                    'name': obj.name}
        res = self.client.post(update_url, formData)

        args = (utils_http.urlquote(tables.wrap_delimiter(container.name)),)
        index_url = reverse('horizon:project:containers:index', args=args)
        self.assertRedirectsNoFollow(res, index_url)

    @test.create_stubs({api.swift: ('swift_get_container', )})
    def test_view_container(self):
        for container in self.containers.list():
            self.mox.ResetAll()  # mandatory in a for loop
            api.swift.swift_get_container(IsA(http.HttpRequest),
                                          container.name,
                                          with_data=False) \
                .AndReturn(container)
            self.mox.ReplayAll()

            view_url = reverse('horizon:project:containers:container_detail',
                               args=[container.name])
            res = self.client.get(view_url)

            self.assertTemplateUsed(res,
                                    'project/containers/container_detail.html')
            self.assertContains(res, container.name, 1, 200)

    @test.create_stubs({api.swift: ('swift_get_object', )})
    def test_view_object(self):
        for container in self.containers.list():
            for obj in self.objects.list():
                self.mox.ResetAll()  # mandatory in a for loop
                api.swift.swift_get_object(IsA(http.HttpRequest),
                                           container.name,
                                           obj.name,
                                           with_data=False) \
                    .AndReturn(obj)
                self.mox.ReplayAll()
                view_url = reverse('horizon:project:containers:object_detail',
                                   args=[container.name, obj.name])
                res = self.client.get(view_url)

                self.assertTemplateUsed(
                    res, 'project/containers/object_detail.html')
                self.assertContains(res, obj.name, 1, 200)

    def test_wrap_delimiter(self):
        expected = {
            'containerA': 'containerA/',
            'containerB%': 'containerB%/',  # no urlquote() should occur
            'containerC/': 'containerC/',   # already wrapped name
            'containerD/objectA': 'containerD/objectA/'
        }
        for name, expected_name in expected.items():
            self.assertEqual(tables.wrap_delimiter(name), expected_name)

    def test_for_url(self):
        expected = {
            'containerA': 'containerA/',
            'containerB%': 'containerB%25/',  # urlquote() must be called
            'containerC%/': 'containerC%25/',
            'containerD%/objectA%': 'containerD%25/objectA%25/'
        }
        for name, expected_name in expected.items():
            self.assertEqual(views.for_url(name), expected_name)
