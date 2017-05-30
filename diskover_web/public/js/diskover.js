$(document).ready(function() {
  $("#tagAllDelete").click(function() {
      $(".tagDeleteInput").prop('checked', true);
      $(".tagDeleteLabel").attr('class', 'tagDeleteLabel btn btn-warning active');
      $(".tagArchiveLabel").attr('class', 'tagArchiveLabel btn btn-success');
      $(".tagKeepLabel").attr('class', 'tagKeepLabel btn btn-info');
      $(".tagDeleteLabel").closest('tr').attr('class', 'warning');
  });

  $("#tagAllArchive").click(function() {
      $(".tagArchiveInput").prop('checked', true);
      $(".tagArchiveLabel").attr('class', 'tagArchiveLabel btn btn-success active');
      $(".tagDeleteLabel").attr('class', 'tagDeleteLabel btn btn-warning');
      $(".tagKeepLabel").attr('class', 'tagKeepLabel btn btn-info');
      $(".tagArchiveLabel").closest('tr').attr('class', 'success');
  });

  $("#tagAllKeep").click(function() {
      $(".tagKeepInput").prop('checked', true);
      $(".tagKeepLabel").attr('class', 'tagKeepLabel btn btn-info active');
      $(".tagArchiveLabel").attr('class', 'tagArchiveLabel btn btn-success');
      $(".tagDeleteLabel").attr('class', 'tagDeleteLabel btn btn-warning');
      $(".tagKeepLabel").closest('tr').attr('class', 'info');
  });

  $("#refresh").click(function() {
      location.reload(true);
  });

  $("#highlightRowDelete input").change(function() {
      $(this).closest('tr').attr('class', 'warning');
  });

  $("#highlightRowArchive input").change(function() {
      $(this).closest('tr').attr('class', 'success');
  });

  $("#highlightRowKeep input").change(function() {
      $(this).closest('tr').attr('class', 'info');
  });

  $(".search").keyup(function () {
  var searchTerm = $(".search").val();
  var listItem = $('.results tbody').children('tr');
  var searchSplit = searchTerm.replace(/ /g, "'):containsi('")

  $.extend($.expr[':'], {'containsi': function(elem, i, match, array){
        return (elem.textContent || elem.innerText || '').toLowerCase().indexOf((match[3] || "").toLowerCase()) >= 0;
    }
  });

  $(".results tbody tr").not(":containsi('" + searchSplit + "')").each(function(e){
    $(this).attr('visible','false');
  });

  $(".results tbody tr:containsi('" + searchSplit + "')").each(function(e){
    $(this).attr('visible','true');
  });

  var jobCount = $('.results tbody tr[visible="true"]').length;
    $('.counter').text(jobCount + ' item');

  if(jobCount == '0') {$('.no-result').show();}
    else {$('.no-result').hide();}
      });

});
