% COMBINE - combine two data sets

function combined = combine(varargin)

f = fields(varargin{1});

for k=1:numel(f)
    for n=1:numel(varargin)
        if n==1
            combined.(f{k}) = varargin{1}.(f{k});
        else
            combined.(f{k}) = [combined.(f{k}) varargin{n}.(f{k})];
        end
    end
end