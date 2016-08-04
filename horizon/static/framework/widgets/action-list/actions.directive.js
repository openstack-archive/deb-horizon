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

  angular
    .module('horizon.framework.widgets.action-list')
    .directive('actions', actions);

  actions.$inject = [
    '$parse',
    'horizon.framework.widgets.action-list.actions.service'
  ];

  /**
   * @ngdoc directive
   * @name horizon.framework.widgets.action-list.directive:actions
   * @element
   * @description
   * The `actions` directive represents the actions to be displayed in a Bootstrap button
   * group, button dropdown, or bootstrap panels.
   *
   *
   * Attributes:
   *
   * @param {string} type
   * Type can be 'row', 'batch', or 'detail'. 'batch' actions are rendered as a button group,
   * 'row' actions are rendered as a button dropdown menu, 'detail' actions are rendered as
   * bootstrap panels. 'batch' actions are typically used for actions across multiple items while
   * 'row' and 'detail' actions are used per item.
   *
   * @param {string=} item
   * The item to pass to the 'service' when using 'row' or 'detail' type.
   *
   * @param {function} result-handler
   * (Optional) A function that is called with the return value from a clicked actions perform
   * function. Ideally the action perform function returns a promise that resolves to some data
   * on success, but it may return just data, or no return at all, depending on the specific action
   * implementation. It is recommended to use the actionResultService to manage the results of your
   * actions, and also to have them generate results which are more broadly usable than a custom
   * result value.
   *
   * @param {function} allowed
   * Returns an array of actions that can be performed on the item(s).
   *
   * This is an array that should contain objects with the following properties:
   * {
   *   template: <template object - described below>,
   *   service: <service to use - described below>
   * }
   *
   *   template: the Template used for the Action Button.
   *   It is an object that can be any of
   *   1. url: <full_path_to_template.html>
   *      This allows for specification of the template for the action button.
   *      Use this option for complete extensibility and control over what is rendered.
   *      The directive will be responsible for binding the callback but not for styling the button.
   *      The template should include the 'item' attribute for the 'action' button,
   *      if the action needs an item to act upon even for 'row' type. Specifying an 'item' other
   *      than the current row 'item' is supported'.
   *
   *      The 'scope' in use for the 'actions' directive can be used in the custom template.
   *
   *      Refer to tests that exercise this functionality with some sample templates at
   *      - 'actions.custom.mock.html' and 'actions.custom.mock2.html'.
   *
   *   2. type: '<action_button_type>'
   *      This creates an action button based off a 'known' button type.
   *      Currently supported values are
   *      1. 'delete' - Delete a single row. Only for 'row' or 'detail' type.
   *      2. 'danger' - For marking an Action as dangerous. Only for 'row' or 'detail' type.
   *      3. 'delete-selected' - Delete multiple rows. Only for 'batch' type.
   *      4. 'create' - Create a new entity. Only for 'batch' type.
   *
   *      The styling of the action button is done based on the 'listType'.
   *      The directive will be responsible for binding the correct callback.
   *
   *   3. text: 'text', actionClasses: 'custom-classes'
   *      This creates an unstyled button with the given text.
   *      For custom styling of the button, `actionClasses` can be optionally included.
   *      The directive will be responsible for binding the correct callback.
   *
   *   4. title: 'title', description: 'description'
   *      A title and description must be provided for the 'detail' type. These are used as
   *      the title and description to display in the bootstrap panel.
   *
   *   service: is the service expected to have two functions
   *   1. allowed: is expected to return a promise that resolves
   *      if the action is permitted and is rejected if not. If there are multiple promises that
   *      need to be resolved, you can $q.all to combine multiple promises into a single promise.
   *      When using 'row' or 'detail' type, the current 'item' will be passed to the function.
   *      When using 'batch' type, no arguments are provided.
   *   2. perform: is what gets called when the button is clicked. Also expected to return a
   *      promise that resolves when the action completes.
   *      When using 'row' or 'detail' type, the current 'item' is evaluated and passed to the
   *      function.
   *      When using 'batch' type, 'item' is not passed.
   *      When using 'delete-selected' for 'batch' type, all selected rows are passed.
   *   3. initScope: actions may perform post-config (in the angular sense) initialization by
   *      providing an initScope method. This might be typically invoked by initActions()
   *      on a ResourceType. Actions should not perform blocking operations in their
   *      construction, for example API calls, because as injectables their constructor
   *      is run during injection, meaning those calls would be executed as the module
   *      is initialized.  This would mean those calls would be blocking on any
   *      Angular context initialization, such as going to the login page.
   *
   * @restrict E
   * @scope
   * @example
   *
   * batch:
   *
   * Create the services that will implement the actions.
   * Each service must have an allowed function and a perform function.
   *
   * var batchDeleteService = {
   *   allowed: function() {
   *     return policy.ifAllowed({ rules: [['image', 'delete_image']] });
   *   },
   *   perform: function(images) {
   *     return $q.all(images.map(function(image){
   *       return glanceAPI.deleteImage(image.id);
   *     }));
   *   }
   * };
   *
   * In the following example we also send off an async check that the image
   * service is enabled, the resultant promise being checked in the allowed
   * function. This saves us checking that enabled flag every time allowed
   * is executed.
   *
   * var createService = {
   *   allowed: function(image) {
   *     return $q.all(
   *       isActive(image),
   *       imageServiceEnabledPromise
   *     );
   *   },
   *   perform: function() {
   *     //open the modal to create volume and return the modal's result promise
   *   },
   *   initScope: function() {
   *     imageServiceEnabledPromise = serviceCatalog.ifTypeEnabled('image');
   *   }
   * };
   *
   * Then create the Service to use in the HTML which lists
   * all allowed actions with the templates to use.
   *
   * function actions() {
   *   return [{
   *     template: {
   *       type: 'delete-selected',
   *       text: gettext('Delete Images')
   *     },
   *     service: batchDeleteService
   *     }, {
   *     template: {
   *       type: 'create',
   *       text: gettext('Create Image')
   *     },
   *     service: createService
   *   }];
   * }
   *
   * Finally, in your HTML, reference the "actions" function and pass
   * in the list of actions that will be allowed.
   *
   * ```
   * <actions allowed="actions" type="batch" result-handler="onResult">
   * </actions>
   * ```
   *
   * row:
   *
   * Create the services that will implement the actions.
   * Each service must have an allowed function and a perform function.
   *
   * var deleteService = {
   *   allowed: function(image) {
   *     return $q.all([
   *       notProtected(image),
   *       policy.ifAllowed({ rules: [['image', 'delete_image']] }),
   *       ownedByUser(image),
   *       notDeleted(image)
   *     ]);
   *   },
   *   perform: function(image) {
   *     return glanceAPI.deleteImage(image.id);
   *   }
   * };
   *
   * var createVolumeService = {
   *   allowed: function(image) {
   *     return createVolumeFromImagePermitted(image);
   *   },
   *   perform: function(image) {
   *     //open the modal to create volume and return the modal's result promise
   *   }
   * };
   *
   * var downloadService = {
   *   allowed: function(image) {
   *     return isPublic(image);
   *   },
   *   perform: function(image) {
   *     return generateUrlFor(image);
   *   }
   * };
   *
   * Then create the Service to use in the HTML which lists
   * all allowed actions with the templates to use.
   *
   * function actions(image) {
   *   return [{
   *     template: {
   *       text: gettext('Delete Image'),
   *       type: 'delete'
   *     },
   *     service: deleteService
   *   }, {
   *     template: {
   *       text: gettext('Create Volume')
   *     },
   *     service: createVolumeService
   *   }];
   * }
   *
   * Finally, in your HTML, reference the "actions" function and pass
   * in the list of actions that will be allowed.
   *
   * ```
   * <actions allowed="actions" type="row" item="image" result-handler="onResult">
   * </actions>
   *
   * ```
   *
   * detail:
   *
   * The 'detail' type actions are identical to the 'row' type actions except that the template
   * property for each action should have a title and description property.
   */
  function actions(
    $parse,
    actionsService
  ) {
    var directive = {
      link: link,
      restrict: 'E',
      scope: true,
      controller: 'horizon.framework.widgets.action-list.ActionsController as actionsCtrl'
    };

    return directive;

    function link(scope, element, attrs, actionsController) {
      var listType = attrs.type;
      var item = attrs.item;
      var allowedActions;
      var resultHandler = $parse(attrs.resultHandler)(scope);
      var actionsParam = $parse(attrs.allowed)(scope);
      if (angular.isFunction(actionsParam)) {
        allowedActions = actionsParam();
      } else {
        allowedActions = actionsParam;
      }

      var service = actionsService({
        scope: scope,
        element: element,
        ctrl: actionsController,
        listType: listType,
        item: item,
        resultHandler: resultHandler
      });

      service.renderActions(allowedActions);
    }
  }
})();
