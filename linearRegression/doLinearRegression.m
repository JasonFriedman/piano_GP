% DOLINEARREGRESSION - predict the improvement
%
% doLinearRegression(data,filename,weight,plotgraphs)
%
% Do it for both utility, and separate regression for the two measures
% 1 → calculate utility (defined as
% (error_after_timing - error_before_timing) + (error_after_pitch - error_before_pitch) - mean_utility
% [mean utility is currently set to 0.75] (default)
% 2 → do separate regression for error_after_timing, error_after_pitch
%
function [results,toSelect,selectednames,utility] = doLinearRegression(data,filename,weight,plotgraphs,withBPM)

if nargin<3 || isempty(weight)
    weight = 0.5;
end

if nargin<4 || isempty(plotgraphs)
    plotgraphs = 0;
end

if nargin<5 || isempty(withBPM)
    withBPM = 0;
end

% variables: bpm
% practice mode (0 = TIMING, 1 = PITCH)
% error_before_right_timing
% error_before_right_pitch
% page number (difficulty proxy)

% outcome - error_after_right_timing
%         - error_after_right_pitch

% double check the practice modes are as we expect
if ~all(strcmp(data.practice_mode,'IMP_TIMING') + strcmp(data.practice_mode,'IMP_PITCH'))
    error('some of the trials have practice modes that are not TIMING or PITCH');
end

%pagenumbers = cellfun(@(x) str2double(x{1}), regexp(data.midi_filename,'([1-9]*).*','tokens'));

practicemodes = strcmp(data.practice_mode,'IMP_PITCH');

utility = calculateUtility(data,weight);

if withBPM
    factors = [data.bpm' practicemodes' data.error_before_right_timing' data.error_before_right_pitch'];
    allnames = {'BPM','practicemode','errorbefore_timing','errorbefore_pitch'};
    factorNums = 1:4;
    t = table(data.bpm',practicemodes',data.error_before_right_timing',data.error_before_right_pitch',utility');
    t.Properties.VariableNames = {'BPM','PracticeMode','TimingError','PitchError','Utility'};
else
    factors = [practicemodes' data.error_before_right_timing' data.error_before_right_pitch'];
    allnames = {'practicemode','errorbefore_timing','errorbefore_pitch'};
    factorNums = 1:3;
    t = table(practicemodes',data.error_before_right_timing',data.error_before_right_pitch',utility');
    t.Properties.VariableNames = {'PracticeMode','TimingError','PitchError','Utility'};
    % for logistic regression
    
end


% If max == min, then there is no variation in that value so it is useless as a predictor (and causes warnings)
tokeep = max(factors) > min(factors);
factors = factors(:,tokeep);

numsUsed = factorNums(tokeep);

selectednames = allnames(tokeep);

outcome_timingerror = data.error_after_right_timing';
outcome_pitcherror = data.error_after_right_pitch';

t.PracticeMode = categorical(t.PracticeMode);

mdl_timingerror = fitlm(factors,outcome_timingerror);
mdl_pitcherror = fitlm(factors,outcome_pitcherror);
%mdl_utility = fitlm(factors,utility);
if withBPM
    mdl_utility = fitlm(t,'Utility~BPM+PracticeMode+TimingError+PitchError+PracticeMode*TimingError+PracticeMode*PitchError');
    mnr_utility = fitmnr(t,'PracticeMode~BPM+TimingError+PitchError');
else
    mdl_utility = fitlm(t,'Utility~PracticeMode+TimingError+PitchError+PracticeMode*TimingError+PracticeMode*PitchError');
    mnr_utility = fitmnr(t,'PracticeMode~TimingError+PitchError');
end
% Ideally we would use lasso to determine features, but there is not enough
% data for it to work
%[B,FitInfo] = lasso(factors,outcome1,'CV',10,'PredictorNames',selectednames);

predicted_timingerror = predict(mdl_timingerror);
predicted_pitcherror = predict(mdl_pitcherror);

% calculate utility based on what was selected
predicted_utility = predict(mdl_utility);

% using the logistic regression - timing=0 (false), pitch=1 (true) 
predicted_selection = double(predict(mnr_utility))-1;

% calculate utility for the both options
b = mdl_utility.Coefficients.Estimate;

% Timing = 0, pitch = 1

if withBPM
factors_pitch = [ones(size(t,1),1) data.bpm' ones(size(t,1),1) data.error_before_right_timing' ...
    data.error_before_right_pitch' data.error_before_right_timing' ...
    data.error_before_right_pitch'];
factors_timing = [ones(size(t,1),1) data.bpm' zeros(size(t,1),1) data.error_before_right_timing' ...
    data.error_before_right_pitch' zeros(size(t,1),2)];
else
    factors_pitch = [ones(size(t,1),1) ones(size(t,1),1) data.error_before_right_timing' ...
    data.error_before_right_pitch' data.error_before_right_timing' ...
    data.error_before_right_pitch'];
    factors_timing = [ones(size(t,1),1) zeros(size(t,1),1) data.error_before_right_timing' ...
    data.error_before_right_pitch' zeros(size(t,1),2)];
end

predicted_utility_pitch =  (b' * factors_pitch')';
predicted_utility_timing = (b' * factors_timing')';
toSelect(predicted_utility_timing > predicted_utility_pitch) = 0;
toSelect(predicted_utility_pitch > predicted_utility_timing) = 1;

%fprintf('0 = TIMING, 1 = PITCH\n');
%toSelect

if plotgraphs
    h = plotdata(data);

    h(4) = plot((1:numel(predicted_timingerror))+0.2,predicted_timingerror,'b*');
    h(5) = plot((1:numel(predicted_pitcherror))+0.2,predicted_pitcherror,'r*');
    h(6) = plot((1:numel(predicted_utility)),predicted_utility,'g*');
    legend(h,'timing error','pitch error','utility','timing after prediction','pitch after prediction','utility prediction','Location','NorthEast');

    if nargin>1 && ~isempty(filename)
        set(gcf,'PaperUnits','centimeters','PaperPosition',[0 0 40 30]);
        print('-depsc2',['figures/' filename]);
    end
end


if plotgraphs
    figure;
    subplot(1,3,1);
    plot(data.error_after_right_timing,predicted_timingerror,'.','MarkerSize',15);
    hold on;
    xlabel('Timing error after');
    ylabel('Predicted timing error after');
    axis equal;
    a = axis;
    plot(a(1:2),a(1:2),'k--');
    title(sprintf('R^2 = %.2f',mdl_timingerror.Rsquared.Ordinary));

    subplot(1,3,2);
    plot(data.error_after_right_pitch,predicted_pitcherror,'.','MarkerSize',15);
    hold on;
    xlabel('Pitch error after');
    ylabel('Predicted pitch error after');
    axis equal;
    a = axis;
    plot(a(1:2),a(1:2),'k--');
    title(sprintf('R^2 = %.2f',mdl_pitcherror.Rsquared.Ordinary));

    subplot(1,3,3);
    plot(utility,predicted_utility,'.','MarkerSize',15);
    hold on;
    xlabel('Utility');
    ylabel('Predicted utility');
    axis equal;
    a = axis;
    plot(a(1:2),a(1:2),'k--');
    title(sprintf('R^2 = %.2f',mdl_utility.Rsquared.Ordinary));

    if nargin>1 && ~isempty(filename)
        set(gcf,'PaperUnits','centimeters','PaperPosition',[0 0 40 10]);
        subplot(1,3,1); axis equal
        print('-depsc2',['figures/' filename '_Rsquared']);
    end
end

results.mdl_timingerror = mdl_timingerror;
results.mdl_pitcherror = mdl_pitcherror;
results.mdl_utility = mdl_utility;
results.mnr_utility = mnr_utility;
results.predicted_utility = predicted_utility;
results.predicted_selection = predicted_selection;
results.factors = factors;