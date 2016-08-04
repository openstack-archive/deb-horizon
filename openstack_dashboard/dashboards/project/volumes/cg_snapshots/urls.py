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

from django.conf.urls import url

from openstack_dashboard.dashboards.project.volumes.cg_snapshots import views

urlpatterns = [
    url(r'^(?P<cg_snapshot_id>[^/]+)/cg_snapshot_detail/$',
        views.DetailView.as_view(),
        name='cg_snapshot_detail'),
    url(r'^(?P<cg_snapshot_id>[^/]+)/create_cgroup/$',
        views.CreateCGroupView.as_view(),
        name='create_cgroup'),
]
