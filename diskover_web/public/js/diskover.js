$("#tagAllDelete").click(function() {
    $(".tagDeleteInput").prop('checked', true);
    $(".tagDeleteLabel").attr('class', 'tagDeleteLabel btn btn-info active');
    $(".tagArchiveLabel").attr('class', 'tagArchiveLabel btn btn-info');
    $(".tagKeepLabel").attr('class', 'tagKeepLabel btn btn-info');
});

$("#tagAllArchive").click(function() {
    $(".tagArchiveInput").prop('checked', true);
    $(".tagArchiveLabel").attr('class', 'tagArchiveLabel btn btn-info active');
    $(".tagDeleteLabel").attr('class', 'tagDeleteLabel btn btn-info');
    $(".tagKeepLabel").attr('class', 'tagKeepLabel btn btn-info');
});

$("#tagAllKeep").click(function() {
    $(".tagKeepInput").prop('checked', true);
    $(".tagKeepLabel").attr('class', 'tagKeepLabel btn btn-info active');
    $(".tagArchiveLabel").attr('class', 'tagArchiveLabel btn btn-info');
    $(".tagDeleteLabel").attr('class', 'tagDeleteLabel btn btn-info');
});

$("#refresh").click(function() {
    location.reload(true);
});
