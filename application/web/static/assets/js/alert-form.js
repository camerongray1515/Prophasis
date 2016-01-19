alert = {
    "entitySelectionChanged": function() {
        if ($(this).val() == "custom") {
            $("#custom-entity-selection").show();
        } else {
            $("#custom-entity-selection").hide();
        }
    },
    "bindEventHandlers": function() {
        $("#entity-selection").change(alert.entitySelectionChanged);
    }
}

$(document).ready(function() {
    alert.bindEventHandlers();
});
