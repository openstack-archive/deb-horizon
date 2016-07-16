/**
 * (c) Copyright 2015 Hewlett-Packard Development Company, L.P.
 *
 * Licensed under the Apache License, Version 2.0 (the "License"); you may
 * not use this file except in compliance with the License. You may obtain
 * a copy of the License at
 *
 *    http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
 * WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
 * License for the specific language governing permissions and limitations
 * under the License.
 */

(function() {
  'use strict';

  /**
   * @ngdoc overview
   * @ngname horizon.app.core.images
   *
   * @description
   * Provides all of the services and widgets required
   * to support and display images related content.
   */
  angular
    .module('horizon.app.core.images', [
      'ngRoute',
      'horizon.app.core.images.actions',
      'horizon.app.core.images.details'
    ])
    .constant('horizon.app.core.images.events', events())
    .constant('horizon.app.core.images.non_bootable_image_types', ['aki', 'ari'])
    .constant('horizon.app.core.images.validationRules', validationRules())
    .constant('horizon.app.core.images.imageFormats', imageFormats())
    .constant('horizon.app.core.images.resourceType', 'OS::Glance::Image')
    .run(run)
    .config(config);

  run.$inject = [
    'horizon.framework.conf.resource-type-registry.service',
    'horizon.app.core.openstack-service-api.glance',
    'horizon.app.core.images.basePath',
    'horizon.app.core.images.resourceType'
  ];

  function run(registry, glance, basePath, imageResourceType) {
    registry.getResourceType(imageResourceType)
      .setNames(gettext('Image'), gettext('Images'))
      .setSummaryTemplateUrl(basePath + 'details/drawer.html')
      .setProperty('checksum', {
        label: gettext('Checksum')
      })
      .setProperty('container_format', {
        label: gettext('Container Format')
      })
      .setProperty('created_at', {
        label: gettext('Created At')
      })
      .setProperty('disk_format', {
        label: gettext('Disk Format')
      })
      .setProperty('id', {
        label: gettext('ID')
      })
      .setProperty('type', {
        label: gettext('Type')
      })
      .setProperty('members', {
        label: gettext('Members')
      })
      .setProperty('min_disk', {
        label: gettext('Min. Disk')
      })
      .setProperty('min_ram', {
        label: gettext('Min. RAM')
      })
      .setProperty('name', {
        label: gettext('Name')
      })
      .setProperty('owner', {
        label: gettext('Owner')
      })
      .setProperty('protected', {
        label: gettext('Protected')
      })
      .setProperty('size', {
        label: gettext('Size')
      })
      .setProperty('status', {
        label: gettext('Status')
      })
      .setProperty('tags', {
        label: gettext('Tags')
      })
      .setProperty('updated_at', {
        label: gettext('Updated At')
      })
      .setProperty('virtual_size', {
        label: gettext('Virtual Size')
      })
      .setProperty('visibility', {
        label: gettext('Visibility')
      })
      .setProperty('description', {
        label: gettext('Description')
      })
      .setProperty('architecture', {
        label: gettext('Architecture')
      })
      .setProperty('kernel_id', {
        label: gettext('Kernel ID')
      })
      .setProperty('ramdisk_id', {
        label: gettext('Ramdisk ID')
      })
      .setListFunction(listFunction)
      .tableColumns
      .append({
        id: 'name',
        priority: 1,
        sortDefault: true,
        urlFunction: urlFunction
      })
      .append({
        id: 'type',
        priority: 1,
        filters: ['imageType']
      })
      .append({
        id: 'status',
        priority: 1,
        filters: ['imageStatus']
      })
      .append({
        id: 'protected',
        priority: 1,
        filters: ['yesno']
      })
      .append({
        id: 'disk_format',
        priority: 2,
        filters: ['noValue', 'uppercase']
      })
      .append({
        id: 'size',
        priority: 2,
        filters: ['bytes']
      });

    registry.getResourceType(imageResourceType).filterFacets
      .append({
        label: gettext('Name'),
        name: 'name',
        isServer: true,
        singleton: true,
        persistent: true
      })
      .append({
        label: gettext('Status'),
        name: 'status',
        isServer: true,
        singleton: true,
        options: [
          {label: gettext('Active'), key: 'active'},
          {label: gettext('Saving'), key: 'saving'},
          {label: gettext('Queued'), key: 'queued'},
          {label: gettext('Pending Delete'), key: 'pending_delete'},
          {label: gettext('Killed'), key: 'killed'},
          {label: gettext('Deactivated'), key: 'deactivated'},
          {label: gettext('Deleted'), key: 'deleted'}
        ]
      })
      .append({
        label: gettext('Protected'),
        name: 'protected',
        isServer: true,
        singleton: true,
        options: [
          {label: gettext('Yes'), key: 'true'},
          {label: gettext('No'), key: 'false'}
        ]
      })
      .append({
        label: gettext('Format'),
        name: 'disk_format',
        isServer: true,
        singleton: true,
        options: [
          {label: gettext('AKI'), key: 'aki'},
          {label: gettext('AMI'), key: 'ami'},
          {label: gettext('ARI'), key: 'ari'},
          {label: gettext('Docker'), key: 'docker'},
          {label: gettext('ISO'), key: 'iso'},
          {label: gettext('OVA'), key: 'ova'},
          {label: gettext('QCOW2'), key: 'qcow2'},
          {label: gettext('Raw'), key: 'raw'},
          {label: gettext('VDI'), key: 'vdi'},
          {label: gettext('VHD'), key: 'vhd'},
          {label: gettext('VMDK'), key: 'vmdk'}
        ]
      })
      .append({
        label: gettext('Min. Size (bytes)'),
        name: 'size_min',
        isServer: true,
        singleton: true
      })
      .append({
        label: gettext('Max. Size (bytes)'),
        name: 'size_max',
        isServer: true,
        singleton: true
      });

    function listFunction(params) {
      return glance.getImages(params).then(modifyResponse);

      function modifyResponse(response) {
        return {data: {items: response.data.items.map(addTrackBy)}};

        function addTrackBy(image) {
          image.trackBy = image.id + image.updated_at;
          return image;
        }
      }
    }

    function urlFunction(item) {
      return 'project/ngdetails/OS::Glance::Image/' + item.id;
    }
  }

  /**
   * @ngdoc constant
   * @name horizon.app.core.images.validationRules
   * @description constants for use in validation fields
   */
  function validationRules() {
    return {
      integer: /^[0-9]+$/,
      fieldMaxLength: 255
    };
  }

  /**
   * @ngdoc constant
   * @name horizon.app.core.images.imageFormats
   * @description constants for list of image types in dropdowns
   */
  function imageFormats() {
    return {
      iso: gettext('ISO - Optical Disk Image'),
      ova: gettext('OVA - Open Virtual Appliance'),
      qcow2: gettext('QCOW2 - QEMU Emulator'),
      raw: gettext('Raw'),
      vdi: gettext('VDI - Virtual Disk Image'),
      vhd: gettext('VHD - Virtual Hard Disk'),
      vmdk: gettext('VMDK - Virtual Machine Disk'),
      aki: gettext('AKI - Amazon Kernel Image'),
      ami: gettext('AMI - Amazon Machine Image'),
      ari: gettext('ARI - Amazon Ramdisk Image'),
      docker: gettext('Docker')
    };
  }

  /**
   * @ngdoc value
   * @name horizon.app.core.images.events
   * @description a list of events for images
   * @returns {Object} The event object
   */
  function events() {
    return {
      VOLUME_CHANGED: 'horizon.app.core.images.VOLUME_CHANGED',
      IMAGE_CHANGED: 'horizon.app.core.images.IMAGE_CHANGED',
      IMAGE_METADATA_CHANGED: 'horizon.app.core.images.IMAGE_METADATA_CHANGED'
    };
  }

  config.$inject = [
    '$provide',
    '$windowProvider',
    '$routeProvider'
  ];

  /**
   * @name config
   * @param {Object} $provide
   * @param {Object} $windowProvider
   * @param {Object} $routeProvider
   * @description Routes used by this module.
   * @returns {undefined} Returns nothing
   */
  function config($provide, $windowProvider, $routeProvider) {
    var path = $windowProvider.$get().STATIC_URL + 'app/core/images/';
    $provide.constant('horizon.app.core.images.basePath', path);

    $routeProvider.when('/project/ngimages/', {
      templateUrl: path + 'panel.html'
    });
  }

})();
