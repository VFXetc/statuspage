jQuery(function($) {

    console.log("hello");

    var charts = {};

    var event_source = new EventSource('/events');

    event_source.onmessage = function(e) {

        var msg = JSON.parse(e.data);
        console.log(msg);

        var chart = charts[msg.host];
        if (!chart) {
            var $div = $('<div class="chart" />').appendTo('body');
            var loadavg = [[], [], []];
            var the_chart = new CanvasJS.Chart($div[0], {
                title: {
                    text: msg.host
                },          
                data: [{
                    type: "area",
                    dataPoints: loadavg[0],
                    fillOpacity: 0.2
                }, {
                    type: "area",
                    dataPoints: loadavg[1],
                    fillOpacity: 0.2
                }, {
                    type: "area",
                    dataPoints: loadavg[2],
                    fillOpacity: 0.2
                }]
            });

            var chart = {
                div: $div,
                chart: the_chart,
                loadavg: loadavg,
            };
            charts[msg.host] = chart;
        }

        for (var i = 0; i < 3; i++) {
            var dps = chart.loadavg[i];
            dps.push({
                x:msg.time,
                y:msg.loadavg[i],
            });
            if (dps.length > 300) {
                dps.shift();
            }
        }

        chart.chart.render();

    }


});
