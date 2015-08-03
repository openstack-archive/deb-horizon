/*
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

  /**
   * @ngdoc controller
   * @name horizon.framework.widgets.metadata-display.controller:HzMetadataDisplayController
   * @description
   * Controller used by `hzMetadataDisplay`
   */
  angular
    .module('horizon.framework.widgets.metadata-display')
    .controller('HzMetadataDisplayController', HzMetadataDisplayController);

  HzMetadataDisplayController.$inject = [
    '$scope',
    'horizon.framework.widgets.metadata-tree.service',
    'horizon.framework.widgets.metadata-display.defaults'
  ];

  function HzMetadataDisplayController($scope, metadataTreeService, defaults) {
    var ctrl = this;

    ctrl.text = angular.extend({}, defaults.text, $scope.text);
    ctrl.tree = null;
    ctrl.selected = null;
    ctrl.hide = true;

    ctrl.onSelect = function (item) {
      ctrl.selected.collapse();
      item.expand(true);
      ctrl.selected = item;
    };

    ctrl.childrenFilter = function (item) {
      return item.visible && item.leaf && item.added;
    };

    ctrl.listFilter = function (item) {
      return item.addedCount > 0;
    };

    init();

    function init() {
      ctrl.tree = new metadataTreeService.Tree($scope.available, $scope.existing);
      angular.forEach(ctrl.tree.flatTree, function (item) {
        if (item.added) {
          if (!item.leaf) {
            item.added = false;
            if (item.parent) {
              item.parent.addedCount -= 1;
            }
          }
          else if (!item.custom) {
            ctrl.hide = false;
          }
        }

      });
      // select first item
      ctrl.tree.flatTree.some(function (item) {
        if (ctrl.listFilter(item)) {
          ctrl.selected = item;
          item.expand(true);
          return true; // break
        }
      });
    }
  }
})();
