schedulingForm = {
    "addInterval": function(e) {
        e.preventDefault();

        var intervalRow = ui.renderTemplate("interval-template", {});

        $("#interval-table tbody").append(intervalRow);
    },
    "removeInterval": function(e) {
        e.preventDefault();

        $(this).closest("tr").remove();
    },
    "bindEventHandlers": function() {
        $("#btn-add-interval").click(schedulingForm.addInterval);
        $("#interval-table").on("click", ".remove-interval", schedulingForm.removeInterval);
    }
}

$(document).ready(function() {
    schedulingForm.bindEventHandlers();
});
