/*
diskover-web community edition (ce)
https://github.com/diskoverdata/diskover-community/
https://diskoverdata.com

Copyright 2017-2023 Diskover Data, Inc.
"Community" portion of Diskover made available under the Apache 2.0 License found here:
https://www.diskoverdata.com/apache-license/
 
All other content is subject to the Diskover Data, Inc. end user license agreement found at:
https://www.diskoverdata.com/eula-subscriptions/
  
Diskover Data products and features for all versions found here:
https://www.diskoverdata.com/solutions/

*/

// default constants

const FILTER = 1;
const MAXDEPTH = 2;
const TIME = 0;
const TIME_FIELD = 'mtime';
const USE_COUNT = 0;
const SHOW_FILES = 0;
const SIZE_FIELD = 'size';

// end default constants


var index = ($_GET('index')) ? $_GET('index') : getCookie('index');
var path = getCookie('path');
// replace any + character from space
path = path.replace(/\+/g, '%20');
// replace any + character from space
path = decodeURIComponent(path);
// remove any trailing slash
if (path !== '/') {
    path = path.replace(/\/$/, "");
}
var rootpath = getCookie('rootpath');
rootpath = rootpath.replace(/\+/g, '%20');
rootpath = decodeURIComponent(rootpath);
// set parent path
var parentpath = getCookie('parentpath');
parentpath = parentpath.replace(/\+/g, '%20');
parentpath = decodeURIComponent(parentpath);

// filters for analytics pages
var filter = FILTER;
var time = TIME;
var timefield = TIME_FIELD;
var maxdepth = MAXDEPTH;
var use_count = USE_COUNT;
var show_files = SHOW_FILES;
var sizefield = getCookie('sizefield');
if (sizefield === '') var sizefield = SIZE_FIELD;

// set usecache
var usecache = setUseCache();


$(document).ready(function () {

    // reload page button on search results page
    $(".reload-results").click(function () {
        // flush cache for file tree
        console.log("setting usecache cookie to 0 because reload");
        usecache = 0;
        setCookie('usecache', 0)
        location.reload(true);
    });

    // select results per page
    $("#resultsize").change(function () {
        setCookie("resultsize", $("#resultsize").val());
        $(this).closest('form').trigger('submit');
    });

    // reload page button
    $("#reload").click(function () {
        console.log("removing path cookie because reload");
        deleteCookie("path");
        console.log("setting usecache cookie to 0 because reload");
        setCookie("usecache", 0);
        location.reload(true);
    });

    // search within text input
    $("#searchwithin").keyup(function () {
        var searchTerm = $("#searchwithin").val();
        var searchSplit = searchTerm.replace(/ /g, "'):containsi('")

        $.extend($.expr[':'], {
            'containsi': function (elem, i, match, array) {
                return (elem.innerText || elem.textContent || '').toLowerCase().indexOf((match[3] || "").toLowerCase()) >= 0;
            }
        });

        $("#results-tbody tr").not(":containsi('" + searchSplit + "')").each(function (e) {
            $(this).attr('visible', 'false');
        });

        $("#results-tbody tr:containsi('" + searchSplit + "')").each(function (e) {
            $(this).attr('visible', 'true');
        });

        var jobCount = $('#results-tbody tr[visible="true"]').length;
        $('.counter').text(jobCount + ' items found');

        if (jobCount === 0) {
            $('.no-result').show();
        } else {
            $('.no-result').hide();
        }
    });

    // convert php saved searches into js array
    var savedsearches = getSavedSearchQuery();

    // default search nav html text
    var searchnavhtml = '<div class="pull-right"><button title="close" type="button" class="btn btn-default btn-sm" onclick="javascript:hideSearchBox(); return false;"><span style="font-size:14px;">&nbsp;<i class="far fa-window-close" style="color:lightgray"></i>&nbsp;</span></button></div>';
    searchnavhtml += '<span style="color:white"><i class="fas fa-info-circle"></i> Search using Elasticsearch Lucene syntax by starting search with \\</span><br>'
    if(getCookie('wildcardsearch') == 1) {
        searchnavhtml += '<div class="pull-right"><span style="color:#EEFD7B"><i class="fab fa-searchengin"></i> Predictive search enabled</span></div>'
    }
    searchnavhtml += '<br><span style="color:white; font-weight:bold">Recent searches</span></span><br>';
    savedsearches.forEach(element => {
        if (element !== null) {
            var element_enc = encodeURIComponent(element);
            var element_min = truncate(element, 175);
            searchnavhtml += '<div style="margin: 4px"><i class="glyphicon glyphicon-time"></i> <a href="search.php?&submitted=true&p=1&q=' + element_enc + '">' + element_min + '</a></div>';
        }
    });

    // search items in ES on keypress on nav search
    $("#searchnavinput").click(function () {
        var search_phrases = ["Search your old data, free up your space. Rejoice.",
            "Search for whatever; let's find it together",
            "Surely that's around here somewhere...",
            "Search all across diskover",
            "Search far and wide",
            "Search because it's faster than scrolling",
            "Type what you want to search for. diskover will do the rest.",
            "What do you want to search for today?"
        ];
        $('#essearchreply-text-nav').html(searchnavhtml);
        $("#searchnavinput").attr("placeholder", search_phrases[Math.floor(Math.random() * search_phrases.length)]);
        $('#essearchreply-nav').show();
        return false;
    })

    // change background colour of nav search box on mousedown
    $("#searchnavinput").mousedown(function () {
        $("#searchnavinput").attr('style', 'background-color: #060606 !important');
    })

    // search items in ES on keypress on nav search
    // delay for 1000 ms before searching ES for user input
    $("#searchnavinput").keyup(delay(function (e) {
        if ($('#searchnavinput').val() === "") {
            $('#essearchreply-text-nav').html(searchnavhtml);
            return false;
        }
        $.ajax({
            type: 'GET',
            url: 'searchkeypress.php',
            data: $('#searchnav').serialize(),
            success: function (data) {
                if (data != "") {
                    $('#essearchreply-nav').show();
                    $('#essearchreply-text-nav').html(data);
                } else {
                    $('#essearchreply-text-nav').html("");
                    $('#essearchreply-nav').hide();
                }
            }
        });
    }, 500));

    // hide search results pull down on body click
    $(document).on('click', '#mainwindow', function () {
        $("#searchnavinput").attr("placeholder", "Search");
        $('#essearchreply-nav').hide();
        // set search nav input background colour back to default
        $("#searchnavinput").attr('style', 'background-color: #373737 !important');
    });

    // notify user of new index
    var newindexnotifcation = getCookie('newindexnotification');
    if (newindexnotifcation == 1) {
        $("#newindexnotification").modal('show');
    }

    // show modal for sending anon data
    var sendanondata = getCookie('sendanondata');
    if (sendanondata == "") {
        $('#sendanondataModal').modal('show');
    }

    // check session hasn't expired
    function check_session() {
        $.ajax({
            url: 'check_session.php',
            method: 'POST',
            cache: false,
            success:function(response){
                if(response == 'logout') {
                    window.location.replace("logout.php?inactive");
                    return true;
                } else if (response == "nologin") {
                    return true;
                } else {
                    console.log('check session login idle time: ' + response + ' sec')
                    return true;
                }
            },
            error: function(response){
                console.error("check session error: " + response);
            }
        });
    }
    // check session every 10 seconds
    setInterval(function(){
        check_session();
    }, 10000);

});

// delay function
function delay(callback, ms) {
    var timer = 0;
    return function() {
        var context = this, args = arguments;
        clearTimeout(timer);
        timer = setTimeout(function () {
            callback.apply(context, args);
        }, ms || 0);
    };
}

// cookie functions
function setCookie(cname, cvalue, exdays) {
    // set default expire time to 1 year
    if (exdays == '') var exdays = 365;
    var d = new Date();
    d.setTime(d.getTime() + (exdays * 24 * 60 * 60 * 1000));
    var expires = "expires=" + d.toUTCString();
    document.cookie = cname + "=" + cvalue + ";" + expires + ";path=/";
}

function getCookie(cname) {
    var name = cname + "=";
    var decodedCookie = decodeURIComponent(document.cookie);
    var ca = decodedCookie.split(';');
    for (var i = 0; i < ca.length; i++) {
        var c = ca[i];
        while (c.charAt(0) == ' ') {
            c = c.substring(1);
        }
        if (c.indexOf(name) == 0) {
            return c.substring(name.length, c.length);
        }
    }
    return "";
}

function deleteCookie(cname) {
    document.cookie = cname + '=; expires=Thu, 01 Jan 1970 00:00:01 GMT;';
}

// GET url values
function $_GET(param) {
    var vars = {};
    window.location.href.replace(location.hash, '').replace(
        /[?&]+([^=&]+)=?([^&]*)?/gi, // regexp
        function (m, key, value) { // callback
            // remove any trailing #
            if (!value) return '';
            value = value.replace(/#$/, "");
            vars[key] = value !== undefined ? value : '';
        }
    );

    if (param) {
        return vars[param] ? vars[param] : '';
    }
    return vars;
}

// format bytes to mb, gb
function format(a, b) {
    if (0 === a) return "0 Bytes";
    // check if we are using base10 or base2 (default)
    if (getCookie('filesizebase10') == '1') {
        var c = 1000; // base 10
    } else {
        var c = 1024; // base 2
    }
    // set decimals
    var dec = getCookie('filesizedec');
    if (dec == '') {
        var dec = 1; // default 1
    } else {
        var dec = parseInt(dec);
    }
    var d = b || dec,
        e = ["Bytes", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB"],
        f = Math.floor(Math.log(a) / Math.log(c));
    return parseFloat((a / Math.pow(c, f)).toFixed(d)) + " " + e[f]
}

// return basename of path
function basename(path) {
    return path.replace(/.*\//, '');
}

// return dirname of path
function dirname(path) {
    return path.match(/.*\//).toString().slice(0, -1);
}

// format number with commas
function numberWithCommas(x) {
    return x.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}

// escape special characters
function escapeHTML(text) {
    var chr = {
        '+': '\\+',
        '-': '\\-',
        '=': '\\=',
        '&': '\\&',
        '|': '\\|',
        '<': '\\<',
        '>': '\\>',
        '!': '\\!',
        '(': '\\(',
        ')': '\\)',
        '{': '\\{',
        '}': '\\}',
        '[': '\\[',
        ']': '\\]',
        '^': '\\^',
        '"': '\\"',
        '~': '\\~',
        '*': '\\*',
        '?': '\\?',
        ':': '\\:',
        '\'': '\\\'',
        '/': '\\/',
        ' ': '\\ '
    };

    function abc(a) {
        return chr[a];
    }
    escaped_text = text.replace('\\', '\\\\');
    escaped_text = escaped_text.replace(/[\+\-\=&\|\<\>\!\(\)\{\}\[\]\^"~\*\?\:\/ ]/g, abc);
    return escaped_text;
}

// calculate change percentage between two numbers
function changePercent(a, b) {
    return ((a - b) / b) * 100;
}

// copy text from element id to clipboard on button click
function copyToClipboard(element) {
    var $temp = $("<input>");
    $("body").append($temp);
    var $text = $(element).text();
    $text = translatePath($text);
    $temp.val($text).select();
    document.execCommand("copy");
    $temp.remove();
    clipboardNotice();
}

// copy text to clipboard on copy path button click
function copyToClipboardText(text) {
    text = translatePath(text);
    var $temp = $("<input>");
    $("body").append($temp);
    $temp.val(text).select();
    document.execCommand("copy");
    $temp.remove();
    clipboardNotice();
}

// translate path
function translatePath(text) {
    var pathtranlsate = getCookie('pathtranslations');
    if (!pathtranlsate) {
        return text;
    }
    var pathtranslateArr = pathtranlsate.split(',');
    var totext;
    pathtranslateArr.forEach(element => {
        var pArr = element.split('|');
        var pattern = new RegExp(pArr[0], "g");
        var replace = pArr[1];
        totext = text.replace(pattern, replace)
        text = totext
    });
    return totext;
}

// clear diskover cookies
function clearCookies() {
    console.log("purging cookies");
    var cookies = document.cookie.split(";");
    for (var i = 0; i < cookies.length; i++) {
        var cookie = cookies[i];
        var eqPos = cookie.indexOf("=");
        var name = eqPos > -1 ? cookie.substr(0, eqPos) : cookie;
        deleteCookie(name);
    }
    alert('cookies cleared, please restart browser');
    return true;
}

// set usecache to false
function clearChartCache() {
    console.log("setting usecache cookie to false");
    setCookie("usecache", 0);
    alert('chart cache cleared');
    return true;
}

// set usecache
function setUseCache() {
    if ($_GET('usecache') != '') {
        usecache = $_GET('usecache');
    } else if (getCookie('usecache') != '') {
        usecache = getCookie('usecache');
    }
    // if usecache unset, set cookie
    if (usecache == null) {
        setCookie('usecache', 0);
    } else if (usecache == 0) {
        // enable cache for next load
        setCookie('usecache', 1);
    }
    return usecache;
}

// set time display for local timezone or utc (default)
function setTimeDisplay() {
    if (document.getElementById('timedisplay').checked) {
        setCookie('localtime', 1);
    } else {
        setCookie('localtime', 0);
    }
}

// set file size display in base10 or base2 (default)
function setFileSizeDisplay() {
    if (document.getElementById('sizedisplay').checked) {
        setCookie('filesizebase10', 1);
    } else {
        setCookie('filesizebase10', 0);
    }
}

// set size field, size_du or size (default)
function setSizeField() {
    if (document.getElementById('sizedu').checked) {
        setCookie('sizefield', 'size_du');
    } else {
        setCookie('sizefield', 'size');
    }
    setCookie('usecache', 0);
}

// set wildcard predictive search
function setWildcardSearch() {
    if (document.getElementById('wildcardsearch').checked) {
        setCookie('wildcardsearch', 1);
    } else {
        setCookie('wildcardsearch', 0);
    }
}

// set filter charts
function setFilterCharts() {
    if (document.getElementById('filterchart').checked) {
        setCookie('filtercharts', 1);
    } else {
        setCookie('filtercharts', 0);
    }
}

// set search file tree sort
function setSearchFileTreeSort() {
    if (document.getElementById('searchfiletreesort').checked) {
        setCookie('searchfiletreesort', 1);
    } else {
        setCookie('searchfiletreesort', 0);
    }
    setCookie('usecache', 0);
}

// set default sort
function setSortDisplay() {
    if (document.getElementById('sortdisplay').checked) {
        setCookie('unsorted', 1);
        deleteCookie('sort');
        deleteCookie('sortorder');
        deleteCookie('sort2');
        deleteCookie('sortorder2');
    } else {
        setCookie('unsorted', 0);
        setCookie('sort', 'parent_path');
        setCookie('sortorder', 'asc');
        setCookie('sort2', 'name');
        setCookie('sortorder2', 'asc');
    }
}

// reset sort order
function resetSort() {
    setCookie('sort', 'parent_path');
    setCookie('sortorder', 'asc');
    setCookie('sort2', 'name');
    setCookie('sortorder2', 'asc');
    alert("sort order reset, try searching again")
}

// set hidden fields for search results
function setHideFields(fieldname) {
    if (document.getElementById('hidefield_' + fieldname).checked) {
        setCookie('hidefield_' + fieldname, 1);
    } else {
        setCookie('hidefield_' + fieldname, 0);
    }
}

// set file size display decimals cookie
function setFileSizeDisplayDec() {
    var d = document.getElementById('filesizedec').value;
    setCookie('filesizedec', d);
    alert("file size decimals set to " + d);
}

function getSavedSearchQuery() {
    if (!getCookie('savedsearches')) {
        return [];
    }
    var json = getCookie('savedsearches');
    var savedsearches = JSON.parse(decodeURIComponent(json))
    var savedsearches_rev = savedsearches.reverse();
    return savedsearches_rev;
}

function truncate(str, n) {
    return (str.length > n) ? str.substr(0, n - 1) + '&hellip;' : str;
}

function setPathTranslation() {
    var val = document.getElementById('pathtranslateselect').value;
    setCookie('pathtranslations', val);
    alert('path translation saved');
    location.reload(true);
}

function removePathTranslation() {
    deleteCookie('pathtranslations');
    alert('path translation removed');
    location.reload(true);
}

// toggle notify on new index cookie
function setNotifyNewIndex() {
    if (document.getElementById('notifynewindex').checked) {
        setCookie('notifynewindex', 1);
    } else {
        setCookie('notifynewindex', 0);
    }
}

// replaces url parameters and loads page with updated parameters
function replaceSearch(name, value) {
    var str = location.search;
    if (new RegExp("[&?]" + name + "([=&].+)?$").test(str)) {
        str = str.replace(new RegExp("(?:[&?])" + name + "[^&]*", "g"), "")
    }
    str += "&";
    str += name + "=" + value;
    str = "?" + str.slice(1);
    location.assign(location.origin + location.pathname + str + location.hash)
}

// returns time range for es queries
function getTime() {
    if (time === '0' || time === 'now') {
        var last_time_high = 'now/m';
    } else if (time === '1d') {
        var last_time_high = 'now/m-1d/d';
    } else if (time === '1w') {
        var last_time_high = 'now/m-1w/d';
    } else if (time === '2w') {
        var last_time_high = 'now/m-2w/d';
    } else if (time === '1m') {
        var last_time_high = 'now/m-1M/d';
    } else if (time === '2m') {
        var last_time_high = 'now/m-2M/d';
    } else if (time === '3m') {
        var last_time_high = 'now/m-3M/d';
    } else if (time === '6m') {
        var last_time_high = 'now/m-6M/d';
    } else if (time === '1y') {
        var last_time_high = 'now/m-1y/d';
    } else if (time === '2y') {
        var last_time_high = 'now/m-2y/d';
    } else if (time === '3y') {
        var last_time_high = 'now/m-3y/d';
    } else if (time === '5y') {
        var last_time_high = 'now/m-5y/d';
    }

    return '* TO ' + last_time_high;
}

// toggles the tag button enabled/disabled state
function toggleTagButton() {
    //check if checkbox is checked
    function count() {
        var tag_checked = $('input.tagcheck:checked').length;
        return tag_checked;
    }
    if (count() > 0) {
        $('#tagbutton').removeAttr('disabled');
    } else {
        $('#tagbutton').attr('disabled', true);
    }
}

// toggles the file action button enabled/disabled state
function toggleFileActionButton() {
    //check if checkbox is checked
    function count() {
        var tag_checked = $('input.tagcheck:checked').length;
        return tag_checked;
    }
    if (count() > 0) {
        $('#fileactionbutton').removeAttr('disabled');
    } else {
        $('#fileactionbutton').attr('disabled', true);
    }
}

// update selected paths list
function updateSelectedList() {
    //check if checkbox is checked
    function count() {
        var tag_checked = $('input.tagcheck:checked').length;
        return tag_checked;
    }
    if (count() == 0) {
        fullpaths_selected = [];
    } else {
        var selectedpaths = document.getElementsByClassName("tagcheck");
        fullpaths_selected = [];
        for(var i = 0; i < selectedpaths.length; i++){
            if (selectedpaths[i].checked) {
                let fullpath = selectedpaths[i].value.split(",")[2];
                fullpaths_selected.push(fullpath)
            }
        }
    }
}

// save search filters form
function saveSearchFilters(action) {
    var extensions_arr = [];
    $.each($("input[name='extensions']:checked"), function () {
        extensions_arr.push($(this).val());
    });
    if (extensions_arr.length === 0) { extensions_arr = null };
    
    var filetype_arr = [];
    $.each($("input[name='filetype']:checked"), function () {
        filetype_arr.push($(this).val());
    });
    if (filetype_arr.length === 0) { filetype_arr = null };
    
    if ($("#nofilterdirs").is(":checked")) {
        nofilterdirsval = "on";
    } else {
        nofilterdirsval = null;
    } 
    
    if ($("#filtercharts").is(":checked")) {
        setCookie('filtercharts', 1)
    } else {
        setCookie('filtercharts', 0)
    }
    
    var formData = {
        doctype: $("#doctype").val(),
        nofilterdirs: nofilterdirsval,
        file_size_bytes_low: $("#file_size_bytes_low").val(),
        file_size_bytes_low_unit: $("#file_size_bytes_low_unit").val(),
        file_size_bytes_high: $("#file_size_bytes_high").val(),
        file_size_bytes_high_unit: $("#file_size_bytes_high_unit").val(),
        last_mod_time_low: $("#last_mod_time_low").val(),
        last_mod_time_high: $("#last_mod_time_high").val(),
        last_accessed_time_low: $("#last_accessed_time_low").val(),
        last_accessed_time_high: $("#last_accessed_time_high").val(),
        last_changed_time_low: $("#last_changed_time_low").val(),
        last_changed_time_high: $("#last_changed_time_high").val(),
        hardlinks_low: $("#hardlinks_low").val(),
        hardlinks_high: $("#hardlinks_high").val(),
        owner_operator: $("#owner_operator").val(),
        owner: $("#owner").val(),
        group_operator: $("#group_operator").val(),
        group: $("#group").val(),
        extensions_operator: $("#extensions_operator").val(),
        extensions: extensions_arr,
        extension_operator: $("#extension_operator").val(),
        extension: $("#extension").val(),
        filetype: filetype_arr,
        filetype_operator: $("#filetype_operator").val(),
        otherfields: $("#otherfields").val(),
        otherfields_operator: $("#otherfields_operator").val(),
        otherfields_input: $("#otherfields_input").val(),
    };
    console.log(formData)
    // clear all filters
    if (action == 'clearall') {
        for (var key in formData) {
            formData[key] = null;
        }
    }

    $.ajax({
        type: "POST",
        url: "savesearchfilters.php",
        data: formData,
        dataType: "json",
        encode: true,
    }).done(function (data) {
        //console.log(data);
        /*if (action == 'clearall') {
            alert('search filters cleared');
        } else {
            alert('search filters saved');
        }*/
        setCookie("usecache", 0);
        location.reload(true);
    });
}

// handle ES json error from analytics pages
function jsonError(err) {
    let errmsg = 'Json error getting data from diskover index.';
    console.error(errmsg);
    // set error cookie to expire 1 hour
    const d = new Date();
    d.setTime(d.getTime() + 3600);
    let expires = "expires="+ d.toUTCString();
    document.cookie = "error=" + errmsg + ";" + expires + ";path=/";
    // redirect to error page
    window.location.href = 'error.php';
}

// clears saved search results table column widths
function resetResultsTable() {
    // Clear all keys
    store.clearAll();
    alert('search results table column sizes reset');
}


// disables nav search submit
function disableSearchSubmit() {
    $("input[type=submit]", this).attr("disabled", "disabled");
    $("#searchnav").bind("submit",function(e){e.preventDefault();});
}


// enables nav search submit
function enableSearchSubmit() {
    $("input[type=submit]", this).removeAttr("disabled", "disabled");
    $("#searchnav").unbind("submit");
}

// show clipboard copy notice and hide after timeout
function clipboardNotice() {
    $('#clipboardnotice').modal('show');
    setTimeout(function() { 
        $('#clipboardnotice').modal('hide'); 
    }, 1000);
}


/* 
============= START INDICES =============
*/

// delete index check
function checkIndexDel() {
    var indices = document.getElementsByName('delindices_arr[]');
    var checked = document.getElementsByName('delindices_arr[]').length;
    var indices_names = [];
    Array.from(indices).forEach(function(item, index){
        indices_names.push(item.value);
    });
    if (checked == 0) {
        alert("select at least one index")
        return false;
    }
    if (confirm('Are you sure you want to remove the selected ' + checked + ' indices? (' + indices_names.join(", ") + ')')) {
        // submit form
        $('#form-deleteindex').submit();
        alert('Index deleting... please do not refresh the page or close the window.');
    } else {
        return false;
    }
}

// force delete index check
function checkForceIndexDel(i) {
    if (confirm('Are you sure you want to force remove this index? Check that the indexing process is no longer running before doing this!')) {
        location.href = 'selectindices.php?forcedelindex='+i
    } else {
        return false;
    }
}

// select index check
function checkSelectedIndex() {
    var indices = document.getElementsByClassName('indexcheck');
    var checked = 0;
    Array.from(indices).forEach(function(item, index){
        if($(item).prop("checked") == true){
            checked += 1;
        }
    });
    if (checked == 0) {
        alert("select at least one index")
        return false;
    }
    // submit form
    $('#form-selectindex').submit();
}

function addHidden() {
    var indices = document.getElementsByClassName('indexcheck');
    Array.from(indices).forEach(function(item, index){
        if($(item).prop("checked") == true){
            var id = 'hidden_index_del_' + item.value;
            $('#form-deleteindex').append('<input type="hidden" name="delindices_arr[]" value="' + item.value + '" id="' + id + '" />');
        } else {
            var id = 'hidden_index_del_' + item.value;
            $('#' + id).remove();
        }
    });
}

function checkSelected() {
    var indices = document.getElementsByClassName('indexcheck');
    var selected_index = getCookie('index');
    Array.from(indices).forEach(function(item, index){
        if (selected_index == item.value) {
            $(item).prop('checked', true);
        } else {
            $(item).prop("checked", false);
        }
    });
}

function setSendAnonData() {
    if ($('#sendanondata').prop('checked')) {
        setCookie("sendanondata", 1);
    } else {
        setCookie("sendanondata", 0);
    }
}

/* 
============= END INDICES =============
*/