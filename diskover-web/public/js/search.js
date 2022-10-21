/*
diskover-web community edition (ce)
https://github.com/diskoverdata/diskover-community/
https://diskoverdata.com

Copyright 2017-2022 Diskover Data, Inc.
"Community" portion of Diskover made available under the Apache 2.0 License found here:
https://www.diskoverdata.com/apache-license/
 
All other content is subject to the Diskover Data, Inc. end user license agreement found at:
https://www.diskoverdata.com/eula-subscriptions/
  
Diskover Data products and features for all versions found here:
https://www.diskoverdata.com/solutions/

*/

/*
 * d3 search results filetree for diskover-web
 */

// globals for file tree
var tree, ul, root, id, tip = null;
// global for selected paths
var fullpaths_selected = [];


$(document).ready(function () {
    // make results table columns resizable and save to store
    $("#results").resizableColumns({
        store: window.store
    });

    // shift-select multiple checkboxes in search results table
    var chkboxShiftLastChecked = [];

    $('[data-chkbox-shiftsel]').click(function(e){
        var chkboxType = $(this).data('chkbox-shiftsel');
        if(chkboxType === ''){
            chkboxType = 'default';
        }
        var $chkboxes = $('[data-chkbox-shiftsel="'+chkboxType+'"]');

        if (!chkboxShiftLastChecked[chkboxType]) {
            chkboxShiftLastChecked[chkboxType] = this;
            highlightRow(this);
            return;
        }

        if (e.shiftKey) {
            var start = $chkboxes.index(this);
            var end = $chkboxes.index(chkboxShiftLastChecked[chkboxType]);

            $chkboxes.slice(Math.min(start,end), Math.max(start,end)+ 1).prop('checked', chkboxShiftLastChecked[chkboxType].checked);

            chkboxShiftLastChecked[chkboxType] = this;

            var $chkboxesSelected = $chkboxes.slice(Math.min(start,end), Math.max(start,end)+ 1);
            for(let i = 0; i < $chkboxesSelected.length; i++){ 
                highlightRow($chkboxesSelected[i]);
            }
        } else {
            chkboxShiftLastChecked[chkboxType] = this;
        }
        highlightRow(this);
    });
});


// select all checkboxes on search results page
function selectAll() {
    $('.results').find('input[type="checkbox"]').prop('checked', true);
    // highlight rows
    $('.results').find('tr').not('thead tr').not('tfoot tr').addClass('info');
}


// unselect all checkboxes on search results page
function unSelectAll() {
    $('.results').find('input[type="checkbox"]').prop('checked', false);
    // remove highlight from rows
    $('.results').find('tr').not('thead tr').not('tfoot tr').removeClass('info');
}


// highlight row when clicking select row checkbox
function highlightRow(e) {
    if ($(e).is(':checked')) {
        $(e).closest('tr').addClass('info');
    } else {
        $(e).closest('tr').removeClass('info');
    }
}


// copy all paths on search result page to clipboard
function copyPathsToClipboard(paths) {
    var $temp = $("<textarea>");
    $("body").append($temp);
    var fullpaths_newlines = '';
    js_fullpaths.forEach(element => {
        element = translatePath(element);
        if(!paths) {
            element = basename(element);
        }
        fullpaths_newlines += element + '\r\n';
    });
    $temp.val(fullpaths_newlines).appendTo('body').select()
    document.execCommand('copy')
    $temp.remove();
    clipboardNotice();
}

// copy selected paths on search result page to clipboard
function copySelectedPathsToClipboard(paths) {
    if (fullpaths_selected.length === 0) {
        alert('no paths selected');
        return false;
    }
    var $temp = $("<textarea>");
    $("body").append($temp);
    var fullpaths_newlines = '';
    fullpaths_selected.forEach(element => {
        element = translatePath(element);
        if(!paths) {
            element = basename(element);
        }
        fullpaths_newlines += element + '\r\n';
    });
    $temp.val(fullpaths_newlines).appendTo('body').select()
    document.execCommand('copy')
    $temp.remove();
    clipboardNotice();
}

function goToTreeTop() {
    window.location.href = "search.php?submitted=true&p=1&q=parent_path:" + encodeURIComponent(escapeHTML(rootpath)) + "&path=" + encodeURIComponent(rootpath);
}

function goToTreeUp() {
    window.location.href = "search.php?submitted=true&p=1&q=parent_path:" + encodeURIComponent(escapeHTML(parentpath)) + "&path=" + encodeURIComponent(parentpath);
}

function goToTreeBack() {
    var page = document.referrer.split(/[?#]/)[0].split("/").slice(-1)[0];
    if (page == "search.php") {
        window.history.back();
    }
}

function goToTreeForward() {
    var page = document.referrer.split(/[?#]/)[0].split("/").slice(-1)[0];
    if (page == "search.php") {
        window.history.forward();
    }
}

function hideTree() {
    if ($("#tree-wrapper").is(":visible") === false) {
        setCookie('hidesearchtree', 0);
        location.reload(true);
    } else {
        var x = document.getElementById("tree-wrapper");
        var y = document.getElementById("search-results-wrapper");
        var a = document.getElementById("tree-button-wrapper");
        var b = document.getElementById("tree-button-container");
        var c = document.getElementById("tree-button-container-sm");
        if (x.style.display === "none") {
            x.style.display = "block";
            y.className = "col-md-10 search-results-wrapper";
            a.className = "col-lg-2 tree-button-wrapper";
            b.style.display = "block";
            c.style.display = "none";
            setCookie('hidesearchtree', 0);
        } else {
            x.style.display = "none";
            y.className = "col-md-12 search-results-wrapper-lg";
            a.className = "col-lg-2 tree-button-wrapper-sm";
            b.style.display = "none";
            c.style.display = "block";
            setCookie('hidesearchtree', 1);
        }
    }
}

function hideCharts() {
    // check if we need to load charts data
    if ($("#searchCharts-container").is(":visible") === false) {
        setCookie('hidesearchcharts', 0);
        location.reload(true);
    } else {
        $('#searchCharts-container').toggle();
        if ($("#searchCharts-container").is(":visible")) {
            setCookie('hidesearchcharts', 0);
        } else {
            setCookie('hidesearchcharts', 1);
        }
    }
}

function getJSONFileTree() {
    console.time('loadtime')
    // get json data from Elasticsearch using php data grabber
    console.log("grabbing json data from Elasticsearch");

    // config references
    chartConfig = {
        target: 'tree-container',
        data_url: 'd3_data_search.php?path=' + encodeURIComponent(path) + '&filter=0&time=0&use_count=0&show_files=0&usecache=' + usecache
    };

    // loader settings
    opts = {
        lines: 12, // The number of lines to draw
        length: 6, // The length of each line
        width: 3, // The line thickness
        radius: 7, // The radius of the inner circle
        color: '#EE3124', // #rgb or #rrggbb or array of colors
        speed: 1.9, // Rounds per second
        trail: 40, // Afterglow percentage
        className: 'spinner', // The CSS class to assign to the spinner
    };

    var target = document.getElementById(chartConfig.target);
    // trigger loader
    var spinner = new Spinner(opts).spin(target);
    console.log(chartConfig.data_url)
    // load json data from Elasticsearch
    d3.json(chartConfig.data_url, function (error, data) {
        // handle error
        if (error) {
            jsonError(error);
        }
        root = data;
        // add dir info to details div
        var dirdetails = "<i class=\"fas fa-info-circle\"></i>&nbsp;&nbsp;&nbsp;&nbsp;<b>" + data.name + "</b>&nbsp;&nbsp;&nbsp;&nbsp;<b>Size</b> " +
            format(data.size) + "&nbsp;&nbsp;&nbsp;&nbsp;<b>Items</b> " + numberWithCommas(data.count) +
            "&nbsp;&nbsp;&nbsp;&nbsp;<b>Files</b> " + numberWithCommas(data.count_files) +
            "&nbsp;&nbsp;&nbsp;&nbsp;<b>Folders</b> " + numberWithCommas(data.count_subdirs) +
            "&nbsp;&nbsp;&nbsp;&nbsp;<b>Modified</b> " + data.modified;
        $("#dirdetails").append(dirdetails);
        // stop spin.js loader
        spinner.stop();
        console.timeEnd('loadtime');
        // load file tree
        if (getCookie('hidesearchtree') != 1) {
            updateTree(root, root);
        }
    });
}

function toggleChildren(d) {
    if (d.children) {
        d._children = d.children;
        d.children = null;
    } else if (d._children) {
        d.children = d._children;
        d._children = null;
    }
}

function click(d) {
    location.href = "search.php?submitted=true&p=1&q=parent_path:" + encodeURIComponent(escapeHTML(d.name)) + "&path=" + encodeURIComponent(d.name);
}

function updateTree(data, parent) {
    var nodes = tree.nodes(data),
        treeduration = 0;

    var nodeEls = ul.selectAll("li.node").data(nodes, function (d) {
        d.id = d.id || ++id;
        return d.id;
    });

    //entered nodes
    var entered = nodeEls.enter().append("li").classed("node", true)
        .style("top", parent.y + "px")
        .style("opacity", 0)
        .style("height", tree.nodeHeight() + "px");

    //add icons for folder for file
    entered.append("span").attr("class", function (d) {
            var foldericon = "fa-folder";
            var icon = (d.count > 0 || d.type === 'directory') ? foldericon : "fa-file";
            return "fas " + icon;
        })
        .style('cursor', 'pointer')
        .on("click", function (d) {
            click(d);
        })
        .on("mouseover", function (d) {
            tip.show(d, this);
        })
        .on('mouseout', function (d) {
            tip.hide(d);
        })
        .on('mousemove', function () {
            return tip
                .style("top", (d3.event.pageY - 10) + "px")
                .style("left", (d3.event.pageX + 10) + "px");
        });

    //add text for filename
    entered.append("span").attr("class", "filename")
        .html(function (d) {
            return d.depth === 0 ? d.name : d.name.split('/').pop();
        })
        .on("click", function (d) {
            click(d);
        })
        .on("mouseover", function (d) {
            d3.select(this).classed("selected", true);
            tip.show(d, this);
        })
        .on('mouseout', function (d) {
            d3.selectAll(".selected").classed("selected", false);
            tip.hide(d);
        })
        .on('mousemove', function () {
            return tip
                .style("top", (d3.event.pageY - 10) + "px")
                .style("left", (d3.event.pageX + 10) + "px");
        });

    //add text for size
    entered.append("span").attr("class", "filesize-darkergray")
        .html(function (d) {
            return " " + format(d.size);
        })

    //update position with transition
    nodeEls.transition().duration(treeduration)
        .style("top", function (d) {
            return (d.y - tree.nodeHeight()) + "px";
        })
        .style("left", function (d) {
            return d.x + "px";
        })
        .style("opacity", 1);
    nodeEls.exit().remove();
}


$(function () {
    'use strict'

    /* ------- SEARCH RESULTS FILE TREE -------*/

    if (getCookie('hidesearchtree') != 1 || getCookie('hidesearchcharts') == 0) {
        // get json data for file tree
        getJSONFileTree();
    }

    if (getCookie('hidesearchtree') != 1) {
        var svg = d3.select("#tree-container")
            .append("svg")
            .append("g");

        /* ------- TOOLTIP -------*/

        tip = d3.tip()
            .attr('class', 'd3-tip')
            .html(function (d) {
                var rootval = root.size;
                var percent = (d.size / rootval * 100).toFixed(1) + '%';
                var sum = format(d.size);
                var ret = "<span style='font-size:12px;color:white;'>" + d.name + "</span><br><span style='font-size:12px; color:red;'>" + sum + " (" + percent + ")</span>";
                if (d.type === 'directory') {
                    ret += "<br><span style='font-size:11px; color:lightgray;'>Items: " + numberWithCommas(d.count) + "</span>";
                    ret += "<br><span style='font-size:11px; color:lightgray;'>Files: " + numberWithCommas(d.count_files) + "</span>";
                    ret += "<br><span style='font-size:11px; color:lightgray;'>Folders: " + numberWithCommas(d.count_subdirs) + "</span>";
                }
                ret += "<br><span style='font-size:11px; color:lightgray;'>Modified: " + d.modified + "</span>";
                return ret;
            });

        svg.call(tip);

        d3.select("#tree-container").append("div")
            .attr("class", "tooltip")
            .style("opacity", 0);


        root, id = 0;

        tree = d3.layout.treelist()
            .childIndent(10)
            .nodeHeight(20);

        ul = d3.select("#tree-container").append("ul").classed("treelist", "true");
    }

    /* ------- END SEARCH RESULTS FILE TREE -------*/


    /* ------- SEARCH RESULTS CHARTS -------*/

    if (getCookie('hidesearchcharts') != 1) {
        // config references
        var chartConfig = {
            target: 'searchCharts-container',
            data_url1: 'd3_data_search_dirsizechart.php?path=' + encodeURIComponent(path) + '&usecache=' + usecache,
            data_url2: 'd3_data_pie_ext_searchresults.php?path=' + encodeURIComponent(path) + '&usecache=' + usecache,
            data_url3: 'd3_data_bar_mtime_searchresults.php?path=' + encodeURIComponent(path) + '&usecache=' + usecache
        };

        // loader settings
        var opts = {
            lines: 12, // The number of lines to draw
            length: 6, // The length of each line
            width: 3, // The line thickness
            radius: 7, // The radius of the inner circle
            color: '#EE3124', // #rgb or #rrggbb or array of colors
            speed: 1.9, // Rounds per second
            trail: 40, // Afterglow percentage
            className: 'spinner', // The CSS class to assign to the spinner
        };

        // loader settings
        var target = document.getElementById(chartConfig.target);

        // trigger loader
        var spinner = new Spinner(opts).spin(target);

        // load json data from Elasticsearch
        // use d3 queue to load json files simultaneously
        var q = d3.queue()
            .defer(d3.json, chartConfig.data_url1)
            .defer(d3.json, chartConfig.data_url2)
            .defer(d3.json, chartConfig.data_url3)
            .await(function (error, data1, data2, data3) {
                // handle error
                if (error) {
                    jsonError(error);
                }

                data1 = data1.children;
                data2 = data2.children;
                data3 = data3.children;

                //console.log(data)
                // stop spin.js loader
                spinner.stop();
                renderCharts(data1, data2, data3);
            });
    }

    function renderCharts(data1, data2, data3) {
        // chart settings
        var ticksStyle = {
            fontColor: '#495057',
            fontStyle: 'bold'
        }

        var mode = 'index'
        var intersect = true

        var default_colors = ['#3366CC', '#DC3912', '#FF9900', '#109618', '#990099', '#3B3EAC', '#0099C6', '#DD4477', '#66AA00', '#B82E2E', '#316395', '#994499', '#22AA99', '#AAAA11', '#6633CC', '#E67300', '#8B0707', '#329262', '#5574A6', '#3B3EAC']
        var hot_cold_colors = ["#00468B", "#3465CC", "#0099C6", "#FEFE22", "#FF9902", "#DC3912"]

        //----------------
        //- BAR/PIE DIR SIZE/COUNT CHART -
        //----------------

        // hide top dir chart if no subdirs
        if (data1.length === 0) {
            $('#topDirs-Chart-container').hide();
        } else {
            // by size bar chart

            var top_dirs_labels = []
            var top_dirs_data_size = []
            var top_dirs_colors = []
            var top_dirs_colors_border = []
            var top_dirs_colors_map = []

            for (var i in data1) {
                var name = data1[i].name;
                top_dirs_labels.push(basename(name))
                top_dirs_data_size.push(data1[i].size)
                var c = default_colors[i]
                top_dirs_colors.push(c)
                top_dirs_colors_border.push('#2F3338')
                top_dirs_colors_map[name] = c
            }

            var topDirsBySizebarChartCanvas = $("#topDirsBySize-barChart")
            var topDirsbarData = {
                labels: top_dirs_labels,
                datasets: [{
                    data: top_dirs_data_size,
                    backgroundColor: top_dirs_colors,
                    borderColor: top_dirs_colors_border
                }]
            }
            var topDirsbarOptions = {
                legend: {
                    display: false,
                },
                tooltips: {
                    mode: 'label',
                    callbacks: {
                        label: function (tooltipItem, data1) {
                            var i = tooltipItem.index;
                            var total = data1.datasets[0].data.reduce(function(previousValue, currentValue, currentIndex, array) {
                                return previousValue + currentValue;
                            });
                            var currentValue = data1.datasets[0].data[i];
                            var percentage = parseFloat((currentValue/total*100).toFixed(1));
                            return data1.labels[i] + ': ' + format(currentValue) + ' (' + percentage +'%)';
                        }
                    }
                },
                scales: {
                    xAxes: [{
                        stacked: true,
                        ticks: {
                            // Format size in the ticks
                            callback: function (value, index, values) {
                                return format(value, '0');
                            }
                        }
                    }]
                },
                title: {
                    display: true,
                    text: 'Top Directories by Size'
                },
                maintainAspectRatio: false,
                responsive: true,
                onClick: function(event, clickedElements) {
                    if (clickedElements.length === 0) return;
                    var e = clickedElements[0];
                    var dir = this.data.labels[e._index];
                    //var size = this.data.datasets[0].data[e._index];
                    var pp = encodeURIComponent(escapeHTML(decodeURIComponent(path) + '\/' + dir));
                    var pp_path = encodeURIComponent(decodeURIComponent(path + '\/' + dir));
                    window.location.href = "search.php?submitted=true&p=1&q=parent_path:" + pp + "*&path=" + pp_path;
                    return false;
                },
                onHover: function (event, legendItem, legend) {
                    $("#topDirsBySize-barChart").css("cursor", "pointer");
                },
                onLeave: function (event, legendItem, legend) {
                    $("#topDirsBySize-barChart").css("cursor", "default");
                }
            }

            var topDirsBySizebarChart = new Chart(topDirsBySizebarChartCanvas, {
                type: 'horizontalBar',
                data: topDirsbarData,
                options: topDirsbarOptions
            })

            // by count pie chart

            var top_dirs_labels = []
            var top_dirs_data_count = []
            var top_dirs_colors = []
            var top_dirs_colors_border = []

            // re-sort data by top count
            data1.sort((a, b) => (a.count > b.count) ? -1 : 1)
            //console.log(data)

            for (var i in data1) {
                var name = data1[i].name;
                top_dirs_labels.push(basename(name))
                top_dirs_data_count.push(data1[i].count)
                if (name in top_dirs_colors_map) {
                    var c = top_dirs_colors_map[name]
                } else {
                    var c = default_colors[i]
                }
                top_dirs_colors.push(c)
                top_dirs_colors_border.push('#2F3338')
            }

            var topDirsByCountpieChartCanvas = $("#topDirsByCount-pieChart")
            var topDirspieData = {
                labels: top_dirs_labels,
                datasets: [{
                    data: top_dirs_data_count,
                    backgroundColor: top_dirs_colors,
                    borderColor: top_dirs_colors_border
                }]
            }
            var topDirspieOptions = {
                legend: {
                    display: true,
                    position: 'right',
                    labels: {
                        fontColor: '#C8C8C8'
                    },
                    onClick: function (event, legendItem, legend) {
                        var dir = legendItem.text;
                        var pp = encodeURIComponent(escapeHTML(decodeURIComponent(path) + '\/' + dir));
                        var pp_path = encodeURIComponent(decodeURIComponent(path + '\/' + dir));
                        window.location.href = "search.php?submitted=true&p=1&q=parent_path:" + pp + "*&path=" + pp_path;
                        return false;
                    },
                    onHover: function (event, legendItem, legend) {
                        $("#topDirsByCount-pieChart").css("cursor", "pointer");
                    },
                    onLeave: function (event, legendItem, legend) {
                        $("#topDirsByCount-pieChart").css("cursor", "default");
                    }
                },
                tooltips: {
                    mode: 'label',
                    callbacks: {
                        label: function (tooltipItem, data1) {
                            var i = tooltipItem.index;
                            var total = data1.datasets[0].data.reduce(function(previousValue, currentValue, currentIndex, array) {
                                return previousValue + currentValue;
                            });
                            var currentValue = data1.datasets[0].data[i];
                            var percentage = parseFloat((currentValue/total*100).toFixed(1));
                            return data1.labels[i] + ': ' + currentValue.toLocaleString() + ' files (' + percentage +'%)';
                        }
                    }
                },
                title: {
                    display: true,
                    text: 'Top Directories by Count'
                },
                maintainAspectRatio: false,
                responsive: true,
                onClick: function(event, clickedElements) {
                    if (clickedElements.length === 0) return;
                    var e = clickedElements[0];
                    var dir = this.data.labels[e._index];
                    //var size = this.data.datasets[0].data[e._index];
                    var pp = encodeURIComponent(escapeHTML(decodeURIComponent(path) + '\/' + dir));
                    var pp_path = encodeURIComponent(decodeURIComponent(path + '\/' + dir));
                    window.location.href = "search.php?submitted=true&p=1&q=parent_path:" + pp + "*&path=" + pp_path;
                    return false;
                },
                onHover: function (event, legendItem, legend) {
                    $("#topDirsByCount-pieChart").css("cursor", "pointer");
                },
                onLeave: function (event, legendItem, legend) {
                    $("#topDirsByCount-pieChart").css("cursor", "default");
                }
            }

            var topDirsByCountpieChart = new Chart(topDirsByCountpieChartCanvas, {
                type: 'doughnut',
                data: topDirspieData,
                options: topDirspieOptions
            })
        }

        //--------------------
        //- END BAR/PIE DIR SIZE/COUNT CHART -
        //--------------------


        //----------------
        //- BAR/PIE EXT CHART -
        //----------------

        // hide top dir chart if no files
        if (data2.length === 0) {
            $('#mtime-Chart-container').hide();
            $('#topFileTypes-Chart-container').hide();
        } else {
            // by size bar chart

            var top_ext_labels = []
            var top_ext_data_size = []
            var top_ext_colors = []
            var top_ext_colors_border = []
            var top_ext_colors_map = []

            for (var i in data2) {
                var name = data2[i].name;
                if (name == '') {
                    name = 'NULL (no ext)'
                }
                top_ext_labels.push(name)
                top_ext_data_size.push(data2[i].size)
                var c = default_colors[i]
                top_ext_colors.push(c)
                top_ext_colors_border.push('#2F3338')
                top_ext_colors_map[name] = c
            }

            var topFileTypesBySizebarChartCanvas = $("#topFileTypesBySize-barChart")
            var topFileTypesbarData = {
                labels: top_ext_labels,
                datasets: [{
                    data: top_ext_data_size,
                    backgroundColor: top_ext_colors,
                    borderColor: top_ext_colors_border
                }]
            }
            var topFileTypesbarOptions = {
                legend: {
                    display: false,
                },
                tooltips: {
                    mode: 'label',
                    callbacks: {
                        label: function (tooltipItem, data2) {
                            var i = tooltipItem.index;
                            var total = data2.datasets[0].data.reduce(function(previousValue, currentValue, currentIndex, array) {
                                return previousValue + currentValue;
                            });
                            var currentValue = data2.datasets[0].data[i];
                            var percentage = parseFloat((currentValue/total*100).toFixed(1));
                            return data2.labels[i] + ': ' + format(currentValue) + ' (' + percentage +'%)';
                        }
                    }
                },
                scales: {
                    xAxes: [{
                        stacked: true,
                        ticks: {
                            // Format size in the ticks
                            callback: function (value, index, values) {
                                return format(value, '0');
                            }
                        }
                    }]
                },
                title: {
                    display: true,
                    text: 'Top File Types by Size'
                },
                maintainAspectRatio: false,
                responsive: true,
                onClick: function(event, clickedElements) {
                    if (clickedElements.length === 0) return;
                    var e = clickedElements[0];
                    var ext = this.data.labels[e._index];
                    //var size = this.data.datasets[0].data[e._index];
                    if (ext == "NULL (no ext)") {
                        ext = "\"\"";
                    }
                    var pp = encodeURIComponent(escapeHTML(decodeURIComponent(path)));
                    window.location.href = "search.php?submitted=true&p=1&q=extension:" + ext + " AND parent_path:" + pp + "*&doctype=file";
                    return false;
                },
                onHover: function (event, legendItem, legend) {
                    $("#topFileTypesBySize-barChart").css("cursor", "pointer");
                },
                onLeave: function (event, legendItem, legend) {
                    $("#topFileTypesBySize-barChart").css("cursor", "default");
                }
            }

            var topFileTypesBySizebarChart = new Chart(topFileTypesBySizebarChartCanvas, {
                type: 'horizontalBar',
                data: topFileTypesbarData,
                options: topFileTypesbarOptions
            })

            // by count pie chart

            var top_ext_labels = []
            var top_ext_data_count = []
            var top_ext_colors = []
            var top_ext_colors_border = []

            // re-sort data by top count
            data2.sort((a, b) => (a.count > b.count) ? -1 : 1)

            for (var i in data2) {
                var name = data2[i].name;
                if (name == '') {
                    name = 'NULL (no ext)'
                }
                top_ext_labels.push(name)
                top_ext_data_count.push(data2[i].count)
                if (name in top_ext_colors_map) {
                    var c = top_ext_colors_map[name]
                } else {
                    var c = default_colors[i]
                }
                top_ext_colors.push(c)
                top_ext_colors_border.push('#2F3338')
            }

            var topFileTypesByCountpieChartCanvas = $("#topFileTypesByCount-pieChart")
            var topFileTypespieData = {
                labels: top_ext_labels,
                datasets: [{
                    data: top_ext_data_count,
                    backgroundColor: top_ext_colors,
                    borderColor: top_ext_colors_border
                }]
            }
            var topFileTypespieOptions = {
                legend: {
                    display: true,
                    position: 'right',
                    labels: {
                        fontColor: '#C8C8C8'
                    },
                    onClick: function (event, legendItem, legend) {
                        var ext = legendItem.text;
                        if (ext == "NULL (no ext)") {
                            ext = "\"\"";
                        }
                        var pp = encodeURIComponent(escapeHTML(decodeURIComponent(path)));
                        window.location.href = "search.php?submitted=true&p=1&q=extension:" + ext + " AND parent_path:" + pp + "*&doctype=file";
                        return false;
                    },
                    onHover: function (event, legendItem, legend) {
                        $("#topFileTypesByCount-pieChart").css("cursor", "pointer");
                    },
                    onLeave: function (event, legendItem, legend) {
                        $("#topFileTypesByCount-pieChart").css("cursor", "default");
                    }
                },
                tooltips: {
                    mode: 'label',
                    callbacks: {
                        label: function (tooltipItem, data2) {
                            var i = tooltipItem.index;
                            var total = data2.datasets[0].data.reduce(function(previousValue, currentValue, currentIndex, array) {
                                return previousValue + currentValue;
                            });
                            var currentValue = data2.datasets[0].data[i];
                            var percentage = parseFloat((currentValue/total*100).toFixed(1));
                            return data2.labels[i] + ': ' + currentValue.toLocaleString() + ' files (' + percentage +'%)';
                        }
                    }
                },
                title: {
                    display: true,
                    text: 'Top File Types by Count'
                },
                maintainAspectRatio: false,
                responsive: true,
                onClick: function(event, clickedElements) {
                    if (clickedElements.length === 0) return;
                    var e = clickedElements[0];
                    var ext = this.data.labels[e._index];
                    //var size = this.data.datasets[0].data[e._index];
                    if (ext == "NULL (no ext)") {
                        ext = "\"\"";
                    }
                    var pp = encodeURIComponent(escapeHTML(decodeURIComponent(path)));
                    window.location.href = "search.php?submitted=true&p=1&q=extension:" + ext + " AND parent_path:" + pp + "*&doctype=file";
                    return false;
                },
                onHover: function (event, legendItem, legend) {
                    $("#topFileTypesByCount-pieChart").css("cursor", "pointer");
                },
                onLeave: function (event, legendItem, legend) {
                    $("#topFileTypesByCount-pieChart").css("cursor", "default");
                }
            }

            var topFileTypesByCountpieChart = new Chart(topFileTypesByCountpieChartCanvas, {
                type: 'doughnut',
                data: topFileTypespieData,
                options: topFileTypespieOptions
            })

            //--------------------
            //- END BAR/PIE EXT CHART -
            //--------------------


            //----------------
            //- STACKED BAR MTIME CHART -
            //----------------

            var datasets = []

            // get total size
            var totalsize = 0;
            for (var i in data3) {
                totalsize += data3[i].size;
            }

            for (var i in data3) {
                datasets.push({
                    label: data3[i].mtime,
                    data: [(data3[i].size / totalsize * 100).toFixed(1)],
                    size: data3[i].size,
                    backgroundColor: hot_cold_colors[i],
                    borderColor: '#2F3338'
                })
            }

            datasets.reverse();

            var mtimebarChartCanvas = $("#mtime-barChart")
            var mtimebarData = {
                labels: ['Last Modified'],
                datasets: datasets
            }
            var mtimebarOptions = {
                legend: {
                    display: true,
                    position: 'top',
                    labels: {
                        fontColor: '#C8C8C8'
                    },
                    onClick: function (event, legendItem, legend) {
                        var mtime = legendItem.text;
                        if (mtime == "0 - 30 days") {
                            mtime = "[now/m-1M/d TO now/m}"
                        } else if (mtime == "30 - 90 days") {
                            mtime = "[now/m-3M/d TO now/m-1M/d}"
                        } else if (mtime == "90 - 180 days") {
                            mtime = "[now/m-6M/d TO now/m-3M/d}"
                        } else if (mtime == "180 days - 1 year") {
                            mtime = "[now/m-1y/d TO now/m-6M/d}"
                        } else if (mtime == "1 - 2 years") {
                            mtime = "[now/m-2y/d TO now/m-1y/d}"
                        } else if (mtime == "> 2 years") {
                            mtime = "[* TO now/m-2y/d}"
                        }
                        var pp = encodeURIComponent(escapeHTML(decodeURIComponent(path)));
                        window.location.href = "search.php?submitted=true&p=1&q=mtime:" + mtime + " AND parent_path:" + pp + "*&sort=size&sortorder=desc&sort2=name&sortorder2=asc&doctype=file";
                        return false;
                    },
                    onHover: function (event, legendItem, legend) {
                        $("#mtime-barChart").css("cursor", "pointer");
                    },
                    onLeave: function (event, legendItem, legend) {
                        $("#mtime-barChart").css("cursor", "default");
                    }
                },
                tooltips: {
                    mode: 'single',
                    callbacks: {
                        label: function (tooltipItem, data3) {
                            var i = tooltipItem.datasetIndex;
                            var currentValue = data3.datasets[i].size
                            var percentage = parseFloat((currentValue/totalsize*100).toFixed(1));
                            return data3.datasets[i].label + ': ' + format(currentValue) + ' (' + percentage +'%)';
                        }
                    }
                },
                scales: {
                    xAxes: [{
                        display: true,
                        stacked: true,
                        gridLines: {
                            display: false
                        },
                        ticks: {
                            min: 0,
                            max: 100,
                            callback: function (value) {
                                return value + '%'
                            }
                        }
                    }],
                    yAxes: [{
                        display: false,
                        stacked: true,
                        gridLines: {
                            display: false
                        }
                    }]
                },
                title: {
                    display: true,
                    text: 'File Age by Size'
                },
                maintainAspectRatio: false,
                onClick: function(event, clickedElements) {
                    if (clickedElements.length === 0) return;
                    var activeElement = mtimebarChart.getElementAtEvent(event);
                    var mtime = this.data.datasets[activeElement[0]._datasetIndex].label;
                    if (mtime == "0 - 30 days") {
                        mtime = "[now/m-1M/d TO now/m}"
                    } else if (mtime == "30 - 90 days") {
                        mtime = "[now/m-3M/d TO now/m-1M/d}"
                    } else if (mtime == "90 - 180 days") {
                        mtime = "[now/m-6M/d TO now/m-3M/d}"
                    } else if (mtime == "180 days - 1 year") {
                        mtime = "[now/m-1y/d TO now/m-6M/d}"
                    } else if (mtime == "1 - 2 years") {
                        mtime = "[now/m-2y/d TO now/m-1y/d}"
                    } else if (mtime == "> 2 years") {
                        mtime = "[* TO now/m-2y/d}"
                    }
                    var pp = encodeURIComponent(escapeHTML(decodeURIComponent(path)));
                    window.location.href = "search.php?submitted=true&p=1&q=mtime:" + mtime + " AND parent_path:" + pp + "*&doctype=file";
                    return false;
                },
                onHover: function (event, legendItem, legend) {
                    $("#mtime-barChart").css("cursor", "pointer");
                },
                onLeave: function (event, legendItem, legend) {
                    $("#mtime-barChart").css("cursor", "default");
                }
            }

            var mtimebarChart = new Chart(mtimebarChartCanvas, {
                type: 'horizontalBar',
                data: mtimebarData,
                options: mtimebarOptions
            })

            //--------------------
            //- END STACKED BAR MTIME CHART -
            //--------------------

        }

    }

    /* ------- END SEARCH RESULTS CHARTS -------*/

});