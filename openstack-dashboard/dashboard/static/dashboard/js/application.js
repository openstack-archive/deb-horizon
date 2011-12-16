(function($, window, document, undefined) {
  $.fn.columnar = function (target, opt) {
    var options = $.extend({
      trigger: 'change',
      retrieve: 'name',
      container: $('table.sortable'),
      selector: '.',
      selected_class: 'hidden'
    }, opt);

    $(this).bind(options.trigger, function(e) {
      options.container.find( options.selector + $(this).attr(options.retrieve) ).toggleClass(options.selected_class)
    })
  }
}(jQuery, this, document));


$(function(){
  $(document).on('click', '.modal:not(.static_page) .cancel', function (evt) {
    $(this).closest('.modal').remove();
    return false;
  });

  $('.ajax-modal').click(function (evt) {
    var $this = $(this);
    $.ajax($this.attr('href'), {
      complete: function (jqXHR, status) {
        $('body').append(jqXHR.responseText);
        $('body .modal:last').modal({'show':true, 'backdrop': true, 'keyboard': true});
      }
    });
    return false;
  });

  $('.table_search input').quicksearch('tr.odd, tr.even', {
    'delay': 300,
    'loader': 'span.loading',
    'bind': 'keyup click',
    'show': function () {
      this.style.color = '';
    },
    'hide': function () {
      this.style.display = 'none';
    },
    'prepareQuery': function (val) {
      return new RegExp(val, "i");
    },
    'testQuery': function (query, txt, _row) {
      return query.test($(_row).find('td:not(.hidden)').text());
    }
  });

  $('table.sortable').tablesorter();

  // show+hide image details
  $(".details").hide()
  $("#images td:not(#actions)").click(function(e){
    $(this).parent().nextUntil(".even, .odd").fadeToggle("slow");
  })

  $(".drop_btn").click(function(){
    $(this).parent().children('.item_list').toggle();
    return false;
  })


  // confirmation on deletion of items
  $(".terminate").click(function(e){
    var response = confirm('Are you sure you want to terminate the Instance: '+$(this).attr('title')+"?");
    return response;
  })

  $(".delete").click(function(e){
    var response = confirm('Are you sure you want to delete the '+$(this).attr('title')+" ?");
    return response;
  })

  $(".reboot").click(function(e){
    var response = confirm('Are you sure you want to reboot the '+$(this).attr('title')+" ?");
    return response;
  })

  $(".disable").click(function(e){
    var response = confirm('Are you sure you want to disable the '+$(this).attr('title')+" ?");
    return response;
  })

  $(".enable").click(function(e){
    var response = confirm('Are you sure you want to enable the '+$(this).attr('title')+" ?");
    return response;
  })

  // disable multiple submissions when launching a form
  $("form").submit(function() {
      $(this).submit(function() {
          return false;
      });
      $('input:submit').removeClass('primary').addClass('disabled');
      $('input:submit').attr('disabled', 'disabled');
      return true;
  });

  // Fancy multi-selects
  $(".chzn-select").chosen()

  $(".detach").click(function(e){
    var response = confirm('Are you sure you want to detach the '+$(this).attr('title')+" ?");
    return response;
  })

  // Actions button dropdown behavior
  $('a.more-actions').mouseenter(function() {
    $(this).addClass('active')
    $('td.actions ul').each(function(){
      // If another dropdown is open, close it.
      if ($(this).hasClass('active')) {
        $(this).removeClass('active')
        $(this).parent().find('a.more-actions').removeClass('active')
      };
    })
    $(this).parent().find('ul').addClass('active');
  })

  $('td.actions ul').mouseleave(function(){
    $(this).parent().find('a.more-actions').removeClass('active')
    $(this).removeClass('active');
  })

  $(document).on("submit", ".modal #create_keypair_form", function(e){
    var $this = $(this);
    $this.closest(".modal").modal("hide");
    $('#main_content .page-header').after('<div class="alert-message info">'
        + '<p><strong>Info: </strong>The data on this page may have changed, '
        + '<a href=".">click here to refresh it</a>.</p>'
        + '</div>');
    return true;
  });
})


