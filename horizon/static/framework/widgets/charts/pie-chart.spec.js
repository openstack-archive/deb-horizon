/*
 *    (c) Copyright 2015 Hewlett-Packard Development Company, L.P.
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

  describe('horizon.framework.widgets.charts module', function () {
    it('should be defined', function () {
      expect(angular.module('horizon.framework.widgets.charts')).toBeDefined();
    });
  });

  describe('pie chart directive', function () {

    var $scope, $elementMax, $elementTotal, $elementOverMax,
        donutChartSettings, quotaChartDefaults;

    beforeEach(module('templates'));
    beforeEach(module('horizon.framework'));
    beforeEach(module('horizon.framework.widgets'));
    beforeEach(module('horizon.framework.widgets.charts'));

    beforeEach(inject(function ($injector) {
      var $compile = $injector.get('$compile');
      $scope = $injector.get('$rootScope').$new();
      donutChartSettings = $injector.get('horizon.framework.widgets.charts.donutChartSettings');
      quotaChartDefaults = $injector.get('horizon.framework.widgets.charts.quotaChartDefaults');

      $scope.testDataTotal = {
        title: 'Total Instances',
        label: '25%',
        data: [
          { label: quotaChartDefaults.usageLabel,
            value: 1,
            colorClass: quotaChartDefaults.usageColorClass },
          { label: quotaChartDefaults.addedLabel,
            value: 1,
            colorClass: quotaChartDefaults.addedColorClass },
          { label: quotaChartDefaults.remainingLabel,
            value: 6,
            colorClass: quotaChartDefaults.remainingColorClass,
            hideKey: true }
        ]
      };

      $scope.testDataMax = {};
      $scope.testDataOverMax = {};
      // Max chart is similar to Total chart data structure
      // but has an additional 'maxLimit' property
      angular.copy($scope.testDataTotal, $scope.testDataMax);
      $scope.testDataMax.maxLimit = 8;
      // using the Max chart, assign values to test for overMax
      angular.copy($scope.testDataMax, $scope.testDataOverMax);
      $scope.testDataOverMax.data[0].value = 6;
      $scope.testDataOverMax.data[1].value = 3;
      $scope.testDataOverMax.data[2].value = 0;
      $scope.testDataOverMax.overMax = true;

      $scope.chartSettings = {
        innerRadius: 24,
        outerRadius: 30,
        titleClass: 'pie-chart-title-medium',
        showTitle: true,
        showLabel: true,
        showLegend: true,
        tooltipIcon: 'fa-square'
      };

      // Max/quota chart markup
      var markupMax = '<pie-chart chart-data="testDataMax"' +
                      '  chart-settings="chartSettings">' +
                      '</pie-chart>';
      $elementMax = angular.element(markupMax);
      $compile($elementMax)($scope);

      // Over Max/quota chart markup
      var markupOverMax = '<pie-chart chart-data="testDataOverMax"' +
                          '  chart-settings="chartSettings">' +
                          '</pie-chart>';
      $elementOverMax = angular.element(markupOverMax);
      $compile($elementOverMax)($scope);

      // Total chart markup
      var markupTotal = '<pie-chart chart-data="testDataTotal" ' +
                        '  chart-settings="chartSettings">' +
                        '</pie-chart>';
      $elementTotal = angular.element(markupTotal);
      $compile($elementTotal)($scope);

      $scope.$apply();
    }));

    it('Max chart should be compiled', function () {
      expect($elementMax.html().trim()).not.toBe('');
    });

    it('OverMax chart should be compiled', function () {
      expect($elementOverMax.html().trim()).not.toBe('');
    });

    it('Total chart should be compiled', function () {
      expect($elementTotal.html().trim()).not.toBe('');
    });

    it('Max chart should have svg element', function () {
      expect($elementMax.find('svg')).toBeDefined();
    });

    it('OverMax chart should have svg element', function () {
      expect($elementOverMax.find('svg')).toBeDefined();
    });

    it('Total chart should have svg element', function () {
      expect($elementTotal.find('svg')).toBeDefined();
    });

    it('Max chart should have 3 path elements', function () {
      expect($elementMax.find('path.slice').length).toBe(3);
    });

    it('OverMax chart should have 3 path elements', function () {
      expect($elementOverMax.find('path.slice').length).toBe(3);
    });

    it('Total chart should have 3 path elements', function () {
      expect($elementTotal.find('path.slice').length).toBe(3);
    });

    it('Max chart should have correct css classes for slices', function () {
      var slices = $elementMax.find('path.slice');
      expect(angular.element(slices[0]).attr('class')).toBe('slice usage');
      expect(angular.element(slices[1]).attr('class')).toBe('slice added');
      expect(angular.element(slices[2]).attr('class')).toBe('slice remaining');
    });

    it('OverMax chart should have correct css classes for slices', function () {
      var slices = $elementOverMax.find('path.slice');
      expect(angular.element(slices[0]).attr('class')).toBe('slice usage');
      expect(angular.element(slices[1]).attr('class')).toBe('slice added');
      expect(angular.element(slices[2]).attr('class')).toBe('slice remaining');
    });

    it('Total chart should have correct css classes for slices', function () {
      var slices = $elementTotal.find('path.slice');
      expect(angular.element(slices[0]).attr('class')).toBe('slice usage');
      expect(angular.element(slices[1]).attr('class')).toBe('slice added');
      expect(angular.element(slices[2]).attr('class')).toBe('slice remaining');
    });

    it('Max chart should have title "Total Instances (8 Max)"', function () {
      var title = $elementMax.find('.pie-chart-title').text().trim();
      expect(title).toBe('Total Instances (8 Max)');
    });

    it('OverMax chart should have title "Total Instances (8 Max)"', function () {
      var title = $elementOverMax.find('.pie-chart-title').text().trim();
      expect(title).toBe('Total Instances (8 Max)');
    });

    it('Total chart should have title "Total Instances (8 Total)"', function () {
      var title = $elementTotal.find('.pie-chart-title').text().trim();
      expect(title).toBe('Total Instances (8 Total)');
    });

    it('Max chart should have a legend', function () {
      expect($elementMax.find('.pie-chart-legend')).toBeDefined();
    });

    it('OverMax chart should have a legend', function () {
      expect($elementOverMax.find('.pie-chart-legend')).toBeDefined();
    });

    it('Total chart should have a legend', function () {
      expect($elementTotal.find('.pie-chart-legend')).toBeDefined();
    });

    it ('Max chart should have correct legend keys and labels', function () {
      var legendKeys = $elementMax.find('.pie-chart-legend .slice-legend');

      var firstKeyLabel = legendKeys[0];
      var secondKeyLabel = legendKeys[1];

      expect(firstKeyLabel.textContent.trim()).toBe('1 Current Usage');
      expect(secondKeyLabel.textContent.trim()).toBe('1 Added');
    });

    it ('OverMax chart should have correct legend keys and labels', function () {
      var legendKeys = $elementOverMax.find('.pie-chart-legend .slice-legend');

      var firstKeyLabel = legendKeys[0];
      var secondKeyLabel = legendKeys[1];

      expect(firstKeyLabel.textContent.trim()).toBe('6 Current Usage');
      expect(secondKeyLabel.textContent.trim()).toBe('3 Added');
    });

    it ('OverMax chart should have "danger" class', function () {
      var pieChart = $elementOverMax.find('svg').parent();
      expect(pieChart.hasClass('danger')).toBe(true);
    });

    it ('Total chart should have correct legend keys and labels', function () {
      var legendKeys = $elementTotal.find('.pie-chart-legend .slice-legend');

      var firstKeyLabel = legendKeys[0];
      var secondKeyLabel = legendKeys[1];

      expect(firstKeyLabel.textContent.trim()).toBe('1 Current Usage');
      expect(secondKeyLabel.textContent.trim()).toBe('1 Added');
    });
  });

})();
