% Analysis for paper
if ~exist('./figures','dir')
    mkdir('figures')
end

% Load data
data1 = readdata('../subject1.h5');
data2 = readdata('../subject2.h5');
data3 = readdata('../subject3.h5');
data4 = readdata('../subject4.h5');
data5 = readdata('../subject5.h5');
data6 = readdata('../subject6.h5');

combined = combine(data1,data2,data3,data4,data5,data6);


%% Do the linear regression

w = 0:0.01:1;
for k=1:numel(w)
    [results(k),selected(k,:),factorNames,utility(k,:)] = doLinearRegression(combined,'combined',w(k),0,0);
    [results_with_BPM(k),selected_with_BPM(k,:),factorNames_with_BPM,utility_with_BPM(k,:)] = doLinearRegression(combined,'combined',w(k),0,1);
end

for k=1:numel(w)
    predicted_selection(k,:) = results(k).predicted_selection';
    predicted_selection_withBPM(k,:) = results_with_BPM(k).predicted_selection';
end

%%

% CALCULATE THE ACCURACY AND PICK THE BEST ONE

% 0 = timing, 1 = pitch
groundtruth = strcmp(combined.practice_mode,'IMP_PITCH');

% calculate the difference

errors = sum(abs(selected - repmat(groundtruth,numel(w),1)),2) ./ size(selected,2) * 100;
errors_withBPM = sum(abs(selected_with_BPM - repmat(groundtruth,numel(w),1)),2) ./ size(selected,2) * 100;

errors_logistic = sum(abs(predicted_selection - repmat(groundtruth,numel(w),1)),2) ./ size(selected,2) * 100;
errors_logistic_BPM = sum(abs(predicted_selection_withBPM - repmat(groundtruth,numel(w),1)),2) ./ size(selected,2) * 100;

accuracy = 100-errors;
accuracy_withBPM = 100-errors_withBPM;

% They are all the same for the logistic regression because a does not
% feature in the equation
accuracy_logistic = 100-errors_logistic(1);
accuracy_logistic_BPM = 100-errors_logistic_BPM(1);

%% Make a graph similar to the GP one
practicemode_PITCH = strcmp(combined.practice_mode,'IMP_PITCH');
practicemode_TIMING = strcmp(combined.practice_mode,'IMP_TIMING');
figure;
ms = 10;
h(1) = plot(combined.error_before_right_timing(practicemode_PITCH),combined.error_before_right_pitch(practicemode_PITCH),'.','Color',[0.5 0 0.5],'MarkerSize',ms);
hold on;
h(2) = plot(combined.error_before_right_timing(practicemode_TIMING),combined.error_before_right_pitch(practicemode_TIMING),'y.','MarkerSize',ms);
set(gca,'Color',0.7 * [1 1 1]);
axis([0 1 0 1]);
legend('pitch practice mode','timing practice mode');
xlabel('Error timing');
ylabel('Error pitch');
set(gcf,'PaperUnits','centimeters','PaperPosition',[0 0 15 15]);
%exportgraphics(gca,'figures/experimentsummary.png')
set(gcf, 'InvertHardcopy', 'off');
print('-dpng','figures/experimentsummary');

%% Make a graph of predicted vs actual utility (this is what the linear regression does)
% select w=0.5;
n = find(w==0);
yellow = [0.9 0.9 0]; purple = [0.3 0 0.3];

ms = 10;

actual_utility = utility(n,:);

practicemodes = strcmp(combined.practice_mode,'IMP_PITCH');
before_timing = combined.error_before_right_timing; 
before_pitch = combined.error_before_right_pitch;

predicted_utility = results(n).predicted_utility;

figure;
plot(actual_utility(practicemodes),predicted_utility(practicemodes),'.','Color',purple,'MarkerSize',ms);
hold on;
plot(actual_utility(~practicemodes),predicted_utility(~practicemodes),'.','Color',yellow,'MarkerSize',ms)
set(gca,'Color',0.7 * [1 1 1]);
axis equal
ax = axis;
plot(ax(1:2),ax(1:2),'k--');
xlabel('Actual utility');
ylabel('Predicted utility');
legend('pitch practice mode','timing practice mode','Location','NorthWest');
set(gcf,'PaperUnits','centimeters','PaperPosition',[0 0 15 15]);
%exportgraphics(gca,'figures/experimentsummary.png')
set(gcf, 'InvertHardcopy', 'off');
print('-dpng','figures/actual_vs_predicted_utility');


%% Make a graph of the linear regression predictions (similar to the GP one) - without BPM
tocheck = 0:0.01:1; % check 100 values in each dimension
n=14;

clear bestpracticemode;

for a=numel(tocheck):-1:1
    for b=numel(tocheck):-1:1
        error_timing((a-1)*numel(tocheck)+b,1) = tocheck(a);
        error_pitch((a-1)*numel(tocheck)+b,1) = tocheck(b);
    end
end

% Need to provide according to results(1).mdl_utility.PredictorNames
% which is Practice mode, timing error, pitch error
pitchutility_raw = feval(results(n).mdl_utility,categorical(true(numel(error_timing),1)),error_timing,error_pitch);
timingutility_raw = feval(results(n).mdl_utility,categorical(false(numel(error_timing),1)),error_timing,error_pitch);

% X axis is timing error (column), Y axis is pitch error (row)
pitchutility = reshape(pitchutility_raw,101,101);
timingutility = reshape(timingutility_raw,101,101);

bestpracticemode = pitchutility>timingutility;
%%
yellow = [0.9 0.9 0]; purple = [0.3 0 0.3];

figure;
image(bestpracticemode)
set(gca,'YDir','normal')
% 0.9 0.9 0 = yellow
% 0.3 0 0.3 = purple
colormap(gca,[yellow;purple]);
set(gca,'XTick',20:20:100,'XTickLabel',0.2:0.2:1,'YTick',20:20:100,'YTick',20:20:100,'YTickLabel',0.2:0.2:1);
clear h;
hold on;
h(1) = plot(500,500,'s','MarkerSize',20,'Color',purple,'MarkerFaceColor',purple);
h(2) = plot(501,501,'s','MarkerSize',20,'Color',yellow,'MarkerFaceColor',yellow);
axis([1 100 1 100]);
xlabel('error\_timing');
ylabel('error\_pitch');
legend(h,'IMP\_PITCH','IMP\_TIMING');
set(gcf,'PaperUnits','centimeters','PaperPosition',[0 0 15 15]);
print('-depsc','figures/linearRegressionBestPracticeMode');
print('-dpng','figures/linearRegressionBestPracticeMode');

%% Make a graph of the linear regression predictions (similar to the GP one) - without BPM
% for the teacher predictions model
tocheck = 0:0.01:1; % check 100 values in each dimension
n=14;

clear bestpracticemode;

for a=numel(tocheck):-1:1
    for b=numel(tocheck):-1:1
        error_timing((a-1)*numel(tocheck)+b,1) = tocheck(a);
        error_pitch((a-1)*numel(tocheck)+b,1) = tocheck(b);
    end
end

% Don't need to provide all these - rather need to provide
% according to results(1).mdl_utility.PredictorNames
% which is Practice mode, timing error, pitch error
bestpracticemode_raw = feval(results(n).mnr_utility,error_timing,error_pitch);
% X axis is timing error (column), Y axis is pitch error (row)
bestpracticemode = reshape(bestpracticemode_raw,101,101);

%%
thisbestpracticemode = double(bestpracticemode);

yellow = [0.9 0.9 0]; purple = [0.3 0 0.3];

figure;
image(thisbestpracticemode)
set(gca,'YDir','normal')
% 0.9 0.9 0 = yellow
% 0.3 0 0.3 = purple
colormap(gca,[yellow;purple]);
set(gca,'XTick',20:20:100,'XTickLabel',0.2:0.2:1,'YTick',20:20:100,'YTick',20:20:100,'YTickLabel',0.2:0.2:1);
clear h;
hold on;
h(1) = plot(500,500,'s','MarkerSize',20,'Color',purple,'MarkerFaceColor',purple);
h(2) = plot(501,501,'s','MarkerSize',20,'Color',yellow,'MarkerFaceColor',yellow);
axis([1 100 1 100]);
xlabel('error\_timing');
ylabel('error\_pitch');
legend(h,'IMP\_PITCH','IMP\_TIMING');
set(gcf,'PaperUnits','centimeters','PaperPosition',[0 0 15 15]);
print('-depsc','figures/logisticRegressionBestPracticeMode');
print('-dpng','figures/logisticRegressionBestPracticeMode');

%% Make a graph of the linear regression predictions (similar to the GP one) - varying BPM
tocheck = 0:0.01:1; % check 100 values in each dimension

BPMs = 50:10:100;
for bpmlevel = 1:6
    BPM = BPMs(bpmlevel);

    tocheck = 0:0.01:1; % check 100 values in each dimension
    n=14;

    clear bestpracticemode;

    for a=numel(tocheck):-1:1
        for b=numel(tocheck):-1:1
            error_timing((a-1)*numel(tocheck)+b,1) = tocheck(a);
            error_pitch((a-1)*numel(tocheck)+b,1) = tocheck(b);
        end
    end

    % Need to provide according to results_with_BPM(1).mdl_utility.PredictorNames
    % which is BPM, Practice mode, timing error, pitch error
    pitchutility_raw = feval(results_with_BPM(n).mdl_utility,BPM,categorical(true(numel(error_timing),1)),error_timing,error_pitch);
    timingutility_raw = feval(results_with_BPM(n).mdl_utility,BPM,categorical(false(numel(error_timing),1)),error_timing,error_pitch);

    % X axis is timing error (column), Y axis is pitch error (row)
    pitchutility = reshape(pitchutility_raw,101,101);
    timingutility = reshape(timingutility_raw,101,101);

    bestpracticemode = pitchutility>timingutility;
    bestpracticemodes{bpmlevel} = bestpracticemode;
end

%%
yellow = [0.9 0.9 0]; purple = [0.3 0 0.3];

figure;
for bpmlevel=1:6
    subplot(2,3,bpmlevel);
    image(bestpracticemodes{bpmlevel})
    set(gca,'YDir','normal')
    % 0.9 0.9 0 = yellow
    % 0.3 0 0.3 = purple
    colormap(gca,[yellow;purple]);
    set(gca,'XTick',20:20:100,'XTickLabel',0.2:0.2:1,'YTick',20:20:100,'YTick',20:20:100,'YTickLabel',0.2:0.2:1);
    clear h;
    hold on;
    h(1) = plot(500,500,'s','MarkerSize',20,'Color',purple,'MarkerFaceColor',purple);
    h(2) = plot(501,501,'s','MarkerSize',20,'Color',yellow,'MarkerFaceColor',yellow);
    axis([1 100 1 100]);
    xlabel('error\_timing');
    ylabel('error\_pitch');
    if b==6
        legend(h,'IMP\_PITCH','IMP\_TIMING');
    end
    title(sprintf('BPM = %d',BPMs(bpmlevel)));
end
set(gcf,'PaperUnits','centimeters','PaperPosition',[0 0 30 15]);
print('-depsc','figures/linearRegressionBestPracticeModeBPM');
print('-dpng','figures/linearRegressionBestPracticeModeBPM');