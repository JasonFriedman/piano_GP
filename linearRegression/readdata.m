% READDATA -read the data from the h5 file
function results = readdata(filename)

data = py.pandas.read_hdf(filename);
columnsPy = data.columns.tolist();
for k=1:columnsPy.length
    column{k} = char(columnsPy{k});
end

pyList = data.values.tolist();
for k=1:pyList.length
    for m=1:numel(column)
        if isa(pyList{k}{m},'double')
            results.(column{m})(k) = double(pyList{k}{m});
        else
            results.(column{m}){k} = char(pyList{k}{m});
        end
    end
end