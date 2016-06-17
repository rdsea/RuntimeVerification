
    var treeFocused = false
    // Calculate total nodes, max label length
    var totalNodes = 0;
    var maxLabelLength = 0;
    // variables for drag/drop
    var selectedNode = null;
    var draggingNode = null;
    // panning variables
    var panSpeed = 200;
    var panBoundary = 20; // Within 20px from edges will pan when dragging.
    // Misc. variables
    var i = 0;
    var duration = 1;
    var root;

    function drawTree(json, tree_container_id, viewerWidth, viewerHeight){

    //if tree SVG in focus, do not redraw
    if (treeFocused){
      return
    }

    treeData = json


    var tree = d3.layout.tree()
        .size([viewerHeight, viewerWidth]);

    // define a d3 diagonal projection for use by the node paths later on.
    var diagonal = d3.svg.diagonal()
        .projection(function(d) {
            return [d.y, d.x];
        });

    // A recursive helper function for performing some setup by walking through all nodes

    function visit(parent, visitFn, childrenFn) {
        if (!parent) return;

        visitFn(parent);

        var children = childrenFn(parent);
        if (children) {
            var count = children.length;
            for (var i = 0; i < count; i++) {
                visit(children[i], visitFn, childrenFn);
            }
        }
    }

    // Call visit function to establish maxLabelLength
    visit(treeData, function(d) {
        totalNodes++;
        maxLabelLength = Math.max(d.name.length, maxLabelLength);

    }, function(d) {
        return d.containedUnits && d.containedUnits.length > 0 ? d.containedUnits : null;
    });


    // sort the tree according to the node names

    function sortTree() {
        tree.sort(function(a, b) {
            if (a.type == 'Test' && b.type != 'Test'){
               return -1;
            }else{
                return b.name.toLowerCase() < a.name.toLowerCase() ? 1 : -1;
            }
        });
    }
    // Sort the tree initially incase the JSON isn't in a sorted order.
    sortTree();

    // TODO: Pan function, can be better implemented.

    function pan(domNode, direction) {
        var speed = panSpeed;
        if (panTimer) {
            clearTimeout(panTimer);
            translateCoords = d3.transform(svgGroup.attr("transform"));
            if (direction == 'left' || direction == 'right') {
                translateX = direction == 'left' ? translateCoords.translate[0] + speed : translateCoords.translate[0] - speed;
                translateY = translateCoords.translate[1];
            } else if (direction == 'up' || direction == 'down') {
                translateX = translateCoords.translate[0];
                translateY = direction == 'up' ? translateCoords.translate[1] + speed : translateCoords.translate[1] - speed;
            }
            scaleX = translateCoords.scale[0];
            scaleY = translateCoords.scale[1];
            scale = zoomListener.scale();
            svgGroup.transition().attr("transform", "translate(" + translateX + "," + translateY + ")scale(" + scale + ")");
            d3.select(domNode).select('g.node').attr("transform", "translate(" + translateX + "," + translateY + ")");
            zoomListener.scale(zoomListener.scale());
            zoomListener.translate([translateX, translateY]);
            panTimer = setTimeout(function() {
                pan(domNode, speed, direction);
            }, 50);
        }
    }

    // Define the zoom function for the zoomable tree

    function zoom() {
        svgGroup.attr("transform", "translate(" + d3.event.translate + ")scale(" + d3.event.scale + ")");
    }


    // define the zoomListener which calls the zoom function on the "zoom" event constrained within the scaleExtents
    var zoomListener = d3.behavior.zoom().scaleExtent([0.1, 3]).on("zoom", zoom);

    function initiateDrag(d, domNode) {
        draggingNode = d;
        d3.select(domNode).select('.ghostCircle').attr('pointer-events', 'none');
        d3.selectAll('.ghostCircle').attr('class', 'ghostCircle show');
        d3.select(domNode).attr('class', 'node activeDrag');

        svgGroup.selectAll("g.node").sort(function(a, b) { // select the parent and sort the path's
            if (a.id != draggingNode.id) return 1; // a is not the hovered element, send "a" to the back
            else return -1; // a is the hovered element, bring "a" to the front
        });
        // if nodes has children, remove the links and nodes
        if (nodes.length > 1) {
            // remove link paths
            links = tree.links(nodes);
            nodePaths = svgGroup.selectAll("path.link")
                .data(links, function(d) {
                    return d.target.id;
                }).remove();
            // remove child nodes
            nodesExit = svgGroup.selectAll("g.node")
                .data(nodes, function(d) {
                    return d.id;
                }).filter(function(d, i) {
                    if (d.id == draggingNode.id) {
                        return false;
                    }
                    return true;
                }).remove();
        }

        // remove parent link
        parentLink = tree.links(tree.nodes(draggingNode.parent));
        svgGroup.selectAll('path.link').filter(function(d, i) {
            if (d.target.id == draggingNode.id) {
                return true;
            }
            return false;
        }).remove();

        dragStarted = null;
    }

    // define the baseSvg, attaching a class for styling and the zoomListener
    d3.select("#" + tree_container_id).selectAll("svg").remove()

    var tooltip = d3.select("#" + tree_container_id)
	.append("div")
    .attr('class', 'nodeText')
	.style("position", "absolute")
	.style("background-color", "white")
	.style("z-index", "10")
	.style("visibility", "hidden")
	.attr('id', 'TOOLTIP_DIV')
	.html("a simple tooltip");


    var baseSvg =  d3.select("#" + tree_container_id).append("svg")
        .attr("width", viewerWidth)
        .attr("height", viewerHeight)
        .attr("class", "overlay")
        .call(zoomListener)
        .on("mouseover", function(d){ treeFocused = true})
        .on("mouseout", function(d){ treeFocused = false});


    // Helper functions for collapsing and expanding nodes.

    function collapse(d) {
        if (d.containedUnits) {
            d._containedUnits = d.containedUnits;
            d._containedUnits.forEach(collapse);
            d.containedUnits = null;
        }
    }

    function expand(d) {
        if (d._containedUnits) {
            d.containedUnits = d._containedUnits;
            d.containedUnits.forEach(expand);
            d._containedUnits = null;
        }
    }


    // Function to update the temporary connector indicating dragging affiliation
    var updateTempConnector = function() {
        var data = [];
        if (draggingNode !== null && selectedNode !== null) {
            // have to flip the source coordinates since we did this for the existing connectors on the original tree
            data = [{
                source: {
                    x: selectedNode.y0,
                    y: selectedNode.x0
                },
                target: {
                    x: draggingNode.y0,
                    y: draggingNode.x0
                }
            }];
        }
        var link = svgGroup.selectAll(".templink").data(data);

        link.enter().append("path")
            .attr("class", "templink")
            .attr("d", d3.svg.diagonal())
            .attr('pointer-events', 'none');

        link.attr("d", d3.svg.diagonal());

        link.exit().remove();
    };

    // Function to center node when clicked/dropped so node doesn't get lost when collapsing/moving with large amount of children.

    function centerNode(source) {
        scale = zoomListener.scale();
        x = -source.y0;
        y = -source.x0;
        x = x +10 ;
        y = y * scale + viewerHeight / 2;
        d3.select('g').transition()
            .duration(duration)
            .attr("transform", "translate(" + x + "," + y + ")scale(" + scale + ")");
        zoomListener.scale(scale);
        zoomListener.translate([x, y]);
    }

    // Toggle children function

    function toggleChildren(d) {
        if (d.containedUnits) {
            d._containedUnits = d.containedUnits;
            d.containedUnits = null;
        } else if (d._containedUnits) {
            d.containedUnits = d._containedUnits;
            d._containedUnits = null;
        }
        return d;
    }

    // Toggle children on click.

    function click(d) {
        if (d3.event.defaultPrevented) return; // click suppressed
        d = toggleChildren(d);
        update(d);
        centerNode(d);
    }

    function update(source) {
        // Compute the new height, function counts total children of root node and sets tree height accordingly.
        // This prevents the layout looking squashed when new nodes are made visible or looking sparse when nodes are removed
        // This makes the layout more consistent.
        var levelWidth = [1];
        var childCount = function(level, n) {

            if (n.containedUnits && n.containedUnits.length > 0) {
                if (levelWidth.length <= level + 1) levelWidth.push(0);

                levelWidth[level + 1] += n.containedUnits.length;
                n.containedUnits.forEach(function(d) {
                    childCount(level + 1, d);
                });
            }
        };
        childCount(0, root);
        var newHeight = d3.max(levelWidth) * (maxLabelLength * 40); // 25 pixels per line
        tree = tree.size([newHeight, viewerWidth]);

        // Compute the new tree layout.
        var nodes = tree.nodes(root).reverse(),
            links = tree.links(nodes);

        // Set widths between levels based on maxLabelLength.
        nodes.forEach(function(d) {
            if (d.parent){
                lengthToParent = 0
                parent = d
                while (parent.parent){
                  parent = parent.parent
                  lengthToParent = lengthToParent +  d.parent.name.length
                }
                if (d.parent.y == 0 ){
                   d.y = (d.parent.name.length * 10); //maxLabelLength * 10px
//                #need to rewrite below to make tests appear somewhere else in tree
                }else if (d.type == 'Test' ){
                   d.y = d.parent.y;// - Math.abs(maxLabelLength - d.parent.name.length) * 10;
                }
                else {
                   d.y = d.parent.y; //maxLabelLength * 10px}
                }
              }else{
                d.y = 0; //maxLabelLength * 10px
              }
            // alternatively to keep a fixed scale one can set a fixed depth per level
            // Normalize for fixed-depth by commenting out below line
            // d.y = (d.depth * 500); //500px per level.
        });

        // Update the nodes…
        node = svgGroup.selectAll("g.node")
            .data(nodes, function(d) {
                return d.id || (d.id = ++i);
            });

        // Enter any new nodes at the parent's previous position.
        var nodeEnter = node.enter().append("g")
            .attr("class", "node")
            .attr("transform", function(d) {
                return "translate(" + source.y0 + "," + source.x0 + ")";
            })
            .on('click', click)
            .on("mouseover", function(d){
                 if(d.type=="Test"){
                    var html = []
                    html.push("<p>");
                    html.push("TestName: " + d.name);
                    html.push("Details: ");
                    html.push(d.details.replace(/</g,'').replace(/>/g,''));
                    html.join("<br/>");
                    html.push("Timestamp: ");
                    html.push(d.timestamp);
                    html.push("</p>");
                    tooltip.html(html);
                    return tooltip.style("visibility", "visible");
                 }else{
                    var html = []
                    html.push("<p>");
                    html.push("UnitID: " + d.name);
                    if(d.uuid){
                        html.push("UnitUUID: " + d.uuid);
                    }
                    html.join("<br/>");
                    html.push("</p>");
                    tooltip.html(html);
                    return tooltip.style("visibility", "visible");
                 }
                })
	        .on("mousemove", function(){
	            return tooltip.style("top", (event.pageY + 10)+"px").style("left",(event.pageX+10)+"px");})
	        .on("mouseout", function(){
	            return tooltip.style("visibility", "hidden");});

        nodeEnter.append("circle")
            .attr('class', 'nodeCircle')
            .attr("r", 0)
            .style("fill", function(d) {
                return d._containedUnits ? "lightsteelblue" : "#fff";
            });

        nodeEnter.append("svn:image")
            .attr("xlink:href", function(d) {
                if (d.type == "VirtualMachine") {
                    return "./static/img/vm.png";
                } else if (d.type == "PhysicalMachine") {
                    return "./static/img/pm.png";
                } else if (d.type == "Gateway") {
                    return "./static/img/gateway.png";
                } else if (d.type == "PhysicalDevice") {
                    return "./static/img/device.png";
                } else if (d.type == "Service") {
                    return "./static/img/service.png";
                } else if (d.type == "Process") {
                    return "./static/img/process.png";
                }else if (d.type == "Test"){
                  return "./static/img/test.png";
                } else {
                   return null;
                }
            })
            .attr("width", 20)
            .attr("height", 20)
            .attr("x", -10)
            .attr("y", -10);



//
//        nodeEnter.append("text")
//            .attr("y", function(d) {
//                return d.containedUnits || d._containedUnits? -10 : -10;
//            })
//            .attr("dy", ".35em")
//            .attr('class', 'nodeText')
//            .attr("text-anchor", function(d) {
//                return d.containedUnits || d._containedUnits ? "start" : "start";
//            })
//            .text(function(d) {
//                return d.name;
//            })
//            .style("fill-opacity", 0);


        // phantom node to give us mouseover in a radius around it
        nodeEnter.append("circle")
            .attr('class', 'ghostCircle')
            .attr("r", 30)
            .attr("opacity", 0.2) // change this to zero to hide the target area
            .style("fill", "red")
            .attr('pointer-events', 'mouseover');

        nodeEnter.append("foreignObject")
        .attr('class', 'nodeText')
        .attr("dy", ".35em")
        .style("color",function(d){
         if(d.type=="Test" ){
            if (d.successful){
              return "green"
            }else{
              return "red"
            }
          }else{
             return "black"
          }
          }
        )
        .attr("width", function(d) {
            var html = []
            html.push(d.name)
            if(d.uuid){
              html.push(d.uuid)
            }
            //width of max line by 10 pixels each char
            max = html[0].length
            for (s in html) {
              if (max < s.length){
                max = s.length
               }
            }
            return max * 20;
        })
        .attr("height", "120")
        .attr("transform", function(d) {
            var html = d.name.split(".");
            return  "translate(10,-10)" // + (html.length * 20) + ")"
        })
        .html(function(d) {
            var html = []
            html.push(d.name)
            if(d.uuid){
              html.push(d.uuid)
            }

            return html.join("<br/>");
        });

//
//        // Update the text to reflect whether node has children or not.
//        node.select('text')
//            .attr("y", function(d) {
//                return d.containedUnits || d.containedUnits ? -10 : -10;
//            })
//            .attr("text-anchor", function(d) {
//                return d.containedUnits || d.containedUnits ? "start" : "start";
//            })
//            .text(function(d) {
//                return d.name;
//            });


        // Change the circle fill depending on whether it has children and is collapsed
        node.select("circle.nodeCircle")
            .attr("r", 4.5)
            .style("fill", function(d) {
                return d._containedUnits ? "lightsteelblue" : "#fff";
            });

        // Transition nodes to their new position.
        var nodeUpdate = node.transition()
            .duration(duration)
            .attr("transform", function(d) {
                return "translate(" + d.y + "," + d.x + ")";
            });

        // Fade the text in
        nodeUpdate.select("text")
            .style("fill-opacity", 1);

        // Transition exiting nodes to the parent's new position.
        var nodeExit = node.exit().transition()
            .duration(duration)
            .attr("transform", function(d) {
                return "translate(" + source.y + "," + source.x + ")";
            })
            .remove();

        nodeExit.select("circle")
            .attr("r", 0);

        nodeExit.select("text")
            .style("fill-opacity", 0);

        // Update the links…
        var link = svgGroup.selectAll("path.link")
            .data(links, function(d) {
                return d.target.id;
            });

        // Enter any new links at the parent's previous position.
        link.enter().insert("path", "g")
            .attr("class", "link")
            .attr("d", function(d) {
                var o = {
                    x: source.x0,
                    y: source.y0
                };
                return diagonal({
                    source: o,
                    target: o
                });
            });

        // Transition links to their new position.
        link.transition()
            .duration(duration)
            .attr("d", diagonal);

        // Transition exiting nodes to the parent's new position.
        link.exit().transition()
            .duration(duration)
            .attr("d", function(d) {
                var o = {
                    x: source.x,
                    y: source.y
                };
                return diagonal({
                    source: o,
                    target: o
                });
            })
            .remove();

        // Stash the old positions for transition.
        nodes.forEach(function(d) {
            d.x0 = d.x;
            d.y0 = d.y;
        });

        function wrap(text, width) {
          text.each(function() {
            var text = d3.select(this),
                words = text.text().split(/\s+/).reverse(),
                word,
                line = [],
                lineNumber = 0,
                lineHeight = 1.1, // ems
                y = text.attr("y"),
                dy = parseFloat(text.attr("dy")),
                tspan = text.text(null).append("tspan").attr("x", 0).attr("y", y).attr("dy", dy + "em");
            while (word = words.pop()) {
              line.push(word);
              tspan.text(line.join(" "));
              if (tspan.node().getComputedTextLength() > width) {
                line.pop();
                tspan.text(line.join(" "));
                line = [word];
                tspan = text.append("tspan").attr("x", 0).attr("y", y).attr("dy", ++lineNumber * lineHeight + dy + "em").text(word);
              }
      }
   });



}


    }

    // Append a group which holds all nodes and which the zoom Listener can act upon.
    var svgGroup = baseSvg.append("g");

    // Define the root
    root = treeData;
    root.x0 = viewerHeight / 2;
    root.y0 = 0;

    // Layout the tree initially and center on the root node.
    update(root);
    centerNode(root);

    }