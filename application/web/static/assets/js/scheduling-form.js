schedulingForm = {
    "addInterval": function(e) {
        e.preventDefault();

        var intervalRow = ui.renderTemplate("interval-template", {});

        $("#interval-table tbody").append(intervalRow);
        $("#interval-table .interval-start").last().datetimepicker();
    },
    "bindEventHandlers": function() {
        $("#btn-add-interval").click(schedulingForm.addInterval);
    }
}

$(document).ready(function() {
    schedulingForm.bindEventHandlers();
});