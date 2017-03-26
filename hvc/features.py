import numpy as np
from matplotlib.mlab import specgram

def extract_svm_features(syls,fs,nfft=256,spmax=128,overlap=192,minf=500,
                         maxf=6000):
    """
    Extracts acoustic features from waveform representing a songbird syllable.
    Based on Matlab code written by R.O. Tachibana (rtachi@gmail.com) in Sept.
    2013. These features were previously shown to be effective for classifying
    Bengalese finch song syllables [1]_. Note all defaults for the spectrogram
    are taken from the Tachibana code and paper.

    Parameters
    ----------
    syls : Python list of numpy vector
        each vector is the raw audio waveform of a segmented syllable
    fs : integer
        sampling frequency
    nfft : integer
        number of samples for each Fast Fourier Transform (FFT) in spectrogram.
        Default is 256.
    spmax : integer
        Default is 128.
    overlap : integer
        number of overlapping samples in each FFT. Default is 192.
    minf : integer
        minimum frequency in FFT
    maxf : integer
        maximum frequency in FFT

    Returns
    -------
    feature_arr : numpy array
            with dimensions of n (number of syllables) x 532 acoustic features

    References
    ----------
    .. [1] Tachibana, Ryosuke O., Naoya Oosugi, and Kazuo Okanoya. "Semi-
    automatic classification of birdsong elements using a linear support vector
     machine." PloS one 9.3 (2014): e92584.

    """
    NUM_FEATURES = 532
    num_syls = len(syls)
    feature_arr = np.empty((num_syls,NUM_FEATURES))
    for syl in syls:
        #make sure syl is a numpy array
        syl = np.asarray(syl)
        
        #extract duration of syllable
        dur = syl.shape[0]/fs

        # spectrogram and cepstrum
        syl_diff = np.diff(syl) # Tachibana applied a differential filter
        # note that the matlab specgram function returns the STFT by default
        # whereas the default for the matplotlib.mlab version of specgra
        # returns the PSD. So to get the behavior of matplotlib.mlab.specgram
        # to match, mode must be set to 'complex'
        power,freqs = specgram(syl_diff,NFFT=nfft,Fs=fs,window=np.hanning(nfft),
                       noverlap=overlap,
                       mode='complex')[0:2]  # don't keep returned time vector
        spectrum = 20*np.log10(np.abs(power[1:,:]))
        mean_spectrum = np.mean(spectrum,axis=1)

        power2 = np.vstack((power,np.flipud(power[1:-1,:])))
        real_cepstrum = np.real(np.fft.fft(np.log10(np.abs(power2)), axis=0))
        # ^ by this step, everything after the decimal point is already difft 
        # from what matlab returns
        really_real_cepstrum = real_cepstrum[1:nfft/2+1,:]
        mean_cepstrum = np.mean(really_real_cepstrum, axis=1)

        # 5-order delta
        if syl.shape[-1] < (5 * nfft - 4 * overlap):
            delta_spectrum = np.zeros(spmax,1)
            delta_cepstrum = np.zeros(spmax,1)
        else:
            delta = lambda x: -2 * x[:, :-4] - 1 * x[:, 1:-3] + 1 * x[:, 3:-1] + 2 * x[:, 4:]
            delta_spectrum = delta(spectrum)
            delta_cepstrum = delta(really_real_cepstrum)

        # mean
        mean_delta_spectrum = np.mean(np.abs(delta_spectrum),axis=1)
        mean_delta_cepstrum = np.mean(np.abs(delta_cepstrum),axis=1)

        maxq = np.round(fs/minf)*2
        minq = np.round(fs/maxf)*2
        num_rows, num_cols = power.shape
        mat = np.matlib.repmat(freqs,1,num_cols)
        # amplitude spectrum
        amplitude_spectrum = np.abs(power)
        # probability
        p = amplitude_spectrum / np.matlib.repmat(np.sum(amplitude_spectrum,1),num_rows,1)
        # 1st moment: centroid (mean of distribution)
        m1 = np.sum(mat * p,1)
        # 2nd moment: variance (ƒÐ^2)
        m2 = np.sum((np.power(mat - np.matlib.repmat(m1,nr,1),2)) * p, 1)
        # 3rd moment
        m3 = np.sum((np.power(mat - np.matlib.repmat(m1,nr,1),3)) * p, 1)
        # 4th moment
        m4 = np.sum((np.power(mat - np.matlib.repmat(m1,nr,1),4)) * p, 1)
        # distribution parameters
        SpecCentroid = m1  # mean
        SpecSpread = np.power(m2,1/2)  # standard deviation
        SpecSkewness = m3 / np.power(m2,3/2)
        SpecKurtosis = m4 / np.power(m2,2)
        # entropy
        SpecFlatness = np.exp(np.mean(np.log(s),1)) / np.mean(s,1)
        # slope
        SpecSlope = np.zeros((1,nc))
        mat2 = np.horzcat((F,np.ones((nr,1))))
        for n in range(nc):
            beta = np.linalg.solve((mat2.T * mat2), mat2.T*s[:, n])
            SpecSlope[n] = beta[1]

        # cepstral pitch and pitch goodness
        exs = np.vertcat((s,repmat(s(end,:),nfft,1),flipud(s(2:end-1,:)))
        C = real(fft(log10(exs)))
        [mv,mid] = np.max(C(minq:maxq,:))
        Pitch = fs./(mid+minq-1)
        PitchGoodness = mv
        # amplitude in dB
        Amp = 20*log10(sum(s)/nfft)

        # 5-order delta
        A = np.horzcat((SpecCentroid.T,SpecSpread.T,SpecSkewness.T,SpecKurtosis.T,
                        SpecFlatness.T,SpecSlope.T,Pitch.T,PitchGoodness.T,Amp.T)
        d5A = -2*A[1:-4,:]-1*A[2:-3,:]+1*A[4:-1,:]+2*A[5:,:]

        # zerocross (in Hz)
        zc = np.length(np.find(np.diff(sign(syl)) != 0))/2
        ZeroCross = zc / dur

        # mean
        mA = np.horzcat((np.mean(A,1),ZeroCross,np.mean(np.abs(d5A),1))
        mA[np.isnan(mA)] = 0

        # output
        features = np.horzcat((mean_spectrum,
                               mean_delta_spectrum,
                               mean_cepstrum,
                               mean_delta_cepstrum,
                               dur,
                               mA))
    return features

