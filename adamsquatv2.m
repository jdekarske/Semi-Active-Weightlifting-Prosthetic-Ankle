clear
close all

fid = fopen('C3ds\Subjects.txt');
subjectfile = textscan(fid, '%f %s %f'); %holds data specific to each subject, used for normalizing
fclose(fid);

myDir = uigetdir; %gets directory
myFiles = dir(fullfile(myDir,'*.c3d'));
for k = 1:length(myFiles) %loop though all files
clearvars -except k mydir myFiles subjectfile %persist
trial = myFiles(k,1).name;
subject = str2double(trial(1));

data = parseC3D([myFiles(k).folder '\' myFiles(k).name]); %handle data from c3d to matlab
data.Analogs = resample(data.Analogs,1,5); % cameras and forceplates at different frequencies
%see labeled force plates, 1 is north plate
fx1 = -data.Analogs(1:length(data.Analogs),1); %backwards from motive I guess
fy1 = -data.Analogs(1:length(data.Analogs),2);
fz1 = data.Analogs(1:length(data.Analogs),3);
mx1 = data.Analogs(1:length(data.Analogs),4);
my1 = data.Analogs(1:length(data.Analogs),5);
mz1 = data.Analogs(1:length(data.Analogs),6);
fx2 = -data.Analogs(1:length(data.Analogs),7);
fy2 = -data.Analogs(1:length(data.Analogs),8);
fz2 = data.Analogs(1:length(data.Analogs),9);
mx2 = data.Analogs(1:length(data.Analogs),10);
my2 = data.Analogs(1:length(data.Analogs),11);
mz2 = data.Analogs(1:length(data.Analogs),12);


%lazy way to fix fp noise and divide by zero
limit = 5;
a=-limit<fz1;
b=-limit<fz2;
fz1(a) = 0; %set low numbers to zero
fz2(b) = 0;
COP1x = zeros(length(fx1),2);
COP1y = zeros(length(fx1),2);
COP1x = -my1./fz1;
COP1y = mx1./fz1;
COP2x = zeros(length(fx2),2);
COP2y = zeros(length(fx2),2);
COP2x = -my2./fz2;
COP2y = mx2./fz2;

COP1x(a) = NaN; %set divide by zero to not a number
COP1y(a) = NaN;
COP2x(b) = NaN;
COP2x(b) = NaN;

%translate reference frames to global origin
%global origin at northwest corner of fp1
%fp origin at center
fp1dim = [.60, .60];
fp2dim = [.40, .60];
gap = .1035; %my very best measurement
COP1(:,2) = COP1x + fp1dim(1)/2; %note x and y swap...
COP1(:,1) = COP1y + fp1dim(2)/2;
COP2(:,2) = COP2x + fp2dim(1)/2;
COP2(:,1) = COP2y + (fp1dim(2)+gap+fp2dim(2)/2);
%plot(-(fz1+fz2)) %to figure out bodyweight manually

%% center of pressure graph
% hold on
% plot(COP1(:,1),COP1(:,2), 'r',COP2(:,1),COP2(:,2), 'g')
% rectangle('position',[0 0 .6 .6], 'facecolor', 'none');
% rectangle('position',[.7035 0 .6 .4], 'facecolor', 'none');
% axis equal

%% Finding ankle moment
Rankle = (data.Marker.MarkerSet_RFM+data.Marker.MarkerSet_RFL)./2; %get the center of the ankle
Rankle = [-Rankle(:,2),Rankle(:,1),Rankle(:,3)]; %I need to standardize this oh my god
Lankle = (data.Marker.MarkerSet_LFM+data.Marker.MarkerSet_LFL)./2;
Lankle = [-Lankle(:,2),Lankle(:,1),Lankle(:,3)];

Rmom_arm = [Rankle(:,1:2) - COP1 zeros(length(Rankle),1)]; %from ankle center to COP in xy plane
Lmom_arm = [Lankle(:,1:2) - COP2 zeros(length(Lankle),1)];
Rforce = [fz1 zeros(length(Rankle),1) zeros(length(Rankle),1)]; %so the cross product cooperates
Lforce = [fz2 zeros(length(Lankle),1) zeros(length(Lankle),1)];

Rankmom = cross(Rmom_arm,Rforce);
Rankmom = Rankmom(:,3);
Lankmom = cross(Lmom_arm,Lforce);
Lankmom = Lankmom(:,3);

%ankle angle calc
RShank_v = data.Marker.MarkerSet_RST - data.Marker.MarkerSet_RSB; %vector from bottom shank marker to top
RShank_v = [-RShank_v(:,2),RShank_v(:,1),RShank_v(:,3)];
LShank_v = data.Marker.MarkerSet_LST - data.Marker.MarkerSet_LSB;
LShank_v = [-LShank_v(:,2),LShank_v(:,1),LShank_v(:,3)];

up = [zeros(length(RShank_v),2) ones(length(RShank_v),1)];
Rang = atan2d( cross(RShank_v,up) , dot(RShank_v',up')' ); %stupid functions...angle between up axis
nRang = sqrt(sum(Rang'.^2))';
Lang = atan2d( cross(LShank_v,up) , dot(LShank_v',up')' ); %stupid functions
nLang = sqrt(sum(Lang'.^2))';

%only plot the good stuff
f1 = figure;
figure(f1)
plot(-[fz1 fz2])
title('select the squat region')
pts = round(ginput(2));
close
figure(subject)
hold on
plot(nRang(pts(1,1):pts(2,1)),(Rankmom(pts(1,1):pts(2,1))/subjectfile{3}(subject)))%only plot right for now, 'r',nLang(pts(1,1):pts(2,1)), Lankmom(pts(1,1):pts(2,1)), 'g')
title(['Subject: ' num2str(subject)])
xlabel('Shin Angle (degrees)')
ylabel('Ankle Torque/bodyweight (N/m/N)')
hold off
%add something to save figures
end
