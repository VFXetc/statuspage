
function aton(ip){
    var a = ip.split('.');
    var x = (
        (parseInt(a[0]) << 24) + 
        (parseInt(a[1]) << 16) + 
        (parseInt(a[2]) << 8) + 
        (parseInt(a[3]))
    )
    return x;
}


function bytesToSize(bytes) {
    var sizes = [' B', 'kB', 'MB', 'GB', 'TB'];
    if (bytes == 0) return '   0 B';
    var i = parseInt(Math.floor(Math.log(bytes) / Math.log(1024)));
    var n = Math.round(bytes / Math.pow(1024, i), 2);
    var s = n.toString();
    var p = '    '
    return p.substring(0, p.length - s.length) + s + '' + sizes[i];
}

function bytesToRate(bytes) {
    return bytesToSize(bytes) + '/s'
}

function colorThreshold(v, values) {
    for (var i = values.length - 1; i >= 0; i--) {
        if (v > values[i][0]) {
            return values[i][1]
        }
    }
}


var cpu_colors = [
    [0, ''],
    [0.01, '#dfd'],
    [0.25, '#bfb'],
    [0.75, '#ffb'],
    [0.95, '#faa'],
]

var load_colors = [
    [0, ''],
    [1, '#dfd'],
    [2, '#bfb'],
    [10, '#ffb'],
    [20, '#faa'],
]

var net_colors = [
    [0, ''],
    [1024, '#dfd'],
    [1024 * 100, '#bfb'],
    [1024 * 1024, '#ffb'],
    [1024 * 1024 * 10, '#faa'],
]


var format_percent = function(x) {
    return Math.floor(100 * x) + '%'
}

var FORMATTERS = [

    {key: 'hostname'},

    {key: 'cpu_min', colors: cpu_colors, format: format_percent, get: function(msg) { return Math.min.apply(null, msg.cpu_percent) }},
    {key: 'cpu_avg', colors: cpu_colors, format: format_percent, get: function(msg) { return msg.cpu_percent.reduce(function (a, b) { return a + b }) / msg.cpu_percent.length }},
    {key: 'cpu_max', colors: cpu_colors, format: format_percent, get: function(msg) { return Math.max.apply(null, msg.cpu_percent) }},
    {key: 'cpu_count', get: function(msg) { return msg.cpu_percent.length }},

    {key: 'mem_used',   format: bytesToSize, "class": "section-start"},
    {key: 'mem_used_p', get: function(msg) { return msg.mem_used / msg.mem_total },
        format: format_percent,
        colors: cpu_colors
    },
    {key: 'mem_total',  format: bytesToSize},

    {key: 'swap_used',  format: bytesToSize, "class": "section-start"},
    {key: 'swap_total', format: bytesToSize},

    {key: 'net_bytes_recv',   format: bytesToRate, colors: net_colors, "class": "section-start"},
    {key: 'net_bytes_sent',   format: bytesToRate, colors: net_colors},

    {key: 'disk_read_bytes',  format: bytesToRate, colors: net_colors, "class": "section-start"},
    {key: 'disk_read_time',   colors: cpu_colors, get: function(msg) { return msg.disk_read_time / 1000 }, format: format_percent},
    {key: 'disk_write_bytes', format: bytesToRate, colors: net_colors},
    {key: 'disk_write_time',  colors: cpu_colors, get: function(msg) { return msg.disk_write_time / 1000 }, format: format_percent},

    {key: 'nfs_lookup', "class": "section-start"},
    {key: 'nfs_readdir'},
    {key: 'nfs_fsstat'},
    {key: 'nfs_access'},
    {key: 'nfs_read'},
    {key: 'nfs_write'},

]


jQuery(function($) {

    // Setup headers
    $.each(FORMATTERS, function(i, spec) {
        var td = $('#column-headers td.' + spec.key)
        if (!td.length) {
            td = $('<td />')
                .addClass(spec.key)
                .text(spec.title || spec.key)
                .appendTo('#column-headers')
        }
    })


    var rows = {};

    var event_source = new EventSource('/events');

    event_source.onmessage = function(e) {

        var sep = e.data.indexOf(" ")
        var host = e.data.substr(0, sep);
        var msg = JSON.parse(e.data.substr(sep + 1))

        var row = rows[host];

        if (row === undefined) {

            row = {}
            rows[host] = row

            var tr = $('<tr>\
                <td class="hostname">\
                <td class="load_average_1 section-start"></td>\
                <td class="load_average_5"></td>\
                <td class="load_average_15"></td>\
            </tr>')
                .attr('host', host)
            
            row.tr = tr
            row.tds = {}

            // Create missing elements.
            $.each(FORMATTERS, function(i, spec) {
                var td = tr.find('td.' + spec.key);
                if (!td.length) {
                    td = $('<td />').addClass(spec.key).appendTo(tr);
                    if (spec["class"]) {
                        td.addClass(spec["class"])
                    }
                }
                row.tds[spec.key] = td;
            })

            // Fetch handled rows.
            row.load1 = tr.find('.load_average_1')
            row.load5 = tr.find('.load_average_5')
            row.load15 = tr.find('.load_average_15')

            // Put it into the body, and sort it.
            tr.appendTo('#main-table tbody');
            $('#main-table tbody tr').sort(function (a, b) {
                return aton($(a).attr('host')) < aton($(b).attr('host')) ? -1 : 1;
            }).appendTo('#main-table tbody');

        }

        // Format them all.
        $.each(FORMATTERS, function(i, spec) {
            var td = row.tds[spec.key];
            var value = spec.get ? spec.get(msg) : msg[spec.key];
            if (value === undefined) {
                return
            }
            var formatted = spec.format ? spec.format(value) : value;
            td.text(formatted)
            if (spec.colors) {
                td.css({backgroundColor: colorThreshold(value, spec.colors)})
            }
        })

        row.load1.text(msg.load_average[0].toFixed(2));
        row.load1.css({backgroundColor: colorThreshold(msg.load_average[0], load_colors)})
        row.load5.text(msg.load_average[1].toFixed(2));
        row.load5.css({backgroundColor: colorThreshold(msg.load_average[1], load_colors)})
        row.load15.text(msg.load_average[2].toFixed(2));
        row.load15.css({backgroundColor: colorThreshold(msg.load_average[2], load_colors)})

    }


});
