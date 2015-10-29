-- The following arrays are provided which contain data collected by the plugin
-- values: Array of "values" returned by the plugin
-- messages: Array of "messages" returned by the plugin
-- result_types: Array with "plugin" for a successful check or the following error values:
--    "command_unsuccessful", "authentication_error", "request_error", "connection_error", "connection_timeout"
if arrayContains(values, nil) then
	return "unknown"
end

maxValue = arrayMax(values)

if maxValue >= 100 then
    return "critical"
elseif maxValue >= 90 then
	return "major"
elseif maxValue >= 50 then
	return "minor"
else
	return "ok"
end
