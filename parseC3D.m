function out = parseC3D(filename, varargin)
% out = parseC3D(filename, varargin)
% 
% optional input pairs: 
%     'swZero', (1 or 0, default 0): tells whether or not to allow a
%     Software Zero
%     'copOverhang' (default 5): how many force plates away from FP center
%     is the COP allowed to be, before we cut it off (because it explodes
%     with low FZ)

% default Parameters
swZero = 0;
copOverhang = 5;

% assign varargin, to overwrite default values if required
assigned = varargassign(varargin{:});


try
	itf = actxserver('C3DServer.C3D');  % makes "itf" a COM object for the "c3dserver" package
catch
	itf = btkEmulateC3Dserver();  % use BTK emulation of C3DServer
end
openc3d(itf, 0, filename)    % applies the correct open options to the file you choose

% Get Basic Parameters from C3D file
frames = nframes(itf);  % calculates and displays the number of video frames
frate = itf.GetParameterIndex('POINT','RATE'); %% get Index for the Frame Rate
frate = double(itf.GetParameterValue(frate, 0));  % get value of the Frame Rate
avrat = itf.GetAnalogVideoRatio();

% Find Units for Motion Capture
markerUnits = itf.GetParameterIndex('POINT','UNITS');
markerUnits = itf.GetParameterValue(markerUnits, 0);
if any(strcmp('mm',markerUnits)) % then the units are mm
    markerUnitScalingFactor = 1/1000; % want units in Meters
else
    markerUnitScalingFactor = 1;
end

% Find Units of Moments
analogUnitsInd = itf.GetParameterIndex('ANALOG','UNITS');
if analogUnitsInd ~= -1
    analogUnitsLength = itf.GetParameterLength(analogUnitsInd);
    for ii = 1:analogUnitsLength
        analogUnits{ii} = itf.GetParameterValue(analogUnitsInd, ii-1);
    end
    if any(strcmp('Nmm',analogUnits)) % then the units are mm
        momentUnitScalingFactor = 1/1000; % want units in Nm
    else
        momentUnitScalingFactor = 1;
    end
end



%% Get Force Platform Corners and Origin (to rebuild the COP)
% Corners: 1,2,3,4 designate the Quadrant of each corner according to the FP coordinate System (but the values actually stored locate those same corners, in order, in the Mocap reference frame). 
cornersparmind = itf.GetParameterIndex('FORCE_PLATFORM','CORNERS');
if cornersparmind ~= -1
    cornersparmlength = itf.GetParameterLength(cornersparmind);
    corners = zeros(3,cornersparmlength/3);
    for ii = 1:cornersparmlength
        corners(ii) = double(itf.GetParameterValue(cornersparmind,ii-1))*markerUnitScalingFactor;
    end
end
% Origin: Vector from Force Plate Origin to Center of the FP Working Surface, in FP Coordinate System. 
% Supposedly the Z-direction should be Negative. (so says the C3D User Manual)
% and Notably, it should be in the Force Plate Reference Frame. 
originparmind = itf.GetParameterIndex('FORCE_PLATFORM','ORIGIN');
if originparmind ~= -1
    originparmlength = itf.GetParameterLength(originparmind);
    origin = zeros(3,originparmlength/3);
    for ii = 1:originparmlength
        origin(ii) = double(itf.GetParameterValue(originparmind,ii-1))*markerUnitScalingFactor;
    end
end

%% Get Marker Data
iLabels = itf.GetParameterIndex('POINT','LABELS');
iDescriptions = itf.GetParameterIndex('POINT','DESCRIPTIONS');
nTargets = itf.GetParameterLength(iLabels);
for ii = 1:nTargets
    Labels{ii} = itf.GetParameterValue(iLabels,ii-1);
    if iDescriptions >= 0
        Descriptions{ii} = itf.GetParameterValue(iDescriptions,ii-1);
    else
        Descriptions{ii} = Labels{ii};
    end
    for jj = 1:3
        Data{ii}(:,jj) = double(cell2mat(itf.GetPointDataEx(ii-1, jj-1, 1, frames, char(1))))*markerUnitScalingFactor ;
    end
    if length(Descriptions{ii}) > length(Labels{ii}) 
        Labels{ii} = strrep(Descriptions{ii},' ','') ;
    end
    Labels{ii} = strrep(Labels{ii},' ','');
    Labels{ii} = strrep(Labels{ii},'*','t') ;
    if any(Data{ii}(:)) % some files come with a bunch of empty markers. Lame! This keeps them from being created. 
        out.Marker.(Labels{ii}) = Data{ii};
        out.Marker.(Labels{ii})(out.Marker.(Labels{ii})==0) = NaN; % when they jump to the origin, that is no good. Make them disappear instead. 
    end
end

% old way
% out.Marker = get3dtargets(itf);
% out.Marker = rmfield(out.Marker,'units');

%% Get the Forces
zerosparmind = itf.GetParameterIndex('FORCE_PLATFORM','ZEROS');
zeroparmind = itf.GetParameterIndex('FORCE_PLATFORM','ZERO');
FPusedind = itf.GetParameterIndex('FORCE_PLATFORM','USED');
FPchannelind = itf.GetParameterIndex('FORCE_PLATFORM','CHANNEL');
	
if zeroparmind ~= -1
	zeroregion(1) = itf.GetParameterValue(zeroparmind, 0);
	zeroregion(2) = itf.GetParameterValue(zeroparmind, 1);
	nFP = itf.GetParameterValue(FPusedind,0); % number of force plates
   nFPchannels = itf.GetParameterLength(FPchannelind);
    
    FPchannels = zeros(6,nFP); 
    for ii = 1:nFPchannels
        FPchannels(ii) = itf.GetParameterValue(FPchannelind,ii-1);
    end
    FPchannels = FPchannels'; % restore it to the orientation specified by C3D. 

    
    % Get Raw Analogs (for manual computation of Moment and COP)
    % Old Way (using the getanalogchannels function): % analogs = getanalogchannels(itf);
    nItems = itf.GetAnalogChannels();
    scaleInd = itf.GetParameterIndex('ANALOG','SCALE');
    gscaleInd = itf.GetParameterIndex('ANALOG','GEN_SCALE');
    gscale = double(itf.GetParameterValue(gscaleInd,0));
    for ii = 1 : nItems
        scales(ii) = double(itf.GetParameterValue(scaleInd,ii-1))*gscale;
        analogs(:,ii) = scales(ii)*double(cell2mat(itf.GetAnalogDataEx(ii-1,1,frames,char(0),0,0,char(0)))); % char(1) instead of the first char(0) gets "scaled" analogs. 
    end
    out.Analogs = analogs;
    
   
    
end

