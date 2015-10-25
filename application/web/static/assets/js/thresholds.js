var thresholds = {
    "highestThresholdIndex": 0,
    "editors": {},
    "bindEventHandlers": function() {
        $("#btn-add-threshold").click(thresholds.addThreshold);
        $("#threshold-form").on("click", ".remove-custom", thresholds.removeThreshold);
    },
    "createLastEditor": function() {
        var editor = CodeMirror.fromTextArea($(".codemirror:last").get(0), {
            "lineNumbers": true,
            "mode": "lua",
            "smartIndent": false
        })
        thresholds.editors["threshold-" + thresholds.highestThresholdIndex] = editor;
        thresholds.highestThresholdIndex++;
    },
    "addThreshold": function() {
        html = ui.renderTemplate("threshold-template", {
            "threshold_index": thresholds.highestThresholdIndex
        });

        $(".threshold-row:last").after(html);
        thresholds.createLastEditor();
    },
    "removeThreshold": function() {
        thresholdId = $(this).closest(".threshold-row").attr("id");
        delete thresholds.editors[thresholdId];
        $(this).closest(".threshold-row").remove();
    }
}

$(document).ready(function() {
    thresholds.bindEventHandlers();
    thresholds.createLastEditor();
});
