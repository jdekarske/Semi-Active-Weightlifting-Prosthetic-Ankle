function out = varargassign(varargin)
% call from another function to assign a bunch of inputs in "varargin" in {name, value} pairs: 
% varargassign(varargin{:});

try
    for ii = 1:2:length(varargin)
        assignin('caller', varargin{ii}, varargin{ii+1});
    end
    out = 0;
catch
    out = -1;
end
