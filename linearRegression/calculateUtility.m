function utility = calculateUtility(data,weight,MEAN_UTILITY)

if nargin<3
    MEAN_UTILITY = 0.75;
end

diff_timing = data.error_after_right_timing - data.error_before_right_timing;
diff_pitch = data.error_after_right_pitch - data.error_before_right_pitch;

MEAN_UTILITY = 0.75;

%if weight<0 || weight>1
%    error('Weight must be between 0 (only pitch) and 1 (only timing)');
%end

utility = - (diff_timing*weight + diff_pitch*(1-weight)) - MEAN_UTILITY;

% Based on this python code:
% def error_diff_to_utility(error_pre, error_post):
%    diff_timing = error_post.timing - error_pre.timing
%    diff_pitch  = error_post.pitch  - error_pre.pitch
%    
%    
%    MEAN_UTILITY = 0.75
%    
%    return - (diff_timing*1 + diff_pitch*1) - MEAN_UTILITY
