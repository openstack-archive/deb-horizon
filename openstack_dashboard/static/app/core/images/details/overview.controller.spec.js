/**
 * (c) Copyright 2016 Hewlett-Packard Development Company, L.P.
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

  describe('image overview controller', function() {
    var ctrl;
    var glance = {
      getNamespaces: angular.noop
    };

    beforeEach(module('horizon.app.core.images'));
    beforeEach(module('horizon.framework.conf'));
    beforeEach(inject(function($controller, $q) {
      var deferred = $q.defer();
      deferred.resolve({data: {properties: {'a': 'apple'}}});
      spyOn(glance, 'getNamespaces').and.returnValue(deferred.promise);
      ctrl = $controller('ImageOverviewController',
        {
          '$scope': {context: {loadPromise: deferred.promise}}
        }
      );
    }));

    it('sets ctrl.resourceType', function() {
      expect(ctrl.resourceType).toBeDefined();
    });

    it('sets ctrl.metadata', inject(function($timeout) {
      $timeout.flush();
      expect(ctrl.image).toBeDefined();
      expect(ctrl.image.properties).toBeDefined();
    }));

  });

})();
