#!/usr/bin/env python3
# coding: utf-8

import struct
import copy
import os
import math
from decimal import Decimal, ROUND_HALF_UP
from .flattenedwaveform import FlattenedWaveform, FlattenedIQWaveform

try:
    import matplotlib
    matplotlib.use("Agg")
    matplotlib.rcParams["agg.path.chunksize"] = 20000
finally:
    import matplotlib.pyplot as plt


class WaveSequenceParams(object):

    __NUM_WAVE_STEPS_OFFSET         = 0
    __IS_IQ_DATA_OFFSET             = 4
    __SAMPLING_RATE_OFFSET          = 8
    __EACH_STEP_PARAMS_OFFSET       = 16
    __STEP_ID_OFFSET                = 0
    __INF_CYCLES_OFFSET             = 4
    __NUM_PRIME_WAVE_SAMPLES_OFFSET = 8
    __NUM_POST_BLANK_SAMPLES_OFFSET = 16
    __EACH_STEP_PARAMS_SIZE         = 24

    """
    波形シーケンスのパラメータ
    """
    @classmethod
    def build_from_bytes(cls, wave_sequence_param_bytes):
        """
        rftool から受信する波形シーケンスのパラメータのバイトデータから
        WaveSequenceParams オブジェクトを作成する
        """
        tmp = wave_sequence_param_bytes[cls.__NUM_WAVE_STEPS_OFFSET : cls.__NUM_WAVE_STEPS_OFFSET + 4]
        num_wave_steps = struct.unpack('I', tmp)[0]
        tmp = wave_sequence_param_bytes[cls.__IS_IQ_DATA_OFFSET : cls.__IS_IQ_DATA_OFFSET + 4]
        is_iq_data = bool(struct.unpack('I', tmp)[0])
        tmp = wave_sequence_param_bytes[cls.__SAMPLING_RATE_OFFSET : cls.__SAMPLING_RATE_OFFSET + 8]
        sampling_rate = struct.unpack('d', tmp)[0]
        
        step_id_list = []
        infinite_cycles_flag_list = []
        num_prime_wave_samples_list = []
        num_post_blank_samples_list = []
        for i in range(num_wave_steps):
            offset = cls.__EACH_STEP_PARAMS_OFFSET + i * cls.__EACH_STEP_PARAMS_SIZE
            step_params_bytes = wave_sequence_param_bytes[offset:]
            tmp = step_params_bytes[cls.__STEP_ID_OFFSET : cls.__STEP_ID_OFFSET + 4]
            step_id_list.append(struct.unpack('I', tmp)[0])
            tmp = step_params_bytes[cls.__INF_CYCLES_OFFSET : cls.__INF_CYCLES_OFFSET + 4]
            infinite_cycles_flag_list.append(struct.unpack('I', tmp)[0])
            tmp = step_params_bytes[cls.__NUM_PRIME_WAVE_SAMPLES_OFFSET : cls.__NUM_PRIME_WAVE_SAMPLES_OFFSET + 8]
            num_prime_wave_samples_list.append(struct.unpack('Q', tmp)[0])
            tmp = step_params_bytes[cls.__NUM_POST_BLANK_SAMPLES_OFFSET : cls.__NUM_POST_BLANK_SAMPLES_OFFSET + 8]
            num_post_blank_samples_list.append(struct.unpack('Q', tmp)[0])

        return WaveSequenceParams(
            num_wave_steps, 
            is_iq_data, 
            sampling_rate, 
            step_id_list, 
            infinite_cycles_flag_list,
            num_prime_wave_samples_list,
            num_post_blank_samples_list)


    def __init__(
        self, 
        num_wave_steps, 
        is_iq_data, 
        sampling_rate, 
        step_id_list, 
        infinite_cycles_flag_list,
        num_prime_wave_samples_list,
        num_post_blank_samples_list):
        
        self.__num_wave_steps = num_wave_steps
        self.__is_iq_data = is_iq_data
        self.__sampling_rate = sampling_rate
        self.__step_id_list = step_id_list
        self.__infinite_cycles_flag_list = infinite_cycles_flag_list
        self.__num_prime_wave_samples_list = num_prime_wave_samples_list
        self.__num_post_blank_samples_list = num_post_blank_samples_list


    @property
    def num_wave_steps(self):
        return self.__num_wave_steps

    @property
    def is_iq_data(self):
        return self.__is_iq_data

    @property
    def sampling_rate(self):
        return self.__sampling_rate

    @property
    def step_id_list(self):
        return copy.copy(self.__step_id_list)

    @property
    def infinite_cycles_flag_list(self):
        return copy.copy(self.__infinite_cycles_flag_list)

    @property
    def num_prime_wave_samples_list(self):
        return copy.copy(self.__num_prime_wave_samples_list)

    @property
    def num_post_blank_samples_list(self):
        return copy.copy(self.__num_post_blank_samples_list)
    

class FlattenedWaveformSequence(object):
    """
    ステップ ID ごとに FlattenedWaveform オブジェクトを保持するクラス
    """   
    @classmethod
    def build_from_wave_ram(cls, wave_seq_params, wave_ram_data):
        """
        ハードウェアの波形 RAM の情報から FlattenedWaveformSequence オブジェクトを作成する
        wave_seq_params : WaveSequenceParams
            wave_ram_data に格納された波形シーケンスのパラメータ
        wave_ram_data : bytes
            波形 RAM のデータ.
        """
        step_id_list = wave_seq_params.step_id_list
        step_id_to_waveform = {}
        step_id_to_post_blank = {}
        step_id_to_duration = {}

        for step_idx in range(wave_seq_params.num_wave_steps):
            step_id = step_id_list[step_idx]
            num_prime_wave_samples = wave_seq_params.num_prime_wave_samples_list[step_idx]
            num_post_blank_samples = wave_seq_params.num_post_blank_samples_list[step_idx]
            waveform = FlattenedWaveform.build_from_wave_ram(wave_ram_data, num_prime_wave_samples, step_idx)
            step_id_to_waveform[step_id] = waveform
            if wave_seq_params.infinite_cycles_flag_list[step_idx] == 0:
                duration = 1000 * num_prime_wave_samples / wave_seq_params.sampling_rate
            else:
                duration = float('inf')
            post_blank = 1000 * num_post_blank_samples / wave_seq_params.sampling_rate
            step_id_to_duration[step_id] = duration
            step_id_to_post_blank[step_id] = post_blank

        return FlattenedWaveformSequence(step_id_to_waveform, step_id_to_duration, step_id_to_post_blank)


    @classmethod
    def build_from_wave_obj(cls, step_id_to_wave, step_id_to_post_blank, sampling_rate):
        """
        ステップごとの AwgWave, AwgAnyWave オブジェクトから FlattenedWaveformSequence オブジェクトを作成する
        
        Parameters
        ----------        
        step_id_to_wave : dict
            key : ステップID
            value : AwgWave or AwgAnyWave
        step_id_to_post_blank : dict
            key : ステップID
            value : 無波形期間の長さ (ns)
        sampling_rate : float
            出力時のサンプリングレート
        """
        step_id_to_waveform = {}
        step_id_to_duration = {}
        for step_id, wave in step_id_to_wave.items():
            waveform = FlattenedWaveform.build_from_wave_obj(wave, sampling_rate)
            step_id_to_waveform[step_id] = waveform
            step_id_to_duration[step_id] = wave.get_duration()

        return FlattenedWaveformSequence(step_id_to_waveform, step_id_to_duration, step_id_to_post_blank)


    def __init__(self, step_id_to_waveform, step_id_to_duration, step_id_to_post_blank):
        """
        Parameters
        ----------
        step_id_to_iq_waveform : dict
            key : ステップID
            value : FlattenedWaveform
        step_id_to_duration : dict
            key : ステップID
            value : 無波形期間の長さ (ns)
        step_id_to_post_blank : dict
            key : ステップID
            value : 波形ステップインターバル
        """
        self.__step_id_to_waveform = copy.copy(step_id_to_waveform)
        self.__step_id_to_duration = copy.copy(step_id_to_duration)
        self.__step_id_to_post_blank = copy.copy(step_id_to_post_blank)


    def get_samples_by_step_id(self):
        """
        ステップ ID をキーとしてサンプル値の配列を保持する dict を返す.
        
        Returns
        -------
        dict
            key : ステップ ID 
            value : サンプル値の配列
        """
        step_id_to_samples = {}
        for step_id, waveform in self.__step_id_to_waveform.items():
            step_id_to_samples[step_id] = waveform.get_samples()
        return step_id_to_samples


    def save_as_img(self, filepath):
        """
        このオブジェクトが保持する一連の波形を図として保存する.
        波形ステップの終了から開始までの間隔は, 設定した値に関わらず最大 60 ns ほど空く場合があるが,
        出力される図ではその期間は考慮しない.
        
        Parameters
        ----------
        file_path : string
            保存先のファイルパス
        """
        out_dir = os.path.dirname(filepath)
        os.makedirs(out_dir, exist_ok = True)
        plt.figure(figsize = (16, 9), dpi = 300)
        plotter = WaveSequencePlotter(
            WaveSequencePlotter.REAL_WAVE,
            self.__step_id_to_duration,
            self.__step_id_to_post_blank,
            self.__step_id_to_waveform)
        plotter.plot_waveform(plt, plt.gca(), "Waveform", "C0")
        plt.xlabel("Time [us]")
        plt.title("Waveform")
        plt.savefig(filepath)
        plt.close()


class FlattenedIQWaveformSequence(object):
    """
    ステップ ID ごとに FlattenedIQWaveform オブジェクトを保持するクラス
    """
    @classmethod
    def build_from_wave_ram(cls, wave_seq_params, wave_ram_data):
        """
        ハードウェアの波形 RAM の情報から FlattenedIQWaveformSequence オブジェクトを作成する
        wave_seq_params : WaveSequenceParams
            wave_ram_data に格納された波形シーケンスのパラメータ
        wave_ram_data : bytes
            波形 RAM のデータ.
        """  
        step_id_list = wave_seq_params.step_id_list
        step_id_to_waveform = {}
        step_id_to_post_blank = {}
        step_id_to_duration = {}

        for step_idx in range(wave_seq_params.num_wave_steps):
            step_id = step_id_list[step_idx]
            num_prime_wave_samples = wave_seq_params.num_prime_wave_samples_list[step_idx]
            num_post_blank_samples = wave_seq_params.num_post_blank_samples_list[step_idx]
            waveform = FlattenedIQWaveform.build_from_wave_ram(wave_ram_data, num_prime_wave_samples, step_idx)
            step_id_to_waveform[step_id] = waveform
            
            if wave_seq_params.infinite_cycles_flag_list[step_idx] == 0:
                duration = 1000.0 * num_prime_wave_samples / wave_seq_params.sampling_rate
            else:
                duration = float('inf')
            post_blank = 1000 * num_post_blank_samples / wave_seq_params.sampling_rate
            step_id_to_duration[step_id] = duration
            step_id_to_post_blank[step_id] = post_blank

        return FlattenedIQWaveformSequence(step_id_to_waveform, step_id_to_duration, step_id_to_post_blank)


    @classmethod
    def build_from_wave_obj(cls, step_id_to_wave, step_id_to_post_blank, sampling_rate):
        """
        ステップごとの AwgWave, AwgAnyWave オブジェクトから FlattenedWaveformSequence オブジェクトを作成する
        
        Parameters
        ----------        
        step_id_to_wave : dict
            key : ステップID
            value : AwgIQWave
        step_id_to_post_blank : dict
            key : ステップID
            value : 無波形期間 (ns)
        sampling_rate : float
            出力時のサンプリングレート
        """
        step_id_to_waveform = {}
        step_id_to_duration = {}
        for step_id, wave in step_id_to_wave.items():
            waveform = FlattenedIQWaveform.build_from_wave_obj(wave, sampling_rate)
            step_id_to_waveform[step_id] = waveform
            step_id_to_duration[step_id] = wave.get_duration()

        return FlattenedIQWaveformSequence(step_id_to_waveform, step_id_to_duration, step_id_to_post_blank)


    def __init__(self, step_id_to_iq_waveform, step_id_to_duration, step_id_to_post_blank):
        """
        Parameters
        ----------
        step_id_to_iq_waveform : dict
            key : ステップID
            value : FlattenedIQWaveform
        step_id_to_duration : dict
            key : ステップID
            value : 波形出力期間
        step_id_to_post_blank : dict
            key : ステップID
            value : 波形ステップインターバル
        """
        self.__step_id_to_iq_waveform = copy.copy(step_id_to_iq_waveform)
        self.__step_id_to_duration = copy.copy(step_id_to_duration)
        self.__step_id_to_post_blank = copy.copy(step_id_to_post_blank)


    def get_i_samples_by_step_id(self):
        """
        ステップ ID をキーとして I データのサンプル値の配列を保持する dict を返す.
        
        Returns
        -------
        dict
            key : ステップ ID 
            value : I データのサンプル値の配列
        """
        step_id_to_i_samples = {}
        for step_id, waveform in self.__step_id_to_iq_waveform.items():
            step_id_to_i_samples[step_id] = waveform.get_i_samples()
        return step_id_to_i_samples


    def get_q_samples_by_step_id(self):
        """
        ステップ ID をキーとして Q データのサンプル値の配列を保持する dict を返す.
        
        Returns
        -------
        dict
            key : ステップ ID 
            value : Q データのサンプル値の配列
        """
        step_id_to_q_samples = {}
        for step_id, waveform in self.__step_id_to_iq_waveform.items():
            step_id_to_q_samples[step_id] = waveform.get_q_samples()
        return step_id_to_q_samples


    def save_as_img(self, filepath, iq_separation = True):
        """
        このオブジェクトが保持する一連の波形を図として保存する.
        波形ステップの終了から開始までの間隔は, 設定した値に関わらず最大 60 ns ほど空く場合があるが,
        出力される図ではその期間は考慮しない.

        Parameters
        ----------
        file_path : string
            保存先のファイルパス
        """
        out_dir = os.path.dirname(filepath)
        os.makedirs(out_dir, exist_ok = True)
        fig = plt.figure(figsize = (16, 9), dpi = 300)
        if iq_separation:
            upper_axes = fig.add_subplot(2, 1, 1)
            i_plotter = WaveSequencePlotter(
                WaveSequencePlotter.I_WAVE,
                self.__step_id_to_duration,
                self.__step_id_to_post_blank,
                self.__step_id_to_iq_waveform)
            i_plotter.plot_waveform(plt, upper_axes, "I Waveform", "C0")
            lower_axes = fig.add_subplot(2, 1, 2)
            q_plotter = WaveSequencePlotter(
                WaveSequencePlotter.Q_WAVE,
                self.__step_id_to_duration,
                self.__step_id_to_post_blank,
                self.__step_id_to_iq_waveform)
            q_plotter.plot_waveform(plt, lower_axes, "Q Waveform", "C1")
            lower_axes.set_xlabel("Time [us]")        
        else:
            plotter = WaveSequencePlotter(
                WaveSequencePlotter.I_WAVE,
                self.__step_id_to_duration,
                self.__step_id_to_post_blank,
                self.__step_id_to_iq_waveform)
            plotter.plot_waveform(plt, plt.gca(), "IQ Waveform", "C0")
            plotter = WaveSequencePlotter(
                WaveSequencePlotter.Q_WAVE,
                self.__step_id_to_duration,
                self.__step_id_to_post_blank,
                self.__step_id_to_iq_waveform)
            plotter.plot_waveform(plt, plt.gca(), "IQ Waveform", "C1")
            plt.xlabel("Time [us]")
            plt.title("IQ Waveform")

        plt.savefig(filepath)
        plt.close()


class WaveSequencePlotter(object):
    """
    波形シーケンスの描画に必要なメソッドを定義したクラス
    """
    REAL_WAVE = 0
    I_WAVE = 1
    Q_WAVE = 2

    def __init__(self, wave_type, step_id_to_duration, step_id_to_post_blank, step_id_to_waveform):
        """
        Parameters
        ----------
        step_id_to_duration : dict
            key : ステップID
            value : 波形出力期間
        step_id_to_post_blank : dict
            key : ステップID
            value : 波形ステップインターバル            
        step_id_to_waveform : dict
            key : ステップID
            value : FlattenedWaveform, FlattenedIQWaveform
        """
        self.__wave_type = wave_type
        self.__step_id_to_duration = step_id_to_duration
        self.__step_id_to_post_blank = step_id_to_post_blank
        self.__step_id_to_waveform = step_id_to_waveform
        self.__num_blank_points = self.__calc_num_blank_points()

    def __calc_num_blank_points(self):
        """ステップ内で無波形区間を描画するときのポイント数を計算する"""
        BLANK_SAPCE_RATE = 0.30 # 描画エリアの内, 無波形の区間に割く割合
        num_samples = 0
        num_blanks = 0
        for step_id, waveform in self.__step_id_to_waveform.items():
            num_samples += waveform.get_num_samples()
            if self.__step_has_blank(step_id):
                num_blanks += 1
        
        if num_blanks == 0:
            return 0

        return max(2, int(num_samples * BLANK_SAPCE_RATE / num_blanks))


    def __step_has_blank(self, step_id):
        """ 引数で指定したステップ ID の波形のステップが無波形区間を持っているか調べる """
        return self.__step_id_to_post_blank[step_id] != 0


    def __get_samples_from_waveform(self, waveform):
        
        if self.__wave_type == WaveSequencePlotter.REAL_WAVE:
            return waveform.get_samples()
        elif self.__wave_type == WaveSequencePlotter.I_WAVE:
            return waveform.get_i_samples()
        elif self.__wave_type == WaveSequencePlotter.Q_WAVE:
            return waveform.get_q_samples()
        else:
            assert False, ("This should never happen.")


    def __get_sequential_wave_samples(self):
        """
        各波形ステップのサンプル点に無波形区間のサンプル点を加えて, 全ステップ分のサンプル点を返す
        """
        samples = []
        waveform_list = sorted(self.__step_id_to_waveform.items())
        for step_id, waveform in waveform_list:
            step_samples = self.__get_samples_from_waveform(waveform)
            samples.extend(step_samples)
            if self.__step_has_blank(step_id):
                samples.extend([0] * self.__num_blank_points)

        return samples


    def __get_xpos_list(self):
        
        xpos_list = []
        xpos = 0
        waveform_list = sorted(self.__step_id_to_waveform.items())
        for step_id, waveform in waveform_list:
            num_samples = waveform.get_num_samples()
            xpos_list.extend([i + xpos for i in range(num_samples)])
            xpos += num_samples - 1
            if self.__step_has_blank(step_id):
                xpos_list.extend([i + xpos for i in range(self.__num_blank_points)])
                xpos += self.__num_blank_points - 1
        
        return xpos_list


    def  __get_vline_pos_list(self):
        """
        グラフに描画する垂直線の位置のリストを返す.
        """
        vline_pos_list = [0]
        vline_pos = 0
        waveform_list = sorted(self.__step_id_to_waveform.items())
        for step_id, waveform in waveform_list:
            num_samples = waveform.get_num_samples()
            vline_pos += num_samples - 1
            vline_pos_list.append(vline_pos)
            if self.__step_has_blank(step_id):
                vline_pos += self.__num_blank_points - 1
                vline_pos_list.append(vline_pos)

        return vline_pos_list


    def  __get_vline_properties_list(self):
        """
        グラフに描画する垂直線の外形パラメータのリストを返す.
        [(linestyle, linewidth), ...]
        """
        vline_props_list = [("dashed", 0.0, 'black')]
        step_id_list = sorted(self.__step_id_to_waveform.keys())
        for step_id in step_id_list:
            if self.__step_has_blank(step_id):
                vline_props_list.append(("dashed", 0.0, 'black'))
                vline_props_list.append(("dashdot", 0.8, 'black'))
            else:
                vline_props_list.append(("dashdot", 0.8, 'black'))
        
        return vline_props_list


    def __get_x_axis_val_list(self):
        """
        グラフの垂直線の下に表示する値のリストを返す.
        """
        step_start_time = 0.0
        xval_list = [0]
        step_id_list = sorted(self.__step_id_to_waveform.keys())
        for step_id in step_id_list:
            duration = self.__step_id_to_duration[step_id]
            post_blank = self.__step_id_to_post_blank[step_id]
            time = step_start_time + duration / 1000.0
            if math.isfinite(time):
                time = Decimal(time).quantize(Decimal("0.001"), rounding = ROUND_HALF_UP)
            xval_list.append(time)
            if self.__step_has_blank(step_id):
                time = step_start_time + (duration + post_blank) / 1000.0
                if math.isfinite(time):
                    time = Decimal(time).quantize(Decimal("0.001"), rounding = ROUND_HALF_UP)
                xval_list.append(time)
            step_start_time += (duration + post_blank) / 1000.0
        
        return xval_list


    def __add_interval_to_graph(self, axes, x_axis_val_list, vline_pos_list, ymax, ymin):
        
        idx = 0
        step_id_list = sorted(self.__step_id_to_waveform.keys())
        for step_id in step_id_list:
            duration = self.__step_id_to_duration[step_id] / 1000.0
            if math.isfinite(duration):
                duration = Decimal(duration).quantize(Decimal("0.001"), rounding = ROUND_HALF_UP)
            self.__add_interval_label(vline_pos_list[idx], vline_pos_list[idx + 1], duration, axes, ymax, ymin)
            idx += 1

            if self.__step_has_blank(step_id):
                post_blank = self.__step_id_to_post_blank[step_id] / 1000.0
                if math.isfinite(post_blank):
                    post_blank = Decimal(post_blank).quantize(Decimal("0.001"), rounding = ROUND_HALF_UP)
                self.__add_interval_label(vline_pos_list[idx], vline_pos_list[idx + 1], post_blank, axes, ymax, ymin)
                idx += 1
    
    def __add_interval_label(self, vpos_start, vpos_end, interval, axes, ymax, ymin):

        extension = 0.06 * (ymax - ymin)
        axes.annotate(
            text = '', 
            xy = (vpos_start, ymin - extension),
            xytext = (vpos_end, ymin - extension),
            arrowprops = dict(arrowstyle = '<->'))
        texst_xpos = vpos_start + (vpos_end - vpos_start) / 5
        if math.isfinite(interval):
            interval = Decimal(interval).quantize(Decimal("0.001"), rounding = ROUND_HALF_UP)
        if not math.isnan(interval):
            extension = 0.05 * (ymax - ymin)
            axes.text(texst_xpos, ymin - extension, interval, rotation = 40, fontsize = 6)


    def __add_grid_lines(self, axes, vline_pos_list, vline_props_list, ymax, ymin):

        extension = 0.06 * (ymax - ymin)
        for i in range(len(vline_pos_list)):
            axes.vlines(
                vline_pos_list[i],
                ymin = ymin - extension,
                ymax = ymax,
                linestyles = vline_props_list[i][0],
                linewidth = vline_props_list[i][1],
                color = vline_props_list[i][2])

        axes.grid(which = "both")
        axes.grid(which = "major", alpha = 0.5)
        axes.grid(which = "minor", alpha = 0.2)


    def __convert_to_x_axis_labes(self, x_axis_val_list):
        
        x_axis_label_list = [""] * len(x_axis_val_list)
        for i in range(len(x_axis_val_list)):
            x_axis_label_list[i] = x_axis_val_list[i]
            if math.isinf(x_axis_val_list[i]):
                break
        return x_axis_label_list


    def plot_waveform(self, plt, axes, title, color):
        """
        引数で指定した matplotlib の axes に波形シーケンスを描画する
        """
        samples = self.__get_sequential_wave_samples()
        xpos_list = self.__get_xpos_list()
        vline_pos_list = self.__get_vline_pos_list()
        vline_props_list = self.__get_vline_properties_list()
        x_axis_val_list = self.__get_x_axis_val_list()
        x_axis_label_list = self.__convert_to_x_axis_labes(x_axis_val_list)

        ymin = min(samples)
        ymax = max(samples)
        self.__add_grid_lines(axes, vline_pos_list, vline_props_list, ymax, ymin)
        self.__add_interval_to_graph(axes, x_axis_val_list, vline_pos_list, ymax, ymin)

        axes.plot(xpos_list, samples, linewidth = 0.8, color = color)
        axes.set_xticks(vline_pos_list)
        axes.set_xticklabels(x_axis_label_list, fontsize = 6)
        plt.setp(axes.get_xticklabels(), rotation = 40, horizontalalignment = 'right')
        plt.title(title)
