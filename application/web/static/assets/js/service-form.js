serviceForm = {
    selectHost: function() {
        $("#host-selection-modal").modal();
    },
    addDependencyClicked: function() {
        serviceForm.nextAction = serviceForm.addDependency;
        serviceForm.selectHost();
    },
    addDependency: function(item) {
        item["icon"] = (item["type"] == "group") ? "object-group" : "desktop";
        var html = ui.renderTemplate("template-dependency", item);

        $("#dependency-container").append(html);
    },
    addItemClicked: function() {
        serviceForm.nextAction = serviceForm.addItem;
        serviceForm.actionGroup = $(this).closest(".service-dependency");
        serviceForm.selectHost();
    },
    addItem: function(item) {
        console.log("Item");
        console.log(serviceForm.actionGroup);
        console.log(item);
    },
    itemSelection: function() {
        $("#host-selection-modal").modal("hide");

        var item = {
            "id": $(this).attr("data-item-id"),
            "name": $(this).attr("data-item-name"),
            "type": $(this).attr("data-item-type")
        }

        // Check the item doesn't already exist before adding
        var exists = false;
        $(".dependency-item").each(function(index) {
            var id = $(this).attr("data-item-id");
            var type = $(this).attr("data-item-type");
            if (item["id"] == id && item["type"] == type) {
                exists = true;
            }
        });

        if (exists) {
            ui.showAlert("error", "That item already exists as a dependency");
        } else {
            serviceForm.nextAction(item);
        }
    },
    removeDependency: function() {
        $(this).closest(".service-dependency").remove();
    },
    bindEventHandlers: function() {
        $("#add-dependency").click(serviceForm.addDependencyClicked);
        $("button.select-item").click(serviceForm.itemSelection);
        $("#dependency-container").on("click", ".add-item", serviceForm.addItemClicked);
        $("#dependency-container").on("click", ".dependency-remove", serviceForm.removeDependency);
    }
}

$(document).ready(function() {
    serviceForm.bindEventHandlers();
});
