import lupa
import json
import numbers

example_function = """
if arrayContains(values, "fail") then
    return "critical"
else
    return "ok"
end
"""

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

    print(lua.execute(full_code))

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
