(function () {
  var hostname = window.location.hostname || '127.0.0.1';
  var protocol = window.location.protocol || 'http:';

  window.APP_CONFIG = {
    apiBaseUrl: protocol + '//' + hostname + ':8000'
  };
}());
