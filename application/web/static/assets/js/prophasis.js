ui = {
    "compiledTemplates": {},
    "renderTemplate": function(templateId, context) {
        if (typeof ui.compiledTemplates[templateId] === "undefined") {
            var source = $("#" + templateId).html();
            ui.compiledTemplates[templateId] = Handlebars.compile(source);
        }

        var html = ui.compiledTemplates[templateId](context);
        return html;
    },
    "showAlert": function(type, message, container) {
        container = (typeof container === "undefined") ? "alert-container" : container;

        var prefix = (type == "success") ? "Success!" : "Error!";

        var html = ui.renderTemplate("alert-template", {"type": type,
            "prefix": prefix, "message": message});

        $("#" + container).hide();
        $("#" + container).html(html);
        $("#" + container).fadeIn();
        setTimeout(function() {
            $("#" + container).fadeOut();
        }, 5000);
    }
}

forms = {
    "autoPost": function(e) {
        e.preventDefault();

        var submittedForm = this;

        function doPost() {
            var endpoint = $(submittedForm).attr("action");
            var formData = $(submittedForm).serialize();
            $.post(endpoint, formData, function(data) {
                var alertType = "danger";
                if (data.success) {
                    alertType = "success";

                    var removeClosest = $(submittedForm).attr("data-auto-post-remove-closest");
                    if (removeClosest) {
                        $(submittedForm).closest(removeClosest).fadeOut();
                    }
                }

                ui.showAlert(alertType, data.message);
            });
        }

        var confirmationMessage = $(this).attr("data-auto-post-confirmation");
        if (confirmationMessage) {
            bootbox.confirm(confirmationMessage, function(result) {
                if (result) {
                    doPost();
                }
            });
        } else {
            doPost();
        }

    },
    "bindEventHandlers": function() {
        $("form.auto-post").submit(forms.autoPost);
    }
}

autoFilter = {
    "filterTable": function() {
        var filterText = $(this).val();
        var tableSelector = "#" + $(this).attr("data-table-id");
        $(tableSelector + " tr").hide();
        $.each($(tableSelector).find("td.filter-text"), function(td) {
            var text = $(this).text().toLowerCase();
            if (text.indexOf(filterText) > -1) {
                $(this).closest("tr").show();
            }
        });
    },
    "bindEventHandlers": function() {
        $("input.auto-filter").keyup(autoFilter.filterTable);
    }
}

$(document).ready(function() {
    forms.bindEventHandlers();
    autoFilter.bindEventHandlers();
});