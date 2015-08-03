(function() {
  'use strict';

  describe('search bar directive', function() {

    var $scope, $element;

    beforeEach(module('templates'));
    beforeEach(module('smart-table'));
    beforeEach(module('horizon.framework.widgets'));
    beforeEach(module('horizon.framework.widgets.table'));

    describe('search bar', function() {

      beforeEach(inject(function($injector) {
        var $compile = $injector.get('$compile');
        $scope = $injector.get('$rootScope').$new();

        $scope.rows = [];

        var markup = '<table st-table="rows">' +
                     '<thead>' +
                     ' <tr>' +
                     '   <th>' +
                     '     <hz-search-bar group-classes="input-group-sm" ' +
                     '       icon-classes="fa-search">' +
                     '     </hz-search-bar>' +
                     '   </th>' +
                     ' </tr>' +
                     '</thead>' +
                     '<tbody></tbody>' +
                     '</table>';

        $element = angular.element(markup);
        $compile($element)($scope);

        $scope.$digest();
      }));

      it('should have a text field', function() {
        expect($element.find('input[st-search]').length).toBe(1);
      });

      it('should have a search icon', function() {
        expect($element.find('.input-group-addon .fa-search').length).toBe(1);
      });

      it('should have a "input-group-sm" class on input group', function() {
        expect($element.find('.input-group.input-group-sm').length).toBe(1);
      });

      it('should have default placeholder text set to "Filter"', function() {
        expect($element.find('input[st-search]').attr('placeholder')).toEqual('Filter');
      });

    });

  });

})();
