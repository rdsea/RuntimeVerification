            var simpleComponentIcon = "m 5,10 c 1.7265,0.251 5.7035,0.0355 4.8055,2.6145 -0.9305,2.0335 -3.066,3.827 0.214,4.8855 1.9925,0.6435 10.717,1.143 9.7905,-2.5835 -1.1255,-1.2255 -2.5535,-2.4125 -1.2315,-4.0245 2.8935,-0.552 5.8135,-0.9665 8.747,-1.2365 2.779,-0.2555 5.01138,-0.3785 7.80388,-0.3535 0,0 0.0342,-28.8233 0,-28.782 l -42.17988,0 c -0.7375,3.8525 -0.9175,8.9665 1.1535,10.61 3.0355,1.834 7.6995,-3.225 9.5015,0.7885 1.384,3.0825 -0.1075,8.324 -4.242,6.515 -4.9185,-2.1525 -7.189,0.88 -6.7055,6.19 0.1545,1.6955 0.472,3.214 0.701,4.702 3.891,-0.081 7.791,0.114 11.642,0.6745 z";

            var complexComponentIcon = "m -10,0 c 3.73224,-0.7459 8.66496,-0.9953 8.05062,0.63028 l -0.81288,2.33051 c 0.0832,1.10156 6.73944,1.38304 6.33894,-0.31885 0,0 -1.18264,-2.45972 -0.99342,-2.50527 -0.0569,-0.88313 8.32576,-0.86545 8.32576,-0.86545 0.78063,1.41974 -0.96421,4.29648 -0.50291,5.19887 1.09973,2.15125 4.95457,0.51254 5.20531,0.70421 0.63103,0.48237 0.96734,3.49919 -0.33288,3.38175 -2.20415,-0.19909 -6.72157,-1.93952 -4.27491,6.24781 l 21.61861,0.3644 -0.33114,-16.07925 c -2.69909,-0.38953 -8.50495,0.33626 -8.33363,1.04589 0.94358,3.90859 -2.59923,4.22934 -5.08229,3.00142 -0.66963,-0.36714 0.47037,-2.20109 0.10252,-2.99309 -0.78827,-1.28418 -3.69368,-0.8065 -8.16329,-0.96312 0,0 -0.70958,-4.82833 -0.42575,-5.05608 2.19333,-0.41775 5.58828,0.77701 5.69185,-2.38338 0.29332,-2.55231 -2.1638,-2.06746 -4.59029,-1.46068 -1.2562,0.31413 -1.57753,-3.06109 -1.19597,-5.67595 l -20.34134,0.0911 0.0473,30.38204 42.43301,-0.1822 0.18922,-30.29094 -22.42279,0";

            var warningTriangle = "m -25,10 11.66727,-22.45064 11.66726,22.45064 z";
            var sphere = "m 0,0 a 10.253048,9.8994951 0 1 1 -4e-5,-0.003";
            var octogon = "m 0,-5 6.63341,-7.14443 11.95156,0 6.46184,7.14443 0,8.97271 -6.46184,6.58185 -11.95156,0 -6.63341,-6.58185 z";
            var auxRect = "m -32,5 0,-13.25825 30.14043,0 0,13.25825 z"

            var margin = {top: 10, right: 0, bottom: 20, left: 10}
            var width;

            var opts = {
                lines: 20, // The number of lines to draw
                length: 7, // The length of each line
                width: 10, // The line thickness
                radius: 100, // The radius of the inner circle
                corners: 1, // Corner roundness (0..1)
                rotate: 0, // The rotation offset
                color: '#000', // #rgb or #rrggbb
                speed: 1, // Rounds per second
                trail: 60, // Afterglow percentage
                shadow: false, // Whether to render a shadow
                hwaccel: false, // Whether to use hardware acceleration
                className: 'spinner', // The CSS class to assign to the spinner
                zIndex: 2e9, // The z-index (defaults to 2000000000)
                top: 'auto', // Top position relative to parent in px
                left: 'auto', // Left position relative to parent in px
                visibility: true
            };
 
            var tree;

            var diagonal;

            var vis;

            var height;
             var i;
             var duration;
             var depth ;

                    
                    
            function contains(containedUnits, child) {
                for (var index = 0; index < containedUnits.length; index++) {
                    if (containedUnits[index].name == child.name) {
                        return 0;
                    }
                }
                return -1;
            }

            function updateTextOnNode(node, new_root, change) {

                if (node.actionName || new_root.actionName) {
                    //node.name = new_root.name + ": " + new_root.actionName;
                    node.attention = new_root.attention;
                    node.actionName = new_root.actionName;
                }

                node.name = new_root.name;
                if (!node.containedUnits) {
                    node.containedUnits = [];
                }


                //check if some new nodes have appeared
                if (node.containedUnits.length < new_root.containedUnits.length) {
                    //for all new containedUnits
                    for (var index = 0; index < new_root.containedUnits.length; index++) {
                        //if the containedUnits are not metrics
                        if (new_root.containedUnits[index].type.match(/SERVIC.*|V.*/g)) {
                            //if new root child DOES NOT ALLREADY EXIST
                            if (contains(node.containedUnits, new_root.containedUnits[index]) == -1) {
                                node.containedUnits.push(new_root.containedUnits[index]);
                                update(node);
                                change = 0;
                            }
                        }
                    }
                }

                //check if nodes need to be removed
                if (node.containedUnits.length > new_root.containedUnits.length) {
                    for (var index = 0; index < node.containedUnits.length; index++) {
                        if (node.containedUnits[index].type.match(/SERVIC.*|V.*/g)) {
                            if (contains(new_root.containedUnits, node.containedUnits[index]) == -1) {
                                node.containedUnits.splice(index, 1);
                                change = 0;
                            }
                        }
                    }
                }

                //remove all metrics, requirements and conditions so that they can be updated
                for (var index = 0; index < node.containedUnits.length; index++) {
                    var oldEntry = node.containedUnits[index];
                    if (!oldEntry.type.match(/SERVIC.*|V.*/g)) {
                        node.containedUnits.splice(index, 1);
                        //start over
                        index = -1;
                    }
                }


                //add all new metrics so that they can be updated
                for (var index = 0; index < new_root.containedUnits.length; index++) {
                    var newEntry = new_root.containedUnits[index];
                    if (!newEntry.type.match(/SERVIC.*|V.*/g)) {
                        node.containedUnits.push(newEntry);
                    }
                }

                //update all containedUnits not metrics
                for (var index = 0; index < node.containedUnits.length; index++) {
                    var oldEntry = node.containedUnits[index];
                    if (oldEntry.type.match(/SERVIC.*|V.*/g)) {
                        //find the element int the new containedUnits that matches this
                        for (var indexNew = 0; indexNew < new_root.containedUnits.length; indexNew++) {
                            var newEntry = new_root.containedUnits[indexNew];
                            if (newEntry.type.match(/SERVIC.*|V.*/g)) {
                                if (oldEntry.name == newEntry.name) {
                                    updateTextOnNode(oldEntry, newEntry);
                                }
                            }
                        }
                    }
                }

            }


            function expandTree(rootNode) {
                var expanded = [];

                expanded.push(rootNode);
                if (rootNode.containedUnits) {
                    for (var i = 0; i < rootNode.containedUnits.length; i++) {
                        var expandedcontainedUnits = expandTree(rootNode.containedUnits[i]);
                        for (var j = 0; j < expandedcontainedUnits.length; j++) {
                            expanded.push(expandedcontainedUnits[j]);
                        }
                    }
                }

                return expanded;
            }


            function clean(d, nodeType) {

                var containedUnits = d.containedUnits;
                if (containedUnits) {
                    for (var i = containedUnits.length - 1; i--; ) {
                        if (containedUnits[i].name == nodeType)
                            containedUnits[i].remove()
                    }

                    for (var i = containedUnits.length - 1; i--; ) {
                        clean(containedUnits[i], nodeType);
                    }
                }
            }


            function updateText(source) {

                // Compute the new tree layout.
                var nodes = tree.nodes(root).reverse();

                //                // Normalize for fixed-depth.
                nodes.forEach(function(d) {
                    if (d.type == "requirement") {
                        d.y = 0.8 * (d.depth * depth);
                    } else {
                        d.y = d.depth * depth;
                    }
                });

                // Update the nodes…
                var node = vis.selectAll("g.node")
                        .data(nodes, function(d) {
                            return d.id || (d.id = ++i);
                        });

                node.selectAll("text")
                        .text(function(d) {
                            if (d.attention) {
                                return d.name + ": " + d.actionName;
                            } else if (d.type == "VM") {
                                return d.name;
                            } else {
                                return d.name;
                            }
                        });

                // Enter any new nodes at the parent's previous position.
                var nodeEnter = node.enter().append("g")
                        .attr("class", "node")
                        .attr("transform", function(d) {
                            return "translate(" + (d.parent.y0) + "," + d.parent.x0 + ")";
                        })
                        .attr("display", function(d) {
                            if (d.name == "SubComponents") {
                                return "none";
                            } else {
                                return "yes"
                            }
                            ;
                        })
                        ;


                nodeEnter.append("path")
                        .attr("d", function(d) {
                            if (d.type == "SERVICE" || d.type == "SERVICE_TOPOLOGY" || d.type == "SERVICE_UNIT") {
                                return simpleComponentIcon;
                            }

                            else if (d.type == "metric") {
                                return auxRect;
                            }
                            else if (d.type == "auxiliaryMetric") {
                                return auxRect;
                            }
                            else if (d.type == "requirement") {
                                if (d.attention) {
                                    return warningTriangle;
                                } else {
                                    return sphere;
                                }
                                ;
                            }
                            else if (d.name == "SubComponents") {
                                return complexComponentIcon;
                            }
                        }
                        )
                        .attr("stroke", "black")
                        .attr("stroke-width", 1)
                        .attr("fill", function(d) {
                            if (d.type == "metric") {
                                return "gray";
                            } else
                                return "red";
                        });

                nodeEnter.append("svn:image")
                        .attr("xlink:href", function(d) {
                            if (d.type == "VM") {
                                return "./vm.png";
                            } else {
                                return null;
                            }
                        })
                        .attr("width", 30)
                        .attr("height", 30)
                        .attr("dx", -15)
                        .attr("y", -15);

                // Transition nodes to their new position.
                var nodeUpdate = node.transition()

                        .duration(function(d) {
                            if (d.type.match(/SERVIC.*|V.*/g)) {
                                return duration;
                            } else {
                                return 0;
                            }
                        })
                        .attr("transform", function(d) {
                            if (d.type != "requirement") {
                                return "translate(" + d.y + "," + d.x + ")";
                            } else {
                                return "translate(" + d.y + "," + d.x + ")";
                            }
                        })

                //console.log(node.name)


                nodeUpdate.select("path")
                        .attr("r", function(d) {
                            return d.value ? 0 : 4.5;
                        })
                        .style("stroke", function(d) {
                            if (d.attention) {
                                return "#909090";
                            } else {
                                return "#909090"
                            }
                            ;
                        })
                        .style("fill", function(d) {
                            if (d.type == "metric") {
                                return "gray";
                            } else {
                                if (d.attention) {
                                    return "#D13F31";
                                } else {
                                    if (d.type == "requirement") {
                                        if (d.fulfilled) {
                                            return "#1F7872"
                                        } else {
                                            return "#D13F31";
                                        }

                                    } else {
                                        return "#72B095";
                                    }
                                }
                            }
                        }
                        );


                nodeUpdate.select("text")
                        .attr("text-anchor", function(d) {
                            var position = 0;
                            switch (d.type) {
                                case "SERVICE":
                                    position = "start";
                                    break;
                                default:
                                    position = "end";
                                    break;

                            }
                            return position;

                        })

                        .attr("dy", function(d) {
                            var position = 0;
                            switch (d.type) {
                                case "SERVICE":
                                    position = -25;
                                    break;
                                case "VM":
                                    position = -15;
                                    break;
                                default:
                                    position = -5;
                                    break;

                            }
                            return position;

                        })
                        .attr("dx", function(d) {
                            var position = 0;
                            switch (d.type) {
                                case "SERVICE":
                                    position = -10;
                                    break;
                                case "VM":
                                    position = +25;
                                    break;
                                default:
                                    position = -15;
                                    break;
                            }
                            return position;

                        })


                        .style("font-size", function(d) {
                            return (d.type == "metric") ? 14 : 18;
                        })
                        .attr("font-style", function(d) {
                            return d.containedUnits ? "normal" : "italic";
                        })
                        .style("fill-opacity", 1)
                        .text(function(d) {
                            if (d.attention) {
                                return d.name + ": " + d.actionName;
                            } else if (d.type == "VM") {
                                return d.name;
                            } else {
                                return d.name;
                            }
                        });

                // Transition exiting nodes to the parent's new position.
                var nodeExit = node.exit().transition()
                        .duration(function(d) {
                            if (d.type.match(/SERVIC.*|V.*/g)) {
                                return duration;
                            } else {
                                return 0;
                            }
                        })
                        .attr("transform", function(d) {
                            return "translate(" + source.y + "," + source.x + ")";
                        })
                        .remove();

                nodeExit.select("circle")
                        .attr("r", function(d) {
                            return d.value ? 0 : 8;
                        });

                nodeExit.select("text")
                        .attr("text-anchor", function(d) {
                            return d.value || d.ip || d.containedUnits ? "end" : "start";
                        })
                        .attr("dy", -5)
                        .style("font-size", function(d) {
                            return (d.type == "metric") ? 14 : 18;
                        })
                        .attr("font-style", function(d) {
                            return d.containedUnits ? "normal" : "italic";
                        })
                        .style("fill-opacity", 1e-6);

                nodeEnter.append("text")
                        .attr("dx", function(d) {
                            return d.value ? 10 : 5;
                        })
                        .attr("dy", function(d) {
                            return d.value ? 0 : 10;
                        })
                        .style("font-size", function(d) {
                            return (d.type == "metric") ? 14 : 18;
                        })
                        .attr("text-anchor", function(d) {
                            return d.ip ? "end" : "start";
                        })
                        .attr("font-style", function(d) {
                            return d.containedUnits ? "normal" : "italic";
                        })
                        .text(function(d) {
                            if (d.attention) {
                                return d.name + ": " + d.actionName;
                            } else if (d.type == "VM") {
                                return d.name;
                            } else {
                                return d.name;
                            }
                        });

                // Update the links…
                var link = vis.selectAll("path.link")
                        .data([], function(d) {
                            return d.target.id;
                        });
                link.exit().remove();


                link = vis.selectAll("path.link")
                        .data(tree.links(nodes), function(d) {
                            return d.target.id;
                        });

                // Enter any new links at the parent's previous position.
                link.enter().insert("path", "g")
                        .attr("class", "link")
                        .attr("d", function(d) {
                            var o = {x: source.x, y: source.y};
                            return diagonal({source: o, target: o});
                        })
                        .style("stroke-dasharray", function(d) {
                            if (d.target.type == "metric") {
                                return "0";
                            }
                            else if (d.target.type == "requirement") {
                                return "3.3";
                            }
                            else if (d.target.type == "auxiliaryMetric") {
                                return "3.3";
                            }
                            else {
                                return "1";
                            }
                        })
                        .style("stroke", function(d) {
                            if (d.target.type == "requirement") {
                                if (d.target.attention) {
                                    return "#E00000";
                                }
                                else {
                                    return "#00E096";
                                }
                            } else {
                                return "#ccc";
                            }
                        })
                        .style("stroke-width", function(d) {
                            if (d.target.type == "requirement") {
                                return "1";
                            }
                            else if (d.target.type == "auxiliaryMetric") {
                                return "0.5";
                            }
                            else {
                                return "1";
                            }
                        })
                        ;

                // Transition links to their new position.
                link.transition()
                        .duration(0)
                        .attr("d", diagonal);

                // Transition exiting nodes to the parent's new position.
                link.exit().transition()
                        .duration(0)
                        .attr("d", function(d) {
                            var o = {x: source.x, y: source.y};
                            return diagonal({source: o, target: o});
                        })
                        .remove();

                // Stash the old positions for transition.
                nodes.forEach(function(d) {
                    d.x0 = d.x;
                    d.y0 = d.y;
                });
            }

            function update(source) {

                // Compute the new tree layout.
                var nodes = tree.nodes(root).reverse();

                // Normalize for fixed-depth.
                nodes.forEach(function(d) {
                    if (d.type == "requirement") {
                        d.y = 0.8 * (d.depth * depth);
                    }   else {
                        d.y = d.depth * depth;
                    }
                });

                // Update the nodes…
                var node = vis.selectAll("g.node")
                        .data(nodes, function(d) {
                            return d.id || (d.id = ++i);
                        });


                // Enter any new nodes at the parent's previous position.
                var nodeEnter = node.enter().append("g")
                        .attr("class", "node")
                        .attr("transform", function(d) {
                            //                    if (d.type != "requirement") {
                            return "translate(" + source.y + "," + source.x + ")";
                            //                    }
                            //                    else {
                            //                        return "translate(" + (d.parent.y0) + "," + d.parent.x0 + ")";
                            //                    }
                        })
                        .attr("display", function(d) {
                            if (d.name == "SubComponents") {
                                return "none";
                            } else {
                                return "yes"
                            }
                        })
                       ;

                nodeEnter.append("path")
                        .attr("d", function(d) {
                            if (d.type == "SERVICE" || d.type == "SERVICE_TOPOLOGY" || d.type == "SERVICE_UNIT") {
                                return simpleComponentIcon;
                            }

                            else if (d.type == "metric") {
                                return auxRect;
                            }
                            else if (d.type == "auxiliaryMetric") {
                                return auxRect;
                            }
                            else if (d.type == "requirement") {
                                if (d.attention) {
                                    return warningTriangle;
                                } else {
                                    return sphere;
                                }
                                ;
                            }
                            else if (d.name == "SubComponents") {
                                return complexComponentIcon;
                            }
                        }
                        )
                        .attr("stroke", "black")
                        .attr("stroke-width", 1)
                        .attr("fill", function(d) {
                            if (d.type == "metric") {
                                return "red";
                            }
                            else {
                                return "orange";
                            }
                        });

                nodeEnter.append("svn:image")
                        .attr("xlink:href", function(d) {
                            if (d.type == "VM") {
                                return "./vm.png";
                            } else {
                                return null;
                            }
                        })
                        .attr("width", 30)
                        .attr("height", 30)
                        .attr("dx", -15)
                        .attr("y", -15);


                nodeEnter.append("text")
                        .attr("text-anchor", function(d) {
                            var position = 0;
                            switch (d.type) {
                                case "SERVICE":
                                    position = "start";
                                    break;
                                case "metric":
                                    position = "start";
                                    break;
                                case "requirement":
                                    position = "start";
                                    break;
                                default:
                                    position = "end";
                                    break;

                            }
                            return position;

                        })

                        .attr("dy", function(d) {
                            var position = 0;
                            switch (d.type) {
                                case "SERVICE":
                                    position = -25;
                                    break;
                                case "VM":
                                    position = -15;
                                    break;
                                default:
                                    position = -5;
                                    break;

                            }
                            return position;

                        })
                        .attr("dx", function(d) {
                            var position = 0;
                            switch (d.type) {
                                case "SERVICE":
                                    position = -10;
                                    break;
                                case "VM":
                                    position = +25;
                                    break;
                                default:
                                    position = -15;
                                    break;
                            }
                            return position;

                        })
                        .style("font-size", function(d) {
                            return (d.type == "metric") ? 14 : 19;
                        })
                        .attr("font-style", function(d) {
                            return d.containedUnits ? "normal" : "italic";
                        })
                        .style("fill-opacity", 1e-6)
                        .text(function(d) {
                            if (d.attention) {
                                return d.name + ": " + d.actionName;
                            } else if (d.type == "VM") {
                                return d.name;
                            } else {
                                return d.name;
                            }
                        });


                // Transition nodes to their new position.
                var nodeUpdate = node.transition()

                        .duration(duration)
                        .attr("transform", function(d) {
                            //                    if (d.type != "requirement") {
                            return "translate(" + d.y + "," + d.x + ")";
                            //                    } else {
                            //                        return "translate(" + d.y + "," + d.x + ")";
                            //                    }
                        })
                //.attr("transform", function(d) { return "translate(" + d.y + "," + d.x + ")"; });
                //console.log(node.name)

                nodeUpdate.select("circle")
                        .attr("r", function(d) {
                            return d.value ? 0 : 8;
                        })
                        .style("stroke", function(d) {
                            if (d.attention) {
                                return "#909090";
                            } else {
                                return "#909090"
                            }
                            ;
                        })
                        .style("fill", function(d) {
                            if (d.attention) {
                                return "#E00000";
                            } else {
                                return "#CCFFFF";
                            }
                        });

                nodeUpdate.select("rect")
                        .attr("r", function(d) {
                            return d.value ? 0 : 4.5;
                        })
                        .style("stroke", function(d) {
                            if (d.attention) {
                                return "#909090";
                            } else {
                                return "#909090"
                            }
                            ;
                        })
                        .style("fill", function(d) {
                            if (d.attention) {
                                return "#FF6666";
                            } else {
                                return "#CCFFFF";
                            }
                        });

                nodeUpdate.select("text")
                        .attr("text-anchor", function(d) {
                            var position = 0;
                            switch (d.type) {
                                case "SERVICE":
                                    position = "start";
                                    break;
                                case "metric":
                                    position = "start";
                                    break;
                                case "requirement":
                                    position = "start";
                                    break;
                                default:
                                    position = "end";
                                    break;

                            }
                            return position;

                        })

                        .attr("dy", function(d) {
                            var position = 0;
                            switch (d.type) {
                                case "SERVICE":
                                    position = -25;
                                    break;
                                case "VM":
                                    position = -15;
                                    break;
                                default:
                                    position = -5;
                                    break;

                            }
                            return position;

                        })
                        .attr("dx", function(d) {
                            var position = 0;
                            switch (d.type) {
                                case "SERVICE":
                                    position = -10;
                                    break;
                                case "VM":
                                    position = +25;
                                    break;
                                default:
                                    position = -15;
                                    break;
                            }
                            return position;

                        })

                        .style("font-size", function(d) {
                            return (d.type == "metric") ? 14 : 19;
                        })
                        .attr("font-style", function(d) {
                            return d.containedUnits ? "normal" : "italic";
                        })
                        .style("fill-opacity", 1);

                // Transition exiting nodes to the parent's new position.
                var nodeExit = node.exit().transition()
                        .duration(duration)
                        .attr("transform", function(d) {
                            return "translate(" + source.y + "," + source.x + ")";
                        })
                        .remove();

                nodeExit.select("circle")
                        .attr("r", function(d) {
                            return d.value ? 0 : 8;
                        });

                nodeExit.select("text")
                        .attr("text-anchor", function(d) {
                            return   d.ip || d.containedUnits ? "end" : "start";
                        })
                        .attr("dy", -5)
                        .style("font-size", function(d) {
                            return (d.type == "metric") ? 14 : 19;
                        })
                        .attr("font-style", function(d) {
                            return d.containedUnits ? "normal" : "italic";
                        })
                        .style("fill-opacity", 1e-6);


                // Update the links…
                var link = vis.selectAll("path.link")
                        .data([], function(d) {
                            return d.target.id;
                        });
                link.exit().remove();


                link = vis.selectAll("path.link")
                        .data(tree.links(nodes), function(d) {
                            return d.target.id;
                        });

                //TODO: test if works without this.
                // Enter any new links at the parent's previous position.
                link.enter().insert("path", "g")
                        .attr("class", "link")
                        .attr("d", function(d) {
                            if (d.target.type == "metric") {
                                var o = {x: source.x, y: source.y};
                                return diagonal({source: o, target: o});
                            } else {
                                var o = {x: source.x, y: source.y};
                                return diagonal({source: o, target: o});
                            }
                        })
                        .style("stroke-dasharray", function(d) {
                            if (d.target.type == "metric") {
                                return "0";
                            }
                            else if (d.target.type == "requirement") {
                                return "3.3";
                            }
                            else if (d.target.type == "auxiliaryMetric") {
                                return "3.3";
                            }
                            else {
                                return "1";
                            }
                        })
                        .style("stroke", function(d) {
                            if (d.target.type == "requirement") {
                                if (d.target.attention) {
                                    return "#E00000";
                                }
                                else {
                                    return "#00E096";
                                }
                            } else {
                                return "#ccc";
                            }
                        })
                        .style("stroke-width", function(d) {
                            if (d.target.type == "requirement") {
                                return "1";
                            }
                            else if (d.target.type == "auxiliaryMetric") {
                                return "0.5";
                            }
                            else {
                                return "1";
                            }
                        })
                        ;

                // Transition links to their new position.
                link.transition()
                        .duration(duration)
                        .attr("d", diagonal);

                // Transition exiting nodes to the parent's new position.
                link.exit().transition()
                        .duration(duration)
                        .attr("d", function(d) {
                            var o = {x: source.x, y: source.y};
                            return diagonal({source: o, target: o});
                        })
                        .remove();

                // Stash the old positions for transition.
                nodes.forEach(function(d) {
                    d.x0 = d.x;
                    d.y0 = d.y;
                });
            }


            

            function showContent(d, show) {
                if (!show && d.containedUnits) {
                    d._containedUnits = d.containedUnits;
                    d.containedUnits = null;
                    update(d);
                } else if (!d.containedUnits) {
                    d.containedUnits = d._containedUnits;
                    d._containedUnits = null;
                    update(d);
                }

            }

            var root = null

            function displayJSONTree(jsonData, displayCanvas) {


             width = displayCanvas.innerWidth

               height = displayCanvas.innerHeight - 100
               i = 0
               duration = 500
               depth = width / 4.5

        tree = d3.layout.tree()
                .size([height, width]);

          diagonal = d3.svg.diagonal()
                .projection(function(d) {
                    return [d.y, d.x];
                });

              vis = d3.select(displayCanvas).append("svg")
                    .attr("width", width + margin.right + margin.left)
                    .attr("height", height + margin.top + margin.bottom)
                    .append("g")
                    .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

                



                        new_root = JSON.parse(jsonData);

 
                        //if we have root that changed and is not metric, update its tree
                        if (root == null) {
                            root = new_root;
                            update(root);
                            //                        updateTextOnNode(root, root, change);
                        } else {
                            var change = -1;
                            updateTextOnNode(root, new_root, change);
                            //if (change == -1) {
                                updateText(root);
                           // } else {
                           //     update(new_root);
                            //}
                        }


               

            }
         

            function drawSpinner(spinnerContainer) {
                var target = document.getElementById(spinnerContainer);
                //target.style.display = "block";
                loadingSpinner.spin(target);
            }

