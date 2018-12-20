clear
data = importpressure('pressures.csv');
difference = diff(data.cyl);
dur = data.dur(1:end-1);
cyl = data.cyl(1:end-1);
difference2 = -difference(difference<1 & cyl>20 );
dur = dur(difference<1& cyl>20);
cyl=cyl(difference<1& cyl>20);
%scatter(data.dur(1:end-1),data.cyl(1:end-1), 10, difference)