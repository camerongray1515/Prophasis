import lupa
import json
import numbers
import os
from models import PluginThreshold, PluginResult
from application_logging import log_message

def execute_classifier(code, values, messages, result_types):
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
    full_code += "messages={}\n".format(list_to_lua_array(messages))
    full_code += "result_types={}\n".format(list_to_lua_array(result_types))
    with open(os.path.join(os.path.dirname(__file__),
        "classifier_functions.lua"), "r") as f:
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
        log_message("Classification", "No classifier code could be found for "
            "plugin: {}".format(latest_result.plugin_id))
        return "unknown"

    # Get n-1 historical values and then append the latest onto this list
    historical_values = PluginResult.query.filter(
        PluginResult.plugin_id == latest_result.plugin_id,
        PluginResult.host_id == latest_result.host_id).order_by(
            PluginResult.id.desc()
        ).limit(threshold.n_historical-1).all()

    values_list = []
    messages_list = []
    result_types_list = []
    for value in historical_values:
        values_list.append(value.value)
        messages_list.append(value.message)
        result_types_list.append(value.result_type)
    values_list.append(latest_result.value)
    messages_list.append(latest_result.message)
    result_types_list.append(latest_result.result_type)

    try:
        classification = execute_classifier(threshold.classification_code,
            values_list, messages_list, result_types_list)
    except (lupa._lupa.LuaSyntaxError, lupa._lupa.LuaError) as e:
        log_message("Classification",
            "Classification code for plugin {} gave error: {}".format(
            latest_result.plugin_id, str(e)))
        classification = "unknown"

    if classification not in ["major", "minor", "critical", "ok", "unknown"]:
        log_message("Classification", "\"{}\" is not a valid classification for"
            " plugin {}".format(classification, latest_result.plugin_id))
        classification = "unknown"

    return classification

def list_to_lua_array(input_list):
    lua_array = "{"
    for entry in input_list:
        if entry == None:
            lua_array += "nil,"
        elif isinstance(entry, numbers.Number):
            lua_array += "{},".format(entry)
        else:
            lua_array += "\"{}\",".format(entry.replace("\"", "\\\""))
    lua_array = "{}}}".format(lua_array[:-1]) # Remove last comma
    return lua_array

if __name__ == "__main__":
    execute_classifier(example_function, {"ok", "ok", "fail", "fail", "ok"})
