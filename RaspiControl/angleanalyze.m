clear
close all
data = importangles("pressurechange.csv");
plot(data.cyl)
hold on
plot(data.res)
plot(data.com)
plot(data.mode)