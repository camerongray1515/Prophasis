from flask import Flask, render_template

web = Flask(__name__)

@web.route("/example/")
def example():
    return render_template("example.html")

@web.route("/")
def home():
    return render_template("home.html", nav_section="home", section="Home")

@web.route("/hosts/")
def hosts():
    return render_template("hosts.html", nav_section="hosts", section="Hosts",
        title="Manage Hosts")

@web.route("/host-groups/")
def host_groups():
    return render_template("host-groups.html", nav_section="host-groups",
        section="Host Groups", title="Manage Host Groups")

if __name__ == "__main__":
    web.run(debug=True)
