var thresholds = {
    "highestThresholdIndex": 0,
    "editors": {},
    "bindEventHandlers": function() {
        $("#btn-add-threshold").click(thresholds.addThreshold);
        $("#threshold-form").on("click", ".remove-custom", thresholds.removeThreshold);
        $("#threshold-form").submit(thresholds.submitForm);
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
        var html = ui.renderTemplate("threshold-template", {
            "threshold_index": thresholds.highestThresholdIndex
        });

        $(".threshold-row:last").after(html);
        thresholds.createLastEditor();
    },
    "removeThreshold": function() {
        var thresholdId = $(this).closest(".threshold-row").attr("id");
        delete thresholds.editors[thresholdId];
        $(this).closest(".threshold-row").remove();
    },
    "submitForm": function(e) {
        e.preventDefault();

        for (row_id in thresholds.editors) {
            var value = thresholds.editors[row_id].getValue();
            $("#" + row_id).find(".codemirror").val(value);
        };
        var formData = $("#threshold-form").serialize();

        $.post("/api/save_plugin_thresholds/", formData, function(data) {
            var alertType = "danger";
            if (data.success) {
                alertType = "success";
            }

            ui.showAlert(alertType, data.message);
        });
    }
}

$(document).ready(function() {
    thresholds.bindEventHandlers();
    thresholds.createLastEditor();
});
