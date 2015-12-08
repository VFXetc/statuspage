
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
};

function colorThreshold(v, values) {
    for (var i = values.length - 1; i >= 0; i--) {
        if (v > values[i][0]) {
            return values[i][1]
        }
    }
}


jQuery(function($) {


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

    var rows = {};

    var event_source = new EventSource('/events');

    event_source.onmessage = function(e) {

        var msg = JSON.parse(e.data);
        console.log(msg);
        
        var row = rows[msg.host];
        if (!row) {

            var tr = $('<tr>\
                <td class="name">\
                <td class="load1">\
                <td class="load5">\
                <td class="load15">\
                <td class="net_r">\
                <td class="net_w">\
                <td class="disk_r">\
                <td class="disk_w">\
            </tr>')
                .attr('host', msg.host)
                .appendTo('#mainTable tbody');

            $('#mainTable tbody tr').sort(function (a, b) {
                return aton($(a).attr('host')) < aton($(b).attr('host')) ? -1 : 1;
            }).appendTo('#mainTable tbody');


            row = {
                tr: tr,
                name:   tr.find('.name'),
                load1:  tr.find('.load1'),
                load5:  tr.find('.load5'),
                load15: tr.find('.load15'),
                net_r:  tr.find('.net_r'),
                net_w:  tr.find('.net_w'),
                disk_r: tr.find('.disk_r'),
                disk_w: tr.find('.disk_w')
            };
            rows[msg.host] = row;
        }

        row.name.text(msg.name);
        row.load1.text(msg.load[0]);
        row.load1.css({backgroundColor: colorThreshold(msg.load[0], load_colors)})
        row.load5.text(msg.load[1]);
        row.load5.css({backgroundColor: colorThreshold(msg.load[1], load_colors)})
        row.load15.text(msg.load[2]);
        row.load15.css({backgroundColor: colorThreshold(msg.load[2], load_colors)})

        row.net_r.text(bytesToSize(msg.net.bytes_recv) + '/s');
        row.net_r.css({backgroundColor: colorThreshold(msg.net.bytes_recv, net_colors)})
        row.net_w.text(bytesToSize(msg.net.bytes_sent) + '/s');
        row.net_w.css({backgroundColor: colorThreshold(msg.net.bytes_sent, net_colors)})
        row.disk_r.text(bytesToSize(msg.disk.read_bytes) + '/s');
        row.disk_r.css({backgroundColor: colorThreshold(msg.disk.read_bytes, net_colors)})
        row.disk_w.text(bytesToSize(msg.disk.write_bytes) + '/s');
        row.disk_w.css({backgroundColor: colorThreshold(msg.disk.write_bytes, net_colors)})
    }


});
