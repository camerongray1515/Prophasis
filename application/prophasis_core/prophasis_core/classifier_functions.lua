function arrayContains(array, value)
    for _, entry in ipairs(array) do
        if entry == value then
            return true
        end
    end
    return false
end

function arrayMax(array)
    max = nil
    for _, entry in ipairs(array) do
        if not (entry == "none") then
            if max == nil or entry > max then
                max = entry;
            end
        end
    end
    return max
end

function arrayMin(array)
    min = nil
    for _, entry in ipairs(array) do
        if not (entry == "none") then
            if min == nil or entry < min then
                min = entry;
            end
        end
    end
    return min
end

function arrayAvg(array)
    sum = 0
    for _, entry in ipairs(array) do
        if (entry == "none") then
            sum = sum + entry
        end
    end
    return (sum / #array)
end
