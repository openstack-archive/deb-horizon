(function() {
  'use strict';

  /**
   * @ngdoc service
   * @name simpleModalService
   *
   * @description
   * Horizon's wrapper for angular-bootstrap modal service.
   * It should only be use for small confirmation dialogs.
   * @param {object} the object containing title, body, submit, and cancel labels
   * @param {object} the object returned from angular-bootstrap $modal
   *
   * @example:
   *  angular
   *    .controller('modalExampleCtrl', ExampleCtrl);
   *
   *  ExampleCtrl.$inject = [
   *    '$scope',
   *    'horizon.framework.widgets.modal.simple-modal.service'
   *  ];
   *
   *  function ExampleCtrl($scope, simpleModalService) {
   *    var options = {
   *      title: 'Confirm Delete',
   *      body: 'Are you sure you want to delete this item?',
   *      submit: 'Yes',
   *      cancel: 'No'
   *    };
   *
   *    simpleModalService(options).result.then(function() {
   *      // user clicked on submit button
   *      // do something useful here
   *    });
   *  });
   */
  angular
    .module('horizon.framework.widgets.modal')
    .factory('horizon.framework.widgets.modal.simple-modal.service', modalService);

  modalService.$inject = [
    '$modal',
    'horizon.framework.widgets.basePath',
    'horizon.framework.util.i18n.gettext'
  ];

  function modalService($modal, path, gettext) {
    var service = {
      modal: modal
    };
    return service;

    ////////////////////

    function modal(params) {
      if (params && params.title && params.body) {
        var options = {
          controller: 'SimpleModalController as modalCtrl',
          templateUrl: path + 'modal/simple-modal.html',
          resolve: {
            context: function() {
              return {
                title: params.title,
                body: params.body,
                submit: params.submit || gettext('Submit'),
                cancel: params.cancel || gettext('Cancel')
              };
            }
          }
        };
        return $modal.open(options);
      }
    } // end of modalOptions function
  } // end of modalService function
})();
