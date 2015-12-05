serviceForm = {
    selectHost: function() {
        $("#host-selection-modal").modal();
    },
    addDependencyClicked: function() {
        serviceForm.nextAction = serviceForm.addDependency;
        serviceForm.selectHost();
    },
    addDependency: function(item) {
        console.log("Dependency");
        console.log(item);
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
        
    }
    bindEventHandlers: function() {
        $("#add-dependency").click(serviceForm.addDependencyClicked);
        $("#dependency-container").on("click", ".add-item", serviceForm.addItemClicked);
    }
}

$(document).ready(function() {
    serviceForm.bindEventHandlers();
});
