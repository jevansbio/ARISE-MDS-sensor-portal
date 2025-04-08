import os
import librosa
import numpy as np
from datetime import timedelta
from django.utils import timezone
from data_models.models import DataFile
import logging
from observation_editor.models import Observation, Taxon

logger = logging.getLogger(__name__)

class AudioQualityChecker:
    """Service for checking audio file quality"""
    
    @staticmethod
    def create_observations_from_segments(data_file, non_silent_segments, rms, hop_length, sr):
        """
        Create observations for significant audio segments
        Returns list of created observations
        """
        observations = []
        
        # Configuration for observation detection
        MIN_DURATION = 1.0  # Minimum duration in seconds
        MAX_DURATION = 30.0  # Maximum duration in seconds
        MIN_AMPLITUDE = 0.0005  # Minimum RMS amplitude 
        MAX_GAP = 5.0  # Maximum gap between segments to merge in seconds
        MAX_OBSERVATIONS = 50  # Maximum number of observations per file
        
        logger.info(f"Starting observation creation with {len(non_silent_segments)} segments")
        logger.info(f"Criteria: min_duration={MIN_DURATION}s, min_amplitude={MIN_AMPLITUDE}, max_gap={MAX_GAP}s")
        
        # Get or create a default "Unknown" taxon for auto-detected observations
        try:
            unknown_taxon = Taxon.objects.get_or_create(
                species_name="Unknown",
                defaults={
                    "species_common_name": "Auto-detected sound",
                    "taxon_source": 0  # custom source
                }
            )[0]
        except Exception as e:
            logger.error(f"Error creating default taxon: {str(e)}")
            return []

        # Convert segments to list of dicts with timing and metrics
        segments_info = []
        short_segments = 0
        low_amplitude_segments = 0
        long_segments = 0  # Initialize the counter
        
        for i, segment in enumerate(non_silent_segments):
            start_time = float(segment[0] * hop_length / sr)
            end_time = float(segment[1] * hop_length / sr)
            duration = end_time - start_time
            
            # Skip segments that are too short or too long
            if duration < MIN_DURATION or duration > MAX_DURATION:
                if duration < MIN_DURATION:
                    short_segments += 1
                    if i < 5:  # Log details for first few segments only to avoid spam
                        logger.info(f"Segment {i} filtered out: duration {duration:.2f}s < {MIN_DURATION}s")
                if duration > MAX_DURATION:
                    long_segments += 1
                    if i < 5:  # Log details for first few segments only to avoid spam
                        logger.info(f"Segment {i} filtered out: duration {duration:.2f}s > {MAX_DURATION}s")
                continue
            
                
            # Calculate segment metrics
            segment_rms = rms[int(segment[0]/hop_length):int(segment[1]/hop_length)]
            avg_amplitude = float(np.mean(segment_rms))
            
            # Skip segments with low amplitude
            if avg_amplitude < MIN_AMPLITUDE:
                low_amplitude_segments += 1
                if i < 5:  # Log details for first few segments only to avoid spam
                    logger.info(f"Segment {i} filtered out: amplitude {avg_amplitude:.4f} < {MIN_AMPLITUDE}")
                continue
                
            segments_info.append({
                'start_time': start_time,
                'end_time': end_time,
                'duration': duration,
                'avg_amplitude': avg_amplitude
            })
        
        logger.info(f"Initial filtering: {short_segments} segments too short, {low_amplitude_segments} segments below amplitude threshold")
        logger.info(f"Remaining segments after initial filtering: {len(segments_info)}")
        
        # Merge nearby segments
        merged_segments = []
        if segments_info:
            current_segment = segments_info[0]
            merged_count = 0
            for next_segment in segments_info[1:]:
                gap = next_segment['start_time'] - current_segment['end_time']
                if gap <= MAX_GAP:
                    # Merge segments
                    merged_count += 1
                    logger.info(f"Merging segments: gap={gap:.2f}s (threshold: {MAX_GAP}s)")
                    logger.info(f"  First: {current_segment['start_time']:.2f}s - {current_segment['end_time']:.2f}s")
                    logger.info(f"  Second: {next_segment['start_time']:.2f}s - {next_segment['end_time']:.2f}s")
                    current_segment['end_time'] = next_segment['end_time']
                    current_segment['duration'] = current_segment['end_time'] - current_segment['start_time']
                    current_segment['avg_amplitude'] = max(current_segment['avg_amplitude'], next_segment['avg_amplitude'])
                else:
                    merged_segments.append(current_segment)
                    current_segment = next_segment
            merged_segments.append(current_segment)
            
            logger.info(f"Merged {merged_count} segment pairs, resulting in {len(merged_segments)} segments")
        
        # Sort segments by amplitude and take top MAX_OBSERVATIONS
        merged_segments.sort(key=lambda x: x['avg_amplitude'], reverse=True)
        if len(merged_segments) > MAX_OBSERVATIONS:
            logger.info(f"Limiting to top {MAX_OBSERVATIONS} segments by amplitude")
            logger.info(f"Amplitude range: {merged_segments[0]['avg_amplitude']:.4f} to {merged_segments[-1]['avg_amplitude']:.4f}")
            merged_segments = merged_segments[:MAX_OBSERVATIONS]
        
        logger.info(f"Found {len(merged_segments)} significant audio segments")
        
        # Create observations for merged segments
        for i, segment in enumerate(merged_segments):
            try:
                observation = Observation.objects.create(
                    source="auto_detect",
                    taxon=unknown_taxon,
                    obs_dt=timezone.now() + timedelta(seconds=segment['start_time']),
                    extra_data={
                        "start_time": segment['start_time'],
                        "end_time": segment['end_time'],
                        "duration": segment['duration'],
                        "avg_amplitude": segment['avg_amplitude'],
                        "auto_detected": True,
                        "needs_review": True
                    }
                )
                observation.data_files.add(data_file)
                observations.append(observation)
                logger.info(f"Created observation {i+1}/{len(merged_segments)}: start={segment['start_time']:.2f}s, duration={segment['duration']:.2f}s, amplitude={segment['avg_amplitude']:.4f}")
            except Exception as e:
                logger.error(f"Error creating observation: {str(e)}")
                continue
            
        return observations

    @staticmethod
    def check_audio_quality(file_path):
        """
        Perform quality checks on an audio file
        Returns a dict with quality metrics and issues
        """
        try:
            logger.info(f"Starting quality check for file: {file_path}")
            # Load the audio file
            y, sr = librosa.load(file_path)
            
            logger.info(f"Successfully loaded audio file with sample rate: {sr}")
            
            # Calculate basic metrics
            duration = float(librosa.get_duration(y=y, sr=sr))
            
            # Temporal analysis
            frame_length = int(sr * 0.025)  # 25ms frames
            hop_length = int(sr * 0.010)    # 10ms hop
            
            # RMS energy over time
            rms = librosa.feature.rms(y=y, frame_length=frame_length, hop_length=hop_length)[0]
            rms_mean = float(np.mean(rms))
            rms_std = float(np.std(rms))
            silence_ratio = float(np.mean(rms < 0.01))
            
            # Detect segments of silence and activity
            silence_threshold = 0.01
            is_silent = rms < silence_threshold
            silent_segments = librosa.effects.split(y, top_db=40, frame_length=frame_length, hop_length=hop_length)
            num_segments = len(silent_segments)
            
            # Spectral analysis
            S = np.abs(librosa.stft(y, n_fft=frame_length, hop_length=hop_length))
            
            # Spectral centroid (brightness)
            cent = librosa.feature.spectral_centroid(S=S, sr=sr)[0]
            cent_mean = float(np.mean(cent))
            
            # Spectral bandwidth (spread of frequencies)
            band = librosa.feature.spectral_bandwidth(S=S, sr=sr)[0]
            band_mean = float(np.mean(band))
            
            # Spectral rolloff (frequency below which 85% of energy is contained)
            rolloff = librosa.feature.spectral_rolloff(S=S, sr=sr)[0]
            rolloff_mean = float(np.mean(rolloff))
            
            # Zero crossing rate (noisiness)
            zcr = librosa.feature.zero_crossing_rate(y, frame_length=frame_length, hop_length=hop_length)[0]
            zcr_mean = float(np.mean(zcr))
            
            # Check for clipping
            clipping_ratio = float(np.mean(np.abs(y) > 0.99))
            
            # Check for DC offset
            dc_offset = float(np.mean(y))
            
            # Calculate signal-to-noise ratio (SNR)
            noise_floor = float(np.percentile(np.abs(y), 10))
            signal_peak = float(np.percentile(np.abs(y), 90))
            snr = float(20 * np.log10(signal_peak / noise_floor) if noise_floor > 0 else 0)
            
            logger.info(f"Calculated metrics - duration: {duration}, silence: {silence_ratio}, clipping: {clipping_ratio}, SNR: {snr}")
            
            # Determine quality score (0-100) with more nuanced criteria
            quality_score = 100.0
            
            # Deduct points for technical issues
            if clipping_ratio > 0.01:  # More than 1% clipping
                quality_score -= 20
                
            if abs(dc_offset) > 0.1:  # Significant DC offset
                quality_score -= 15
                
            if snr < 20:  # Poor signal-to-noise ratio
                quality_score -= max(0, min(25, (20 - snr)))
            
            # Analyze content quality
            if silence_ratio > 0.8:  # More than 80% silence
                quality_score -= 40
            elif silence_ratio > 0.5:  # More than 50% silence
                quality_score -= 20
            elif silence_ratio > 0.3:  # More than 30% silence
                quality_score -= 10
                
            if num_segments < 2 and duration > 5:  # No significant audio events in long recording
                quality_score -= 30
            
            if zcr_mean > 0.4:  # Very noisy signal
                quality_score -= 15
            
            # Collect detailed issues and observations
            issues = []
            observations = []
            
            # Technical issues
            if clipping_ratio > 0.01:
                issues.append(f"Audio clipping detected: {clipping_ratio:.2%} of samples")
            if abs(dc_offset) > 0.1:
                issues.append(f"Significant DC offset: {dc_offset:.3f}")
            if snr < 20:
                issues.append(f"Low signal-to-noise ratio: {snr:.1f} dB")
            
            # Content analysis
            if silence_ratio > 0.8:
                issues.append(f"Extremely high silence content: {silence_ratio:.1%}")
            elif silence_ratio > 0.5:
                issues.append(f"High silence content: {silence_ratio:.1%}")
            elif silence_ratio > 0.3:
                observations.append(f"Moderate silence content: {silence_ratio:.1%}")
            
            if num_segments < 2 and duration > 5:
                issues.append("No significant audio events detected")
            else:
                observations.append(f"Detected {num_segments} distinct audio segments")
            
            if zcr_mean > 0.4:
                issues.append(f"High noise level detected (ZCR: {zcr_mean:.3f})")
            
            # Add spectral observations
            if cent_mean > 2000:
                observations.append("Audio contains predominantly high frequencies")
            elif cent_mean < 500:
                observations.append("Audio contains predominantly low frequencies")
            
            if band_mean > 2000:
                observations.append("Wide frequency spread (rich spectral content)")
            elif band_mean < 500:
                observations.append("Narrow frequency spread (limited spectral content)")
            
            logger.info(f"Quality check completed with score: {quality_score} and {len(issues)} issues")
            
            # Temporal evolution data (downsampled for visualization)
            num_points = min(100, len(rms))  # Limit to 100 points
            step = len(rms) // num_points if len(rms) > num_points else 1
            
            temporal_data = {
                'times': [float(t) for t in np.arange(len(rms))[::step] * hop_length / sr][:num_points],
                'rms_energy': [float(x) for x in rms[::step]][:num_points],
                'spectral_centroid': [float(x) for x in cent[::step]][:num_points],
                'zero_crossing_rate': [float(x) for x in zcr[::step]][:num_points]
            }
            
            return {
                'quality_score': float(max(0, min(100, quality_score))),
                'quality_issues': issues,
                'observations': observations,
                'metrics': {
                    'duration': duration,
                    'silence_ratio': silence_ratio,
                    'clipping_ratio': clipping_ratio,
                    'dc_offset': dc_offset,
                    'snr': snr,
                    'num_segments': num_segments,
                    'rms_energy_mean': rms_mean,
                    'rms_energy_std': rms_std,
                    'spectral_centroid_mean': cent_mean,
                    'spectral_bandwidth_mean': band_mean,
                    'spectral_rolloff_mean': rolloff_mean,
                    'zero_crossing_rate_mean': zcr_mean
                },
                'temporal_evolution': temporal_data
            }
            
        except Exception as e:
            logger.error(f"Error during quality check: {str(e)}", exc_info=True)
            return {
                'quality_score': 0,
                'quality_issues': [f"Error analyzing audio: {str(e)}"],
                'observations': [],
                'metrics': {},
                'temporal_evolution': {}
            }
    
    @staticmethod
    def update_file_quality(data_file):
        """
        Update quality metrics for a DataFile instance
        """
        try:
            # Get the local file path
            file_path = os.path.join(data_file.path, data_file.local_path, f"{data_file.file_name}{data_file.file_format}")
            logger.info(f"Attempting to check quality for file: {file_path}")
            
            if not os.path.exists(file_path):
                logger.error(f"File not found: {file_path}")
                raise FileNotFoundError(f"Audio file not found: {file_path}")
            
            # Update status to in progress
            DataFile.objects.filter(id=data_file.id).update(quality_check_status='in_progress')
            logger.info("Updated status to in_progress")
            
            # Load audio file
            y, sr = librosa.load(file_path)
            logger.info(f"Loaded audio file: duration={len(y)/sr:.2f}s, sample_rate={sr}Hz")
            
            frame_length = int(sr * 0.025)  # 25ms frames
            hop_length = int(sr * 0.010)    # 10ms hop
            
            # RMS energy over time
            rms = librosa.feature.rms(y=y, frame_length=frame_length, hop_length=hop_length)[0]
            logger.info(f"Calculated RMS energy: mean={np.mean(rms):.3f}, std={np.std(rms):.3f}")
            
            # Detect segments of activity (non-silent segments)
            non_silent_segments = librosa.effects.split(y, top_db=40, frame_length=frame_length, hop_length=hop_length)
            logger.info(f"Detected {len(non_silent_segments)} non-silent segments")
            
            # Create observations for detected segments
            observations = AudioQualityChecker.create_observations_from_segments(
                data_file, non_silent_segments, rms, hop_length, sr
            )
            logger.info(f"Created {len(observations)} observations")
            
            # Perform quality check using the already loaded audio data
            quality_data = AudioQualityChecker.check_audio_quality_from_data(y, sr, frame_length, hop_length, rms)
            logger.info("Quality check completed")
            
            # Store the temporal evolution data in extra_data
            extra_data = {
                'quality_metrics': quality_data['metrics'],
                'temporal_evolution': quality_data['temporal_evolution'],
                'observations': quality_data['observations'],
                'auto_detected_observations': [obs.id for obs in observations]
            }
            
            # Update the data file with results using update() to skip validation
            DataFile.objects.filter(id=data_file.id).update(
                quality_score=quality_data['quality_score'],
                quality_issues=quality_data['quality_issues'],
                quality_check_dt=timezone.now(),
                quality_check_status='completed',
                extra_data=extra_data
            )
            logger.info(f"Updated file with quality results: score={quality_data['quality_score']}, issues={len(quality_data['quality_issues'])}")
            
            return quality_data
            
        except Exception as e:
            logger.error(f"Error in update_file_quality: {str(e)}", exc_info=True)
            DataFile.objects.filter(id=data_file.id).update(
                quality_check_status='failed',
                quality_issues=[f"Failed to check quality: {str(e)}"]
            )
            raise

    @staticmethod
    def check_audio_quality_from_data(y, sr, frame_length, hop_length, rms=None):
        """
        Perform quality checks on audio data that's already loaded
        Returns a dict with quality metrics and issues
        """
        try:
            logger.info("Starting quality check on loaded audio data")
            
            # Calculate basic metrics
            duration = float(librosa.get_duration(y=y, sr=sr))
            
            # Calculate RMS if not provided
            if rms is None:
                rms = librosa.feature.rms(y=y, frame_length=frame_length, hop_length=hop_length)[0]
            
            rms_mean = float(np.mean(rms))
            rms_std = float(np.std(rms))
            silence_ratio = float(np.mean(rms < 0.01))
            
            # Detect segments of silence and activity
            silence_threshold = 0.01
            is_silent = rms < silence_threshold
            silent_segments = librosa.effects.split(y, top_db=40, frame_length=frame_length, hop_length=hop_length)
            num_segments = len(silent_segments)
            
            # Spectral analysis
            S = np.abs(librosa.stft(y, n_fft=frame_length, hop_length=hop_length))
            
            # Spectral centroid (brightness)
            cent = librosa.feature.spectral_centroid(S=S, sr=sr)[0]
            cent_mean = float(np.mean(cent))
            
            # Spectral bandwidth (spread of frequencies)
            band = librosa.feature.spectral_bandwidth(S=S, sr=sr)[0]
            band_mean = float(np.mean(band))
            
            # Spectral rolloff (frequency below which 85% of energy is contained)
            rolloff = librosa.feature.spectral_rolloff(S=S, sr=sr)[0]
            rolloff_mean = float(np.mean(rolloff))
            
            # Zero crossing rate (noisiness)
            zcr = librosa.feature.zero_crossing_rate(y, frame_length=frame_length, hop_length=hop_length)[0]
            zcr_mean = float(np.mean(zcr))
            
            # Check for clipping
            clipping_ratio = float(np.mean(np.abs(y) > 0.99))
            
            # Check for DC offset
            dc_offset = float(np.mean(y))
            
            # Calculate signal-to-noise ratio (SNR)
            noise_floor = float(np.percentile(np.abs(y), 10))
            signal_peak = float(np.percentile(np.abs(y), 90))
            snr = float(20 * np.log10(signal_peak / noise_floor) if noise_floor > 0 else 0)
            
            logger.info(f"Calculated metrics - duration: {duration}, silence: {silence_ratio}, clipping: {clipping_ratio}, SNR: {snr}")
            
            # Determine quality score (0-100) with more nuanced criteria
            quality_score = 100.0
            
            # Deduct points for technical issues
            if clipping_ratio > 0.01:  # More than 1% clipping
                quality_score -= 20
                
            if abs(dc_offset) > 0.1:  # Significant DC offset
                quality_score -= 15
                
            if snr < 20:  # Poor signal-to-noise ratio
                quality_score -= max(0, min(25, (20 - snr)))
            
            # Analyze content quality
            if silence_ratio > 0.8:  # More than 80% silence
                quality_score -= 40
            elif silence_ratio > 0.5:  # More than 50% silence
                quality_score -= 20
            elif silence_ratio > 0.3:  # More than 30% silence
                quality_score -= 10
                
            if num_segments < 2 and duration > 5:  # No significant audio events in long recording
                quality_score -= 30
            
            if zcr_mean > 0.4:  # Very noisy signal
                quality_score -= 15
            
            # Collect detailed issues and observations
            issues = []
            observations = []
            
            # Technical issues
            if clipping_ratio > 0.01:
                issues.append(f"Audio clipping detected: {clipping_ratio:.2%} of samples")
            if abs(dc_offset) > 0.1:
                issues.append(f"Significant DC offset: {dc_offset:.3f}")
            if snr < 20:
                issues.append(f"Low signal-to-noise ratio: {snr:.1f} dB")
            
            # Content analysis
            if silence_ratio > 0.8:
                issues.append(f"Extremely high silence content: {silence_ratio:.1%}")
            elif silence_ratio > 0.5:
                issues.append(f"High silence content: {silence_ratio:.1%}")
            elif silence_ratio > 0.3:
                observations.append(f"Moderate silence content: {silence_ratio:.1%}")
            
            if num_segments < 2 and duration > 5:
                issues.append("No significant audio events detected")
            else:
                observations.append(f"Detected {num_segments} distinct audio segments")
            
            if zcr_mean > 0.4:
                issues.append(f"High noise level detected (ZCR: {zcr_mean:.3f})")
            
            # Add spectral observations
            if cent_mean > 2000:
                observations.append("Audio contains predominantly high frequencies")
            elif cent_mean < 500:
                observations.append("Audio contains predominantly low frequencies")
            
            if band_mean > 2000:
                observations.append("Wide frequency spread (rich spectral content)")
            elif band_mean < 500:
                observations.append("Narrow frequency spread (limited spectral content)")
            
            logger.info(f"Quality check completed with score: {quality_score} and {len(issues)} issues")
            
            # Temporal evolution data (downsampled for visualization)
            num_points = min(100, len(rms))  # Limit to 100 points
            step = len(rms) // num_points if len(rms) > num_points else 1
            
            temporal_data = {
                'times': [float(t) for t in np.arange(len(rms))[::step] * hop_length / sr][:num_points],
                'rms_energy': [float(x) for x in rms[::step]][:num_points],
                'spectral_centroid': [float(x) for x in cent[::step]][:num_points],
                'zero_crossing_rate': [float(x) for x in zcr[::step]][:num_points]
            }
            
            return {
                'quality_score': float(max(0, min(100, quality_score))),
                'quality_issues': issues,
                'observations': observations,
                'metrics': {
                    'duration': duration,
                    'silence_ratio': silence_ratio,
                    'clipping_ratio': clipping_ratio,
                    'dc_offset': dc_offset,
                    'snr': snr,
                    'num_segments': num_segments,
                    'rms_energy_mean': rms_mean,
                    'rms_energy_std': rms_std,
                    'spectral_centroid_mean': cent_mean,
                    'spectral_bandwidth_mean': band_mean,
                    'spectral_rolloff_mean': rolloff_mean,
                    'zero_crossing_rate_mean': zcr_mean
                },
                'temporal_evolution': temporal_data
            }
            
        except Exception as e:
            logger.error(f"Error during quality check: {str(e)}", exc_info=True)
            return {
                'quality_score': 0,
                'quality_issues': [f"Error analyzing audio: {str(e)}"],
                'observations': [],
                'metrics': {},
                'temporal_evolution': {}
            } 