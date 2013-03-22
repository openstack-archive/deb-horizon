horizon.alert = function (type, message, extra_tags) {
  safe = false
  // Check if the message is tagged as safe.
  if (typeof(extra_tags) !== "undefined" && _.contains(extra_tags.split(' '), 'safe')) {
    safe = true
  }
  var template = horizon.templates.compiled_templates["#alert_message_template"],
      params = {
        "type": type,
        "type_capitalized": horizon.utils.capitalize(type),
        "message": message,
        "safe": safe
      };
  return $(template.render(params)).hide().prependTo("#main_content .messages").fadeIn(100);
};

horizon.clearErrorMessages = function() {
  $('#main_content .messages .alert.alert-error').remove();
};

horizon.clearSuccessMessages = function() {
  $('#main_content .messages .alert.alert-success').remove();
};

horizon.clearAllMessages = function() {
  horizon.clearErrorMessages();
  horizon.clearSuccessMessages();
};

horizon.autoDismissAlerts = function() {
  var $alerts = $('#main_content .messages .alert');

  $alerts.each(function(index, alert) {
    var $alert = $(this),
        types = $alert.attr('class').split(' ');

    // Check if alert should auto-fade
    if (_.intersection(types, horizon.conf.auto_fade_alerts.types).length > 0) {
      setTimeout(function() {
        $alert.fadeOut(horizon.conf.auto_fade_alerts.fade_duration);
      }, horizon.conf.auto_fade_alerts.delay);
    }
  });
}

horizon.addInitFunction(function () {
  // Bind AJAX message handling.
  $("body").ajaxComplete(function(event, request, settings){
    var message_array = $.parseJSON(horizon.ajax.get_messages(request));
    $(message_array).each(function (index, item) {
      horizon.alert(item[0], item[1], item[2]);
    });
  });

  // Dismiss alert messages when moving on to a new type of action.
  $('a.ajax-modal').click(function() {
    horizon.clearAllMessages();
  });

  // Bind dismiss(x) handlers for alert messages.
  $(".alert").alert();

  // Hide alerts automatically if attribute data-dismiss-auto is set to true.
  horizon.autoDismissAlerts();
});
