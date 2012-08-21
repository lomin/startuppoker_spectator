/**
 * User: nross
 */
var w = 1600,
    h = 650;

var svg = null,
	yAxisGroup = null,
	xAxisGroup = null,
	dataCirclesGroup = null,
	dataLinesGroup = null;

function draw(data) {
    data = data['standings'];
	var margin = 40;

    var min_max = function(f) {
        var accessor  = function (history) { return history['credits']; };
        return f(_.map(data, function(player) {
                    return f(player['history'], accessor);
                }), accessor)['credits'];
    }
	var x_max = d3.max(data, function(d,i) {
                                return _.max(d['history'], function(history){ return history['hands']; });
                            })['hands'];
	var y_max = min_max(_.max);
	var y_min = min_max(_.min);
	
    console.log(y_min);
    console.log(y_max);

	var x = d3.scale.linear().range([0, w - margin * 2]).domain([0, x_max]);
	var y = d3.scale.linear().range([h - margin * 2, 0]).domain([y_min, y_max]);

	var xAxis = d3.svg.axis().scale(x).tickSize(h - margin * 2).tickPadding(10).ticks(8);
	var yAxis = d3.svg.axis().scale(y).orient('left').tickSize(-w + margin * 2).tickPadding(10);

		svg = d3.select('#chart')
			.append('svg:svg')
				.attr('width', w)
				.attr('height', h)
			.append('svg:g')
				.attr('transform', 'translate(' + margin + ',' + margin + ')');


		yAxisGroup = svg.append('svg:g')
			.attr('class', 'yTick')
			.call(yAxis);

		xAxisGroup = svg.append('svg:g')
			.attr('class', 'xTick')
			.call(xAxis);

	var line = d3.svg.line()
		.x(function(d,i) { 
			return x(d['hands']); 
		})
		.y(function(d,i) {
			return y(d['credits']); 
		})
		.interpolate("basis");

    _.each(data,
            function(player) {
                var name = player['name'];
                svg.append('svg:g').selectAll(name)
                .data([player['history']]).enter().append('path')
                .attr('class', 'data-line ' + name)
                .attr("d", line(player['history']));
            });
		// .attr('class', function(d,i) {
         //       return d['players'][i]['name'];
          //  })

}


function generateData() {
	var d = [{'value': 0, 'hand': 0}];
    var i = 0;
	var max = 100;

	while (i++ < max) {
        var val = Math.round(Math.random()*10-5);
		d.push({'value' : d[i-1]['value'] + val , 'hand' : i});
	}
	return d;
}


