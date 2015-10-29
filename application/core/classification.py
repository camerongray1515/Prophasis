import lupa
import json
import numbers
from models import PluginThreshold, PluginResult

def execute_classifier(code, values):
    lua = lupa.LuaRuntime()
    # Create a sandbox to prevent code from accessing dangerous functions
    sandbox = lua.eval("{}")
    setfenv = lua.eval("setfenv")
    # Specify what libraries/functions we want to allow access to
    sandbox.math = lua.globals().math
    sandbox.table = lua.globals().table
    sandbox.ipairs = lua.globals().ipairs
    setfenv(0, sandbox)

    # Build up the code by including library functions and the data array itself
    full_code = "values={}\n".format(list_to_lua_array(values))
    with open("classifier_functions.lua", "r") as f:
        full_code += "\n".join(f.readlines())
    full_code += "\n{}".format(code)

    return lua.execute(full_code)

def classify(latest_result, check_id):
    # Try and get a check specific threshold, if there isn't one, get default
    threshold = PluginThreshold.query.filter(
        PluginThreshold.plugin_id == latest_result.plugin_id,
        PluginThreshold.check_id == check_id,
        PluginThreshold.default == False
    ).all()

    if not threshold:
        threshold = PluginThreshold.query.filter(
            PluginThreshold.plugin_id == latest_result.plugin_id,
            PluginThreshold.default == True
        ).all()

    try:
        threshold = threshold[0]
    except KeyError:
        # TODO: Log error here
        return "unknown"

    # Get n-1 historical values and then append the latest onto this list
    historical_values = PluginResult.query.filter(
        PluginResult.plugin_id == latest_result.plugin_id,
        PluginResult.host_id == latest_result.host_id).order_by(
            PluginResult.id.desc()
        ).limit(threshold.n_historical-1).all()

    historical_values_list = []
    for value in historical_values:
        if threshold.variable == "value":
            historical_values_list.append(value.value)
        else:
            historical_values_list.append(value.message)
    if threshold.variable == "value":
        historical_values_list.append(latest_result.value)
    else:
        historical_values_list.append(latest_result.message)

    try:
        classification = execute_classifier(threshold.classification_code,
            historical_values_list)
    except lupa._lupa.LuaSyntaxError as e:
        # TODO: Log error here
        print(str(e))
        classification = "unknown"

    if classification not in ["major", "minor", "critical", "ok", "unknown"]:
        # TODO: Log error here
        classification = "unknown"

    return classification

def list_to_lua_array(input_list):
    lua_array = "{"
    for entry in input_list:
        if isinstance(entry, numbers.Number):
            lua_array += "{},".format(entry)
        else:
            lua_array += "\"{}\",".format(entry)
    lua_array = "{}}}".format(lua_array[:-1]) # Remove last comma
    return lua_array

if __name__ == "__main__":
    execute_classifier(example_function, {"ok", "ok", "fail", "fail", "ok"})
