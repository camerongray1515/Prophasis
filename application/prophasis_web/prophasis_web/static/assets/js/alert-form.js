alert = {
    "entitySelectionChanged": function() {
        if ($(this).val() == "custom") {
            $("#custom-entity-selection").show();
        } else {
            $("#custom-entity-selection").hide();
        }
    },
    "moduleSelectionChanged": function() {
        var module_id = $(this).val();
        var rows = $(".module-options[data-module-id=\"" + module_id + "\"]").html();
        $("#module-options tbody").html(rows);
    },
    "bindEventHandlers": function() {
        $("#entity-selection").change(alert.entitySelectionChanged);
        $("#module-selection").change(alert.moduleSelectionChanged);
    }
}

$(document).ready(function() {
    alert.bindEventHandlers();
});
