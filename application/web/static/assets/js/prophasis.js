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
        var endpoint = $(this).attr("action");
        var formData = $(this).serialize();
        $.post(endpoint, formData, function(data) {
            var alertType = "danger";
            if (data.success) {
                alertType = "success";
            }

            ui.showAlert(alertType, data.message);
        });
    },
    "bindEventHandlers": function() {
        $("form.auto-post").submit(forms.autoPost);
    }
}

$(document).ready(function() {
    forms.bindEventHandlers();
});