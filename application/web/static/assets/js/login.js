var login = {
    "doLogin": function(e) {
        e.preventDefault()

        var form_data = $(this).serialize();

        $.post("/api/login/", form_data, function(response) {
            if (response.success) {
                var nextUrl = url.getUrlParameter("next")
                if (!nextUrl) {
                    nextUrl = "/"
                }
                window.location.href = nextUrl;
            } else {
                ui.showAlert("error", response.message);
                $("#password").val("");
            }
        });
    },
    "bindEventHandlers": function() {
        $("#login-form").submit(login.doLogin);
    }
}

$(document).ready(function() {
    login.bindEventHandlers();
});
