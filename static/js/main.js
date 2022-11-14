'use strict';

/* function dataCtrl($scope, $http, $timeout) {
 *   $scope.data = [];
 *
 *   (function tick() {
 *     $http.get('api/changingData').success(function (data) {
 *       $scope.data = data;
 *       $timeout(tick, 1000);
 *     });
 *   })();
 * };
 *  */
angular
  .module('iot-app', [])
  .controller('InterfaceController', function($scope, $http, $timeout) {
    var ifc = this;
    function polling() {
      $http.get('/board-status').then(function (response) {
        ifc.lightbulb_status = response.data.led_status === 1;
        $timeout(polling, 1000);
      });
    }

    ifc.switchLightbulb = function () {
      var cmd = ifc.lightbulb_status ? '/toggle/off' : '/toggle/on'
      $http.get(cmd).then(function (response) {
        ifc.lightbulb_status = response.data.led_status === 1;
      })
    };

    $timeout(polling, 500);

  });
