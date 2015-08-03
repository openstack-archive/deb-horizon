/**
 * (c) Copyright 2015 Hewlett-Packard Development Company, L.P.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *    http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
(function () {
  'use strict';

  angular
    .module('horizon.app.core.images')
    .filter('imageType', imageTypeFilter);

  imageTypeFilter.$inject = [
    'horizon.framework.util.i18n.gettext'
  ];

  /**
   * @ngdoc filter
   * @name imageTypeFilter
   * @description
   * Takes a raw image object from the API and returns the user friendly type.
   */
  function imageTypeFilter(gettext) {
    return function (input) {
      if (null !== input &&
        angular.isDefined(input) &&
        angular.isDefined(input.properties) &&
        input.properties.image_type === 'snapshot') {
        return gettext('Snapshot');
      } else {
        return gettext('Image');
      }
    };
  }

}());
