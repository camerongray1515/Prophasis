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

        var html = ui.renderTemplate("alert-template", {"type": type, "message": message});
        $("#" + container).hide();
        $("#" + container).html(html);
        $("#" + container).fadeIn();
        setTimeout(function() {
            $("#" + container).fadeOut();
        }, 5000);
    }
}