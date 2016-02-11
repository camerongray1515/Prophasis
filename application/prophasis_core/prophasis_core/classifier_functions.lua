function arrayContains(array, value)
    for _, entry in ipairs(array) do
        if entry == value then
            return true
        end
    end
    return false
end

function arrayMax(array)
    table.sort(array)
    return array[#array]
end

function arrayMin(array)
    table.sort(array)
    return array[1]
end

function arrayAvg(array)
    sum = 0
    for _, entry in ipairs(array) do
        sum = sum + entry
    end
    return (sum / #array)
end
