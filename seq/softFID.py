import configs.hw_config as hw
import seq.mriBlankSeq as blankSeq
import numpy as np
import controller.experiment_gui as ex


class SoftFID(blankSeq.MRIBLANKSEQ):
    def __init__(self):
        super(SoftFID, self).__init__()
        # Input the parameters
        self.addParameter(key='seqName', string='FIDinfo', val='SoftFID')
        self.addParameter(
            key='larmorFreq', string='中心频率 (MHz)', val=hw.larmorFreq, field='RF')
        self.addParameter(
            key='rfAmpMin', string='激发功率下限 (a.u.)', val=0.06, field='RF')
        self.addParameter(
            key='rfAmpMax', string='激发功率上限 (a.u.)', val=0.08, field='RF')
        self.addParameter(
            key='rfExTime', string='激发脉冲宽度 (ms)', val=50.0, field='RF')
        self.addParameter(
            key='rfLobes', string='sinc波峰个数 (0为方波)', val=0, field='RF')
        self.addParameter(key='shimming', string='线性匀场',
                          val=[0, 0, 666], field='OTH')
        self.addParameter(key='repetitionTime',
                          string='TR(ms)', val=500, field='SEQ')
        self.addParameter(key='nScan', string='循环次数', val=10, field='SEQ')

    def sequenceInfo(self):
        print("用软脉冲的FID")

    def sequenceTime(self):
        return self.mapVals['repetitionTime'] * self.mapVals['nScan'] / 1e3  # sec

    def sequenceRun(self, plotSeq=0):
        larmorFreq = self.mapVals['larmorFreq']  # MHz
        rfAmpMin = self.mapVals['rfAmpMin']
        rfAmpMax = self.mapVals['rfAmpMax']
        if rfAmpMin > rfAmpMax:
            print('Minimum RF amplitude must be smaller than maximum!')
            return 0
        rfExTime = self.mapVals['rfExTime']  # us
        shimming = np.array(self.mapVals['shimming'])*1e-4
        shimmingTime = 2e3  # us
        nPoints = 100
        acqTime = 1e3  # us
        bw = nPoints / acqTime  # MHz
        repetitionTime = self.mapVals['repetitionTime']*1e3  # us
        nScan = self.mapVals['nScan']
        if nScan < 1: return 0
        nLobes = self.mapVals['rfLobes']
        if (nLobes + 1) % 2 != 0:
            print('Number of lobes must be odd!')
            return 0

        # Initialize the experiment
        samplingPeriod = 1 / bw
        self.expt = ex.Experiment(lo_freq=larmorFreq, rx_t=samplingPeriod)
        samplingPeriod = self.expt.getSamplingRate()
        bw = 1 / samplingPeriod
        acqTime = nPoints / bw
        self.mapVals['acqTime'] = acqTime*1e-3
        self.mapVals['bw'] = bw

        # Create the sequence
        self.iniSequence(20, shimming)
        for i in range(nScan):
            tEx = shimmingTime + nScan * repetitionTime
            rfExAmp = rfAmpMin + (rfAmpMax - rfAmpMin) * i / nScan
            if nLobes == 0:
                self.rfRecPulse(tEx, rfExTime, rfExAmp)
            else:
                self.rfSincPulse(tEx, rfExTime, rfExAmp, 0, nLobes)
            
            tAq = tEx + hw.blkTime + rfExTime + hw.deadTime
            self.rxGateSync(tAq, acqTime)
        self.endSequence(nScan * repetitionTime)

        if not self.floDict2Exp():
            return 0

        if not plotSeq:
            rxd, msg = self.expt.run()
            print(msg)
            dataFull = self.decimate(rxd['rx0'], 1)
            self.mapVals['data'] = dataFull
            self.matrix = np.reshape(dataFull, (nScan, -1))

        self.expt.__del__()

    def sequenceAnalysis(self):
        xAxis = np.linspace(self.mapVals['rfAmpMin'],
                                self.mapVals['rfAmpMax'], nScan)
        yAxis = []
        nScan = self.mapVals['nScan']
        for i in range(nScan):
            signal = self.matrix[i, :]

            spectrum = np.abs(np.fft.ifftshift(
                np.fft.ifftn(np.fft.ifftshift(signal))))
            yAxis.append(np.max(np.abs(spectrum)))

        return [{
            'widget': 'curve',
            'xData': xAxis,
            'yData': yAxis,
            'xLabel': 'RF amplitude (a.u.)',
            'yLabel': 'Spectrum (a.u.)',
            'title': 'Spectrum vs. RF amplitude',
            'legend': ['abs'],
            'row': 0,
            'col': 0
        }]
        signal = self.mapVals['data']
        bw = self.mapVals['bw']*1e3  # kHz
        nPoints = 100
        deadTime = hw.deadTime*1e-3  # ms
        rfExTime = self.mapVals['rfExTime']*1e-3  # ms
        tVector = np.linspace(rfExTime/2 + deadTime + 0.5/bw,
                              rfExTime/2 + deadTime + (nPoints-0.5)/bw, nPoints)
        fVector = np.linspace(-bw/2, bw/2, nPoints)
        spectrum = np.abs(np.fft.ifftshift(
            np.fft.ifftn(np.fft.ifftshift(signal))))
        fitedLarmor = self.mapVals['larmorFreq'] + \
            fVector[np.argmax(np.abs(spectrum))] * 1e-3
        print('Larmor frequency: %1.5f MHz' % fitedLarmor)
        self.mapVals['signalVStime'] = [tVector, signal]
        self.mapVals['spectrum'] = [fVector, spectrum]
        self.saveRawData()

        # Add time signal to the layout
        result1 = {
            'widget': 'curve',
            'xData': tVector,
            'yData': [np.abs(signal), np.real(signal), np.imag(signal)],
            'xLabel': 'Time (ms)',
            'yLabel': 'Signal amplitude (mV)',
            'title': 'Signal vs time',
            'legend': ['abs', 'real', 'imag'],
            'row': 0,
            'col': 0
        }

        # Add frequency spectrum to the layout
        result2 = {
            'widget': 'curve',
            'xData': fVector,
            'yData': [spectrum],
            'xLabel': 'Frequency (kHz)',
            'yLabel': 'Spectrum amplitude (a.u.)',
            'title': 'Spectrum',
            'legend': [''],
            'row': 1,
            'col': 0
        }
        return [result1, result2]
