ace.define("ace/mode/test_execution_description_highlight_rules",["require","exports","module","ace/lib/oop","ace/mode/text_highlight_rules"], function(require, exports, module) {
"use strict";

var oop = require("../lib/oop");
var TextHighlightRules = require("./text_highlight_rules").TextHighlightRules;

var test_execution_descriptionHighlightRules = function() {

    var keywordMapper = this.createKeywordMapper({
        "variable.language": "UnitType UnitID UnitUUID",
        "keyword": 
            "Description Triggers Execution",
        "constant.language": 
            "TRUE FALSE NULL SPACE",
        "support.type": 
            "name description timeout  event every executor distinct",
        "keyword.operator":
            "on for s" 
    }, "text", false, " ");

     
    this.$rules = {
        "start" : [
            {token : "string", regex : "\"", next  : "qstring"},
            {token : "doc.comment", regex : /^\#.+/},
            {token : "comment",  regex : /"#.+$/},
            {token : "invalid", regex: "\\.{2,}"},
            {token : "paren.lparen", regex : "[\\[({]"},
            {token : "paren.rparen", regex : "[\\])}]"},
            {token : "constant.numeric", regex: "[+-]?\\d+\\b"},
            {token : "variable.parameter", regex : /sy|pa?\d\d\d\d\|t\d\d\d\.|innnn/}, 
            {token : "variable.parameter", regex : /\w+-\w+(?:-\w+)*/}, 
            {token : keywordMapper, regex : "\\b\\w+\\b"},
            {caseInsensitive: false}
        ],
        "qstring" : [
            {token : "constant.language.escape",   regex : "\"\""},
            {token : "string", regex : "\"",     next  : "start"},
            {defaultToken : "string"}
        ]
    };
};
oop.inherits(test_execution_descriptionHighlightRules, TextHighlightRules);

exports.test_execution_descriptionHighlightRules = test_execution_descriptionHighlightRules;
});

ace.define("ace/mode/folding/coffee",["require","exports","module","ace/lib/oop","ace/mode/folding/fold_mode","ace/range"], function(require, exports, module) {
"use strict";

var oop = require("../../lib/oop");
var BaseFoldMode = require("./fold_mode").FoldMode;
var Range = require("../../range").Range;

var FoldMode = exports.FoldMode = function() {};
oop.inherits(FoldMode, BaseFoldMode);

(function() {

    this.getFoldWidgetRange = function(session, foldStyle, row) {
        var range = this.indentationBlock(session, row);
        if (range)
            return range;

        var re = /\S/;
        var line = session.getLine(row);
        var startLevel = line.search(re);
        if (startLevel == -1 || line[startLevel] != "#")
            return;

        var startColumn = line.length;
        var maxRow = session.getLength();
        var startRow = row;
        var endRow = row;

        while (++row < maxRow) {
            line = session.getLine(row);
            var level = line.search(re);

            if (level == -1)
                continue;

            if (line[level] != "#")
                break;

            endRow = row;
        }

        if (endRow > startRow) {
            var endColumn = session.getLine(endRow).length;
            return new Range(startRow, startColumn, endRow, endColumn);
        }
    };
    this.getFoldWidget = function(session, foldStyle, row) {
        var line = session.getLine(row);
        var indent = line.search(/\S/);
        var next = session.getLine(row + 1);
        var prev = session.getLine(row - 1);
        var prevIndent = prev.search(/\S/);
        var nextIndent = next.search(/\S/);

        if (indent == -1) {
            session.foldWidgets[row - 1] = prevIndent!= -1 && prevIndent < nextIndent ? "start" : "";
            return "";
        }
        if (prevIndent == -1) {
            if (indent == nextIndent && line[indent] == "#" && next[indent] == "#") {
                session.foldWidgets[row - 1] = "";
                session.foldWidgets[row + 1] = "";
                return "start";
            }
        } else if (prevIndent == indent && line[indent] == "#" && prev[indent] == "#") {
            if (session.getLine(row - 2).search(/\S/) == -1) {
                session.foldWidgets[row - 1] = "start";
                session.foldWidgets[row + 1] = "";
                return "";
            }
        }

        if (prevIndent!= -1 && prevIndent < indent)
            session.foldWidgets[row - 1] = "start";
        else
            session.foldWidgets[row - 1] = "";

        if (indent < nextIndent)
            return "start";
        else
            return "";
    };

}).call(FoldMode.prototype);

});

ace.define("ace/mode/test_execution_description",["require","exports","module","ace/mode/test_execution_description_highlight_rules","ace/mode/folding/coffee","ace/range","ace/mode/text","ace/lib/oop"], function(require, exports, module) {
"use strict";

var Rules = require("./test_execution_description_highlight_rules").test_execution_descriptionHighlightRules;
var FoldMode = require("./folding/coffee").FoldMode;
var Range = require("../range").Range;
var TextMode = require("./text").Mode;
var oop = require("../lib/oop");

function Mode() {
    this.HighlightRules = Rules;
    this.foldingRules = new FoldMode();
}

oop.inherits(Mode, TextMode);

(function() {
    
    this.lineCommentStart = '"'
    
    this.getNextLineIndent = function(state, line, tab) {
        var indent = this.$getIndent(line);
        return indent;
    };    
    
    this.$id = "ace/mode/test_execution_description";
}).call(Mode.prototype);

exports.Mode = Mode;

});
