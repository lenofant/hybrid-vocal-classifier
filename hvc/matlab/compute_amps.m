function [amp_sm_rect,amp_rms] = compute_amps(raw_syl,Fs,win_duration,overlap)
%compute_amps
%   computes two types of amplitude from raw voltage waveform
%   
%   input arguments:
%       raw_syl -- voltage waveform from .cbin file, e.g., syllable
%           extracted by make_spect_files function
%       Fs -- sampling frequency
%       win_duration --
%       overlap --
%
%       Note that Fs, win_duration, and overlap should be taken from .spect.mat 
%       files generated by make_spect_files function

smooth_syl = evsmooth(raw_syl,Fs,0);

win_duration_in_Fs = round((win_duration/1000) * Fs);
overlap_in_Fs = win_duration_in_Fs * overlap;
hop_size = win_duration_in_Fs - overlap_in_Fs;

amp_sm_rect = [];
amp_rms = [];

%if raw_syl cannot be divided into an integer number of segments of
%length (win_duration - overlap), then find the number of segments it can be
%divided into, round down to the nearest integer, and use the index of the
%first element of that last full-length segment as the last value in a loop
%i.e., truncate raw_syl in the same way that spectrogram does, so that the
%amplitude vector will have the same number of elements as the time_bin
%vector
num_segments = floor((length(raw_syl) - overlap_in_Fs) / hop_size);
indices_vector = 1:hop_size:length(raw_syl);

for indexing_index = 1:num_segments
    start_id = indices_vector(indexing_index);
    end_id = start_id + win_duration_in_Fs - 1;
    amp_sm_rect = [amp_sm_rect mean(smooth_syl(start_id:end_id))];
    
    raw_bin = raw_syl(start_id:end_id);
    bin_rmsd = sqrt(mean(raw_bin.^2));
    amp_rms = [amp_rms bin_rmsd];
end
end