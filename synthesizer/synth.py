"""
Sample waveform synthesizer. Inspired by FM synthesizers such as the Yamaha DX-7.
Creates some simple waveform samples with adjustable parameters.

Written by Irmen de Jong (irmen@razorvine.net) - License: MIT open-source.
"""

import sys
import itertools
import random
from math import sin, pi, floor, fabs, log
from .sample import Sample


__all__ = ["key_freq", "WaveSynth", "Sine", "Triangle", "Square", "SquareH", "Sawtooth", "SawtoothH",
           "Pulse", "Harmonics", "WhiteNoise", "Linear",
           "FastSine", "FastPulse", "FastTriangle", "FastSawtooth", "FastSquare"]


def key_freq(key_number, a4=440.0):
    """
    Return the note frequency for the given piano key number.
    C4 is key 40 and A4 is key 49 (=440 hz).
    https://en.wikipedia.org/wiki/Piano_key_frequencies
    """
    return 2**((key_number-49)/12) * a4


class WaveSynth:
    """
    Waveform sample synthesizer. Can generate various wave forms based on mathematic functions:
    sine, square (perfect or with harmonics), triangle, sawtooth (perfect or with harmonics),
    variable harmonics, white noise.  It also supports an optional LFO for Frequency Modulation.
    The resulting waveform sample data is in integer 16 or 32 bits format.
    """
    def __init__(self, samplerate=Sample.norm_samplerate, samplewidth=Sample.norm_samplewidth):
        if samplewidth not in (2, 4):
            raise ValueError("only sample widths 2 and 4 are supported")
        self.samplerate = samplerate
        self.samplewidth = samplewidth

    def sine(self, frequency, duration, amplitude=0.9999, phase=0.0, bias=0.0, fm_lfo=None):
        """Simple sine wave. Optional FM using a supplied LFO."""
        wave = self.__sine(frequency, amplitude, phase, bias, fm_lfo)
        return self.__render_sample(duration, wave)

    def sine_gen(self, frequency, amplitude=0.9999, phase=0.0, bias=0.0, fm_lfo=None):
        """Simple sine wave generator. Optional FM using a supplied LFO."""
        wave = self.__sine(frequency, amplitude, phase, bias, fm_lfo)
        while True:
            yield int(next(wave))

    def square(self, frequency, duration, amplitude=0.75, phase=0.0, bias=0.0, fm_lfo=None):
        """
        A perfect square wave [max/-max].
        It is fast, but the square wave is not as 'natural' sounding as the ones
        generated by the square_h function (which is based on harmonics).
        """
        wave = self.__square(frequency, amplitude, phase, bias, fm_lfo)
        return self.__render_sample(duration, wave)

    def square_gen(self, frequency, amplitude=0.75, phase=0.0, bias=0.0, fm_lfo=None):
        """
        Generator for a perfect square wave [max/-max].
        It is fast, but the square wave is not as 'natural' sounding as the ones
        generated by the square_h function (which is based on harmonics).
        """
        wave = self.__square(frequency, amplitude, phase, bias, fm_lfo)
        while True:
            yield int(next(wave))

    def square_h(self, frequency, duration, num_harmonics=16, amplitude=0.9999, phase=0.0, bias=0.0, fm_lfo=None):
        """A square wave based on harmonic sine waves (more natural sounding than pure square)"""
        wave = self.__square_h(frequency, num_harmonics, amplitude, phase, bias, fm_lfo)
        return self.__render_sample(duration, wave)

    def square_h_gen(self, frequency, num_harmonics=16, amplitude=0.9999, phase=0.0, bias=0.0, fm_lfo=None):
        """Generator for a square wave based on harmonic sine waves (more natural sounding than pure square)"""
        wave = self.__square_h(frequency, num_harmonics, amplitude, phase, bias, fm_lfo)
        while True:
            yield int(next(wave))

    def triangle(self, frequency, duration, amplitude=0.9999, phase=0.0, bias=0.0, fm_lfo=None):
        """Perfect triangle waveform (not using harmonics). Optional FM using a supplied LFO."""
        wave = self.__triangle(frequency, amplitude, phase, bias, fm_lfo)
        return self.__render_sample(duration, wave)

    def triangle_gen(self, frequency, amplitude=0.9999, phase=0.0, bias=0.0, fm_lfo=None):
        """Generator for a perfect triangle waveform (not using harmonics). Optional FM using a supplied LFO."""
        wave = self.__triangle(frequency, amplitude, phase, bias, fm_lfo)
        while True:
            yield int(next(wave))

    def sawtooth(self, frequency, duration, amplitude=0.75, phase=0.0, bias=0.0, fm_lfo=None):
        """Perfect sawtooth waveform (not using harmonics)."""
        wave = self.__sawtooth(frequency, amplitude, phase, bias, fm_lfo)
        return self.__render_sample(duration, wave)

    def sawtooth_gen(self, frequency, amplitude=0.75, phase=0.0, bias=0.0, fm_lfo=None):
        """Generator for a perfect sawtooth waveform (not using harmonics)."""
        wave = self.__sawtooth(frequency, amplitude, phase, bias, fm_lfo)
        while True:
            yield int(next(wave))

    def sawtooth_h(self, frequency, duration, num_harmonics=16, amplitude=0.75, phase=0.0, bias=0.0, fm_lfo=None):
        """Sawtooth waveform based on harmonic sine waves"""
        wave = self.__sawtooth_h(frequency, num_harmonics, amplitude, phase, bias, fm_lfo)
        return self.__render_sample(duration, wave)

    def sawtooth_h_gen(self, frequency, num_harmonics=16, amplitude=0.75, phase=0.0, bias=0.0, fm_lfo=None):
        """Generator for a Sawtooth waveform based on harmonic sine waves"""
        wave = self.__sawtooth_h(frequency, num_harmonics, amplitude, phase, bias, fm_lfo)
        while True:
            yield int(next(wave))

    def pulse(self, frequency, duration, amplitude=0.75, phase=0.0, bias=0.0, pulsewidth=0.1, fm_lfo=None, pwm_lfo=None):
        """
        Perfect pulse waveform (not using harmonics).
        Optional FM and/or Pulse-width modulation. If you use PWM, pulsewidth is ignored.
        The pwm_lfo oscillator should yield values between 0 and 1 (=the pulse width factor), or it will be clipped.
        """
        wave = self.__pulse(frequency, amplitude, phase, bias, pulsewidth, fm_lfo, pwm_lfo)
        return self.__render_sample(duration, wave)

    def pulse_gen(self, frequency, amplitude=0.75, phase=0.0, bias=0.0, pulsewidth=0.1, fm_lfo=None, pwm_lfo=None):
        """
        Generator for perfect pulse waveform (not using harmonics).
        Optional FM and/or Pulse-width modulation. If you use PWM, pulsewidth is ignored.
        The pwm_lfo oscillator should yield values between 0 and 1 (=the pulse width factor), or it will be clipped.
        """
        wave = self.__pulse(frequency, amplitude, phase, bias, pulsewidth, fm_lfo, pwm_lfo)
        while True:
            yield int(next(wave))

    def harmonics(self, frequency, duration, num_harmonics, amplitude=0.9999, phase=0.0, bias=0.0, only_even=False, only_odd=False, fm_lfo=None):
        """Makes a waveform based on harmonics. This is slow because many sine waves are added together."""
        wave = self.__harmonics(frequency, num_harmonics, amplitude, phase, bias, only_even, only_odd, fm_lfo)
        return self.__render_sample(duration, wave)

    def harmonics_gen(self, frequency, num_harmonics, amplitude=0.9999, phase=0.0, bias=0.0, only_even=False, only_odd=False, fm_lfo=None):
        """Generator for a waveform based on harmonics. This is slow because many sine waves are added together."""
        wave = self.__harmonics(frequency, num_harmonics, amplitude, phase, bias, only_even, only_odd, fm_lfo)
        while True:
            yield int(next(wave))

    def white_noise(self, duration, amplitude=0.9999, bias=0.0):
        """White noise (randomness) waveform."""
        wave = self.__white_noise(amplitude, bias)
        return self.__render_sample(duration, wave)

    def white_noise_gen(self, amplitude=0.9999, bias=0.0):
        """Generator for White noise (randomness) waveform."""
        wave = self.__white_noise(amplitude, bias)
        while True:
            yield int(next(wave))

    def linear(self, duration, start_amp, finish_amp):
        """A linear constant or sloped waveform."""
        wave = self.__linear(duration, start_amp, finish_amp)
        return self.__render_sample(duration, wave)

    def linear_gen(self, duration, startamp, finishamp):
        """Generator for linear constant or sloped waveform (it ends when it reaches the specified duration)"""
        wave = self.__linear(duration, startamp, finishamp)
        for _ in range(int(duration*self.samplerate)):
            yield int(next(wave))

    def __sine(self, frequency, amplitude, phase, bias, fm_lfo):
        scale = self.__check_and_get_scale(frequency, amplitude, bias)
        if fm_lfo:
            return Sine(frequency, amplitude*scale, phase, bias*scale, fm_lfo=fm_lfo, samplerate=self.samplerate)
        else:
            return FastSine(frequency, amplitude*scale, phase, bias*scale, samplerate=self.samplerate)

    def __square(self, frequency, amplitude, phase, bias, fm_lfo):
        scale = self.__check_and_get_scale(frequency, amplitude, bias)
        if fm_lfo:
            return Square(frequency, amplitude*scale, phase, bias*scale, fm_lfo=fm_lfo, samplerate=self.samplerate)
        else:
            return FastSquare(frequency, amplitude*scale, phase, bias*scale, samplerate=self.samplerate)

    def __square_h(self, frequency, num_harmonics, amplitude, phase, bias, fm_lfo):
        scale = self.__check_and_get_scale(frequency, amplitude, bias)
        return SquareH(frequency, num_harmonics, amplitude*scale, phase, bias*scale, fm_lfo=fm_lfo, samplerate=self.samplerate)

    def __triangle(self, frequency, amplitude, phase, bias, fm_lfo):
        scale = self.__check_and_get_scale(frequency, amplitude, bias)
        if fm_lfo:
            return Triangle(frequency, amplitude*scale, phase, bias*scale, fm_lfo=fm_lfo, samplerate=self.samplerate)
        else:
            return FastTriangle(frequency, amplitude*scale, phase, bias*scale, samplerate=self.samplerate)

    def __sawtooth(self, frequency, amplitude, phase, bias, fm_lfo):
        scale = self.__check_and_get_scale(frequency, amplitude, bias)
        if fm_lfo:
            return Sawtooth(frequency, amplitude*scale, phase, bias*scale, fm_lfo=fm_lfo, samplerate=self.samplerate)
        else:
            return FastSawtooth(frequency, amplitude*scale, phase, bias*scale, samplerate=self.samplerate)

    def __sawtooth_h(self, frequency, num_harmonics, amplitude, phase, bias, fm_lfo):
        scale = self.__check_and_get_scale(frequency, amplitude, bias)
        return SawtoothH(frequency, num_harmonics, amplitude*scale, phase, bias*scale, fm_lfo=fm_lfo, samplerate=self.samplerate)

    def __pulse(self, frequency, amplitude, phase, bias, pulsewidth, fm_lfo, pwm_lfo):
        assert 0 <= pulsewidth <= 1
        scale = self.__check_and_get_scale(frequency, amplitude, bias)
        if fm_lfo:
            return Pulse(frequency, amplitude*scale, phase, bias*scale, pulsewidth, fm_lfo=fm_lfo, pwm_lfo=pwm_lfo, samplerate=self.samplerate)
        else:
            return FastPulse(frequency, amplitude*scale, phase, bias*scale, pulsewidth, pwm_lfo=pwm_lfo, samplerate=self.samplerate)

    def __harmonics(self, frequency, num_harmonics, amplitude, phase, bias, only_even, only_odd, fm_lfo):
        scale = self.__check_and_get_scale(frequency, amplitude, bias)
        return Harmonics(frequency, num_harmonics, amplitude*scale, phase, bias*scale, only_even=only_even, only_odd=only_odd, fm_lfo=fm_lfo, samplerate=self.samplerate)

    def __white_noise(self, amplitude, bias):
        scale = self.__check_and_get_scale(1, amplitude, bias)
        return WhiteNoise(amplitude*scale, bias*scale, samplerate=self.samplerate)

    def __linear(self, duration, start_amp, finish_amp):
        num_samples = int(duration*self.samplerate)
        increment = (finish_amp - start_amp) / (num_samples - 1)
        return Linear(start_amp, increment, samplerate=self.samplerate)

    def __check_and_get_scale(self, freq, amplitude, bias):
        assert freq <= self.samplerate/2    # don't exceed the Nyquist frequency
        assert 0 <= amplitude <= 1.0
        assert -1 <= bias <= 1.0
        scale = 2 ** (self.samplewidth * 8 - 1) - 1
        return scale

    def __render_sample(self, duration, wave):
        wave = iter(wave)
        samples = Sample.get_array(self.samplewidth)
        for _ in range(int(duration*self.samplerate)):
            samples.append(int(next(wave)))
        return Sample.from_array(samples, self.samplerate, 1)


class OscillatorBase:
    """
    Oscillator base class for several types of waveforms.
    You can also apply FM to an osc, and/or an ADSR envelope.
    These are generic oscillators and as such have floating-point inputs and result values
    with variable amplitude (though usually -1.0...1.0), depending on what parameters you use.
    Using a FM LFO is computationally quite heavy, so if you know you don't use FM,
    consider using the Fast versions instead. They contain optimized algorithms but
    some of their parameters cannot be changed.
    """
    def __init__(self, samplerate=None):
        self.samplerate = samplerate or Sample.norm_samplerate

    def __iter__(self):
        return self.generator()

    def envelope(self, attack, decay, sustain, sustain_level, release, stop_at_end=False, cycle=False):
        """
        Returns the oscillator with an ADSR volume envelope applied to it.
        A,D,S,R are in seconds, sustain_level is an amplitude factor.
        """
        assert attack >= 0 and decay >= 0 and sustain >= 0 and release >= 0
        assert 0 <= sustain_level <= 1
        def wrapper(oscillator):
            oscillator = iter(oscillator)
            while True:
                time = 0.0
                end_time_decay = attack + decay
                end_time_sustain = end_time_decay + sustain
                end_time_release = end_time_sustain + release
                increment = 1/self.samplerate
                if attack:
                    amp_change = 1/attack*increment
                    amp = 0.0
                    while time < attack:
                        yield next(oscillator)*amp
                        amp += amp_change
                        time += increment
                if decay:
                    amp = 1.0
                    amp_change = (sustain_level-1)/decay*increment
                    while time < end_time_decay:
                        yield next(oscillator)*amp
                        amp += amp_change
                        time += increment
                while time < end_time_sustain:
                    yield next(oscillator)*sustain_level
                    time += increment
                if release:
                    amp = sustain_level
                    amp_change = (-sustain_level)/release*increment
                    while time < end_time_release:
                        yield next(oscillator)*amp
                        amp += amp_change
                        time += increment
                    if amp > 0:
                        yield next(oscillator)*amp
                if not cycle:
                    break
            if not stop_at_end:
                while True:
                    yield 0.0
        return FilteredOscillator(self, wrapper)

    def mix(self, oscillator):
        """Mixes (adds) the wave from another oscillators together into one output wave."""
        for v in self:
            yield v+next(oscillator)

    def modulate_amp(self, modulator):
        """Modulate the amplitude of the wave of the oscillator by another oscillator (the modulator)."""
        for v in self:
            yield v*next(modulator)

    def delay(self, seconds):
        """
        Delays the oscillator.
        If you use a negative value, it skips ahead in time instead.
        Note that if you want to precisely phase-shift an oscillator, you should perhaps
        use the phase parameter on the oscillator function itself instead.
        """
        def delayfunc(oscillator):
            if seconds < 0:
                for _ in range(int(-self.samplerate*seconds)):
                    next(oscillator)
            else:
                for _ in range(int(self.samplerate*seconds)):
                    yield 0.0
            yield from oscillator
        return FilteredOscillator(self, delayfunc)

    def abs(self):
        """Returns the absolute values from the oscillator."""
        def wrapper(osc):
            for v in osc:
                yield fabs(v)
        return FilteredOscillator(self, wrapper)

    def custom(self, func):
        """Apply custom function to every oscillator value."""
        def wrapper(osc):
            return map(func, osc)
        return FilteredOscillator(self, wrapper)

    def clip(self, minimum=None, maximum=None):
        """Clips the values from the oscillator at the given mininum and/or maximum value."""
        assert not(minimum is None and maximum is None)
        if minimum is None:
            minimum = sys.float_info.min
        if maximum is None:
            maximum = sys.float_info.max
        def wrapper(osc):
            for v in osc:
                yield max(min(v, maximum), minimum)
        return FilteredOscillator(self, wrapper)

    def echo(self, after, amount, delay, decay):
        """
        Mix given number of echos of the oscillator into itself.
        The decay is the factor with which each echo is decayed in volume (can be >1 to increase in volume instead).
        If you use a very short delay the echos blend into the sound and the effect is more like a reverb.
        """
        return EchoingOscillator(self, after, amount, delay, decay)


class EchoingOscillator(OscillatorBase):
    # @todo not sure if I want this to be a wrapper like Oscillator or if it should be explicitly outside of it, like a FilterChain or something
    def __init__(self, oscillator, after, amount, delay, decay):
        super().__init__(oscillator.samplerate)
        if decay < 1:
            # avoid computing echos that you can't hear:
            amount = int(min(amount, log(0.000001, decay)))
        self._oscillator = oscillator
        self._after = after
        self._amount = amount
        self._delay = delay
        self._decay = decay

    def generator(self):
        oscillator = iter(self._oscillator)
        # first play the first part till the echos start
        for _ in range(int(self.samplerate*self._after)):
            yield next(oscillator)
        # now start mixing the echos
        amp = self._decay
        echo_oscs = [FilteredOscillator(osc, samplerate=self.samplerate) for osc in itertools.tee(oscillator, self._amount+1)]
        echos = [echo_oscs[0]]
        echo_delay = self._delay
        for echo in echo_oscs[1:]:
            echo = echo.delay(echo_delay)
            echo = echo.modulate_amp(itertools.repeat(amp))
            echos.append(echo)
            echo_delay += self._delay
            amp *= self._decay
        echos = [iter(echo) for echo in echos]
        while True:
            yield sum([next(echo) for echo in echos])


class FilteredOscillator(OscillatorBase):
    # @todo not sure if I want this to be a wrapper like Oscillator or if it should be explicitly outside of it, like a FilterChain or something
    def __init__(self, oscillator_or_iterable, wrapper=None, samplerate=None):
        if samplerate:
            super().__init__(samplerate)
        else:
            super().__init__(oscillator_or_iterable.samplerate)
        self._wrapper = wrapper
        self._oscillator = oscillator_or_iterable

    def generator(self):
        if self._wrapper:
            return self._wrapper(self._oscillator)
        return self._oscillator


class Sine(OscillatorBase):
    """Sine Wave oscillator."""
    def __init__(self, frequency, amplitude=1.0, phase=0.0, bias=0.0, fm_lfo=None, samplerate=Sample.norm_samplerate):
        # The FM compensates for the phase change by means of phase_correction.
        # See http://stackoverflow.com/questions/3089832/sine-wave-glissando-from-one-pitch-to-another-in-numpy
        # and http://stackoverflow.com/questions/28185219/generating-vibrato-sine-wave
        # The same idea is applied to the other waveforms to correct their phase with FM.
        super().__init__(samplerate)
        self.frequency = frequency
        self.amplitude = amplitude
        self._phase = phase
        self.bias = bias
        self.fm = iter(fm_lfo or itertools.repeat(0.0))

    def generator(self):
        phase_correction = self._phase*2*pi
        freq_previous = self.frequency
        increment = 2*pi/self.samplerate
        t = 0
        while True:
            freq = self.frequency*(1+next(self.fm))
            phase_correction += (freq_previous-freq)*t
            freq_previous = freq
            yield sin(t*freq+phase_correction)*self.amplitude+self.bias
            t += increment


class Triangle(OscillatorBase):
    """Perfect triangle wave oscillator (not using harmonics)."""
    def __init__(self, frequency, amplitude=1.0, phase=0.0, bias=0.0, fm_lfo=None, samplerate=Sample.norm_samplerate):
        super().__init__(samplerate)
        self.frequency = frequency
        self.amplitude = amplitude
        self._phase = phase
        self.bias = bias
        self.fm = iter(fm_lfo or itertools.repeat(0.0))

    def generator(self):
        phase_correction = self._phase
        freq_previous = self.frequency
        increment = 1/self.samplerate
        t = 0
        while True:
            freq = self.frequency * (1+next(self.fm))
            phase_correction += (freq_previous-freq)*t
            freq_previous = freq
            tt = t*freq+phase_correction
            yield 4*self.amplitude*(abs((tt+0.75) % 1 - 0.5)-0.25)+self.bias
            t += increment


class Square(OscillatorBase):
    """Perfect square wave [max/-max] oscillator (not using harmonics)."""
    def __init__(self, frequency, amplitude=1.0, phase=0.0, bias=0.0, fm_lfo=None, samplerate=Sample.norm_samplerate):
        super().__init__(samplerate)
        self.frequency = frequency
        self.amplitude = amplitude
        self._phase = phase
        self.bias = bias
        self.fm = iter(fm_lfo or itertools.repeat(0.0))

    def generator(self):
        phase_correction = self._phase
        freq_previous = self.frequency
        increment = 1/self.samplerate
        t = 0
        while True:
            freq = self.frequency*(1+next(self.fm))
            phase_correction += (freq_previous-freq)*t
            freq_previous = freq
            tt = t*freq + phase_correction
            yield (-self.amplitude if int(tt*2) % 2 else self.amplitude)+self.bias
            t += increment


class Sawtooth(OscillatorBase):
    """Perfect sawtooth waveform oscillator (not using harmonics)."""
    def __init__(self, frequency, amplitude=1.0, phase=0.0, bias=0.0, fm_lfo=None, samplerate=Sample.norm_samplerate):
        super().__init__(samplerate)
        self.frequency = frequency
        self.amplitude = amplitude
        self._phase = phase
        self.bias = bias
        self.fm = iter(fm_lfo or itertools.repeat(0.0))

    def generator(self):
        increment = 1/self.samplerate
        freq_previous = self.frequency
        phase_correction = self._phase
        t = 0
        while True:
            freq = self.frequency*(1+next(self.fm))
            phase_correction += (freq_previous-freq)*t
            freq_previous = freq
            tt = t*freq + phase_correction
            yield self.bias+self.amplitude*2*(tt - floor(0.5+tt))
            t += increment


class Pulse(OscillatorBase):
    """
    Oscillator for a perfect pulse waveform (not using harmonics).
    Optional FM and/or Pulse-width modulation. If you use PWM, pulsewidth is ignored.
    The pwm_lfo oscillator will be clipped between 0 and 1 as pulse width factor.
    """
    def __init__(self, frequency, amplitude=1.0, phase=0.0, bias=0.0, pulsewidth=0.1, fm_lfo=None, pwm_lfo=None, samplerate=Sample.norm_samplerate):
        super().__init__(samplerate)
        assert 0 <= pulsewidth <= 1
        self.frequency = frequency
        self.amplitude = amplitude
        self._phase = phase
        self.bias = bias
        self.pulsewidth = pulsewidth
        self.fm = iter(fm_lfo or itertools.repeat(0.0))
        self.pwm = iter(pwm_lfo or itertools.repeat(pulsewidth))

    def generator(self):
        epsilon = sys.float_info.epsilon
        increment = 1/self.samplerate
        freq_previous = self.frequency
        phase_correction = self._phase
        t = 0
        while True:
            pw = next(self.pwm)
            if pw <= 0:
                pw = epsilon
            elif pw >= 1:
                pw = 1.0-epsilon
            freq = self.frequency*(1+next(self.fm))
            phase_correction += (freq_previous-freq)*t
            freq_previous = freq
            tt = t*freq+phase_correction
            yield (self.amplitude if tt % 1 < pw else -self.amplitude)+self.bias
            t += increment


class Harmonics(OscillatorBase):
    """
    Oscillator that produces a waveform based on harmonics.
    This is computationally intensive because many sine waves are added together.
    """
    def __init__(self, frequency, num_harmonics, amplitude=1.0, phase=0.0, bias=0.0, only_even=False, only_odd=False, fm_lfo=None, samplerate=Sample.norm_samplerate):
        super().__init__(samplerate)
        self.frequency = frequency
        self.amplitude = amplitude
        self._phase = phase
        self.bias = bias
        self.fm = iter(fm_lfo or itertools.repeat(0.0))
        self.num_harmonics = num_harmonics
        self.only_even = only_even
        self.only_odd = only_odd

    def generator(self):
        increment = 2*pi/self.samplerate
        phase_correction = self._phase*2*pi
        freq_previous = self.frequency
        t = 0
        while True:
            # remove harmonics above the Nyquist frequency:
            num_harmonics = min(self.num_harmonics, int(self.samplerate/2/self.frequency))
            h = 0.0
            freq = self.frequency*(1+next(self.fm))
            phase_correction += (freq_previous-freq)*t
            freq_previous = freq
            q = t*freq + phase_correction
            if self.only_odd:
                for k in range(1, 2*num_harmonics, 2):
                    h += sin(q*k)/k
            elif self.only_even:
                h += sin(q)*0.7  # always include harmonic #1 as base
                for k in range(2, 2*num_harmonics, 2):
                    h += sin(q*k)/k
            else:
                for k in range(1, 1+num_harmonics):
                    h += sin(q*k)/k/2
            yield h*self.amplitude+self.bias
            t += increment


class SquareH(Harmonics):
    """
    Oscillator that produces a square wave based on harmonic sine waves.
    It is a lot heavier to generate than square because it has to add many individual sine waves.
    It's done by adding only odd-integer harmonics, see https://en.wikipedia.org/wiki/Square_wave
    """
    def __init__(self, frequency, num_harmonics=16, amplitude=1.0, phase=0.0, bias=0.0, fm_lfo=None, samplerate=Sample.norm_samplerate):
        super().__init__(frequency, num_harmonics, amplitude, phase, bias, only_odd=True, fm_lfo=fm_lfo, samplerate=samplerate)


class SawtoothH(Harmonics):
    """
    Oscillator that produces a sawtooth wave based on harmonic sine waves.
    It is a lot heavier to generate than square because it has to add many individual sine waves.
    It's done by adding all harmonics, see https://en.wikipedia.org/wiki/Sawtooth_wave
    """
    def __init__(self, frequency, num_harmonics=16, amplitude=1.0, phase=0.0, bias=0.0, fm_lfo=None, samplerate=Sample.norm_samplerate):
        super().__init__(frequency, num_harmonics, amplitude, phase+0.5, bias, fm_lfo=fm_lfo, samplerate=samplerate)

    def generator(self):
        for y in super().generator():
            yield self.bias*2-y


class WhiteNoise(OscillatorBase):
    """Oscillator that produces white noise (randomness) waveform."""
    def __init__(self, amplitude=1.0, bias=0.0, samplerate=Sample.norm_samplerate):
        super().__init__(samplerate)
        self.amplitude = amplitude
        self.bias = bias

    def generator(self):
        while True:
            yield random.uniform(-self.amplitude, self.amplitude) + self.bias


class Linear(OscillatorBase):
    """Oscillator that produces a linear sloped value, until it reaches a maximum or minimum value."""
    def __init__(self, startlevel, increment=0.0, min_value=-1.0, max_value=1.0, samplerate=Sample.norm_samplerate):
        super().__init__(samplerate)
        self.value = startlevel
        self.increment = increment
        self.min_value = min_value
        self.max_value = max_value

    def generator(self):
        while True:
            yield self.value
            if self.increment:
                self.value = min(self.max_value, max(self.min_value, self.value+self.increment))


class FastSine(OscillatorBase):
    """Fast sine wave oscillator. Some parameters cannot be changed."""
    def __init__(self, frequency, amplitude=1.0, phase=0.0, bias=0.0, samplerate=Sample.norm_samplerate):
        super().__init__(samplerate)
        self._frequency = frequency
        self._phase = phase
        self.amplitude = amplitude
        self.bias = bias

    def generator(self):
        rate = self.samplerate/self._frequency
        increment = 2*pi/rate
        t = self._phase*2*pi
        while True:
            yield sin(t)*self.amplitude+self.bias
            t += increment


class FastTriangle(OscillatorBase):
    """Fast perfect triangle wave oscillator (not using harmonics). Some parameters cannot be changed."""
    def __init__(self, frequency, amplitude=1.0, phase=0.0, bias=0.0, samplerate=Sample.norm_samplerate):
        super().__init__(samplerate)
        self._frequency = frequency
        self._phase = phase
        self.amplitude = amplitude
        self.bias = bias

    def generator(self):
        freq = self._frequency
        t = self._phase/freq
        increment = 1/self.samplerate
        while True:
            yield 4*self.amplitude*(abs((t*freq+0.75) % 1 - 0.5)-0.25)+self.bias
            t += increment


class FastSquare(OscillatorBase):
    """Fast perfect square wave [max/-max] oscillator (not using harmonics). Some parameters cannot be changed."""
    def __init__(self, frequency, amplitude=1.0, phase=0.0, bias=0.0, samplerate=Sample.norm_samplerate):
        super().__init__(samplerate)
        self._frequency = frequency
        self._phase = phase
        self.amplitude = amplitude
        self.bias = bias

    def generator(self):
        freq = self._frequency
        t = self._phase/freq
        increment = 1/self.samplerate
        while True:
            yield (-self.amplitude if int(t*freq*2) % 2 else self.amplitude)+self.bias
            t += increment


class FastSawtooth(OscillatorBase):
    """Fast perfect sawtooth waveform oscillator (not using harmonics). Some parameters canot be changed."""
    def __init__(self, frequency, amplitude=1.0, phase=0.0, bias=0.0, samplerate=Sample.norm_samplerate):
        super().__init__(samplerate)
        self._frequency = frequency
        self._phase = phase
        self.amplitude = amplitude
        self.bias = bias

    def generator(self):
        freq = self._frequency
        t = self._phase/freq
        increment = 1/self.samplerate
        while True:
            tt = t*freq
            yield self.bias+2*self.amplitude*(tt - floor(0.5+tt))
            t += increment


class FastPulse(OscillatorBase):
    """
    Fast oscillator that produces a perfect pulse waveform (not using harmonics).
    Some parameters cannot be changed.
    Optional Pulse-width modulation. If used, the pulsewidth argument is ignored.
    The pwm_lfo oscillator will be clipped between 0 and 1 as pulse width factor.
    """
    def __init__(self, frequency, amplitude=1.0, phase=0.0, bias=0.0, pulsewidth=0.1, pwm_lfo=None, samplerate=Sample.norm_samplerate):
        super().__init__(samplerate)
        assert 0 <= pulsewidth <= 1
        self._frequency = frequency
        self._phase = phase
        self._pulsewidth = pulsewidth
        self._pwm = pwm_lfo
        self.amplitude = amplitude
        self.bias = bias

    def generator(self):
        if self._pwm:
            # optimized loop without FM, but with PWM
            epsilon = sys.float_info.epsilon
            freq = self._frequency
            pwm = iter(self._pwm)
            t = self._phase/freq
            increment = 1/self.samplerate
            while True:
                pw = next(pwm)
                if pw <= 0:
                    pw = epsilon
                elif pw >= 1:
                    pw = 1.0-epsilon
                yield (self.amplitude if t*freq % 1 < pw else -self.amplitude)+self.bias
                t += increment
        else:
            # no FM, no PWM
            freq = self._frequency
            pw = self._pulsewidth
            t = self._phase/freq
            increment = 1/self.samplerate
            while True:
                yield (self.amplitude if t*freq % 1 < pw else -self.amplitude)+self.bias
                t += increment
