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

$(function () {
    'use strict'

    var ticksStyle = {
        fontColor: '#495057',
        fontStyle: 'bold'
    }

    var mode = 'index'
    var intersect = true

    var default_colors = ['#3366CC', '#DC3912', '#FF9900', '#109618', '#990099', '#3B3EAC', '#0099C6', '#DD4477', '#66AA00', '#B82E2E', '#316395', '#994499', '#22AA99', '#AAAA11', '#6633CC', '#E67300', '#8B0707', '#329262', '#5574A6', '#3B3EAC']
    var hot_cold_colors = ["#00468B", "#3465CC", "#0099C6", "#FEFE22", "#FF9902", "#DC3912"]

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

    //----------------
    //- BAR/PIE EXT CHART -
    //----------------

    // trigger loader
    var spinner = new Spinner(opts).spin(document.getElementById('topFileTypes-Chart-container'));

    // load json data from Elasticsearch
    var data_url = 'd3_data_pie_ext_dashboard.php?usecache=' + usecache;
    d3.json(data_url, function (error, data) {
        // by size bar chart

        data = data.children;

        var top_ext_labels = []
        var top_ext_data_size = []
        var top_ext_data_size_count = []
        var top_ext_colors = []
        var top_ext_colors_border = []

        for (var i in data['top_extensions_bysize']) {
            var name = data['top_extensions_bysize'][i].name;
            if (name == '') {
                name = 'NULL (no ext)'
            }
            top_ext_labels.push(name)
            top_ext_data_size.push(data['top_extensions_bysize'][i].size)
            top_ext_data_size_count.push(data['top_extensions_bysize'][i].count)
            var c = default_colors[i]
            top_ext_colors.push(c)
            top_ext_colors_border.push('#2F3338')
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
                    label: function (tooltipItem, data) {
                        var i = tooltipItem.index;
                            var total = data.datasets[0].data.reduce(function(previousValue, currentValue, currentIndex, array) {
                                return previousValue + currentValue;
                            });
                            var currentValue = data.datasets[0].data[i];
                            var percentage = parseFloat((currentValue/total*100).toFixed(1));
                            var currentCount = top_ext_data_size_count[i];
                            return data.labels[i] + ': ' + format(currentValue) + ' (' + percentage +'%) (' + numberWithCommas(currentCount) + ' items)';
                    }
                }
            },
            scales: {
                xAxes: [{
                    ticks: {
                        // Format size in the ticks
                        callback: function(value, index, values) {
                            return format(value, '0');
                        }
                    }
                }]
            },
            title: {
                display: true,
                text: 'Top File Types by Size'
            },
            onClick: function(event, clickedElements) {
                if (clickedElements.length === 0) return;
                var e = clickedElements[0];
                var ext = this.data.labels[e._index];
                //var size = this.data.datasets[0].data[e._index];
                if (ext == "NULL (no ext)") {
                    ext = "\"\"";
                }
                var pp = encodeURIComponent(escapeHTML(decodeURIComponent(rootpath)));
                window.open("search.php?submitted=true&p=1&q=extension:" + ext + " AND parent_path:" + pp + "*&doctype=file&path=" + encodeURIComponent(rootpath));
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
        var top_ext_data_count_size = []
        var top_ext_colors = []
        var top_ext_colors_border = []

        // re-sort data by top count
        //data.sort((a, b) => (a.count > b.count) ? -1 : 1)

        for (var i in data['top_extensions_bycount']) {
            var name = data['top_extensions_bycount'][i].name;
            if (name == '') {
                name = 'NULL (no ext)'
            }
            top_ext_labels.push(name)
            top_ext_data_count.push(data['top_extensions_bycount'][i].count)
            top_ext_data_count_size.push(data['top_extensions_bycount'][i].size)
            var c = default_colors[i]
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
                    window.open("search.php?submitted=true&p=1&q=extension:" + ext + " AND parent_path:" + encodeURIComponent(escapeHTML(rootpath)) +"*&doctype=file&path=" + encodeURIComponent(rootpath));
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
                    label: function (tooltipItem, data) {
                        var i = tooltipItem.index;
                        var total = data.datasets[0].data.reduce(function(previousValue, currentValue, currentIndex, array) {
                            return previousValue + currentValue;
                        });
                        var currentValue = data.datasets[0].data[i];
                        var percentage = parseFloat((currentValue/total*100).toFixed(1));
                        var currentSize = top_ext_data_count_size[i];
                        return data.labels[i] + ': ' + currentValue.toLocaleString() + ' files (' + percentage +'%) (' + format(currentSize) + ')';
                    }
                }
            },
            title: {
                display: true,
                text: 'Top File Types by Count'
            },
            onClick: function(event, clickedElements) {
                if (clickedElements.length === 0) return;
                var e = clickedElements[0];
                var ext = this.data.labels[e._index];
                //var size = this.data.datasets[0].data[e._index];
                if (ext == "NULL (no ext)") {
                    ext = "\"\"";
                }
                var pp = encodeURIComponent(escapeHTML(decodeURIComponent(rootpath)));
                window.open("search.php?submitted=true&p=1&q=extension:" + ext + " AND parent_path:" + pp + "*&doctype=file&path=" + encodeURIComponent(rootpath));
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

        // stop spin.js loader
        spinner.stop();
    });

    //--------------------
    //- END BAR/PIE EXT CHART -
    //--------------------


    //----------------
    //- STACKED BAR MTIME CHART -
    //----------------

    // trigger loader
    var spinner2 = new Spinner(opts).spin(document.getElementById('mtime-Chart-container'));

    // load json data from Elasticsearch
    var data_url2 = 'd3_data_bar_mtime_dashboard.php?usecache=' + usecache;
    d3.json(data_url2, function (error, data) {

        data = data.children;
        
        var datasets = []

        // get total size
        var totalsize = 0;
        var totalcount = 0;
        for (var i in data) {
            totalsize += data[i].size;
            totalcount += data[i].count;
        }

        for (var i in data) {
            datasets.push({
                label: data[i].mtime,
                data: [(data[i].size / totalsize * 100).toFixed(1)],
                size: data[i].size,
                count: data[i].count,
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
                    window.open("search.php?submitted=true&p=1&q=mtime:" + mtime + " AND parent_path:" + encodeURIComponent(escapeHTML(rootpath)) +"* AND " + sizefield + ":>=" + filter + "&doctype=file&path=" + encodeURIComponent(rootpath));
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
                    label: function (tooltipItem, data) {
                        var i = tooltipItem.datasetIndex;
                        var currentValue = data.datasets[i].size;
                        var currentCount = data.datasets[i].count;
                        var percentage = parseFloat((currentValue/totalsize*100).toFixed(1));
                        return data.datasets[i].label + ': ' + format(currentValue) + ' (' + percentage +'%) (' + numberWithCommas(currentCount) + ' items)';
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
                        callback: function(value) {
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
                var pp = encodeURIComponent(escapeHTML(decodeURIComponent(rootpath)));
                window.open("search.php?submitted=true&p=1&q=mtime:" + mtime + " AND parent_path:" + pp + "* AND " + sizefield + ":>=" + filter + "&doctype=file&path=" + encodeURIComponent(rootpath));
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

        // stop spin.js loader
        spinner2.stop();
    });

    //--------------------
    //- END STACKED BAR MTIME CHART -
    //--------------------

})