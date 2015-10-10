pluginInstall = {
    "installPlugin": function(e) {
        e.preventDefault();

        var formData = new FormData($(this)[0]);
        var endpoint = $(this).attr("action");

        pluginInstall._makeInstallRequest(formData, endpoint);
    },
    "_makeInstallRequest": function(formData, endpoint) {
        $.ajax({
            url: endpoint,
            type: "POST",
            data: formData,
            success: function(data) {
                if (data.success) {
                    if (data.result == "plugin_exists") {
                        bootbox.confirm("This plugin is already installed, do you want "
                            + "to overwrite it with the version you are uploading?",
                            function(result) {
                                if (result === true) {
                                    endpoint = endpoint + "?allow-overwrite=1";
                                    pluginInstall._makeInstallRequest(formData, endpoint);
                                }
                            });
                    } else if (data.result == "plugin_updated") {
                        ui.showAlert("success", "Plugin has been updated successfully!");
                    } else if (data.result == "plugin_installed") {
                        ui.showAlert("success", "Plugin has been installed successfully!");
                    }
                } else {
                    ui.showAlert("danger", data.message);
                }
            },
            processData: false,
            contentType: false
        });
    },
    "bindEventHandlers": function() {
        $("#form-plugin-install").submit(pluginInstall.installPlugin);
    }
}

$(document).ready(function() {
    pluginInstall.bindEventHandlers();
});