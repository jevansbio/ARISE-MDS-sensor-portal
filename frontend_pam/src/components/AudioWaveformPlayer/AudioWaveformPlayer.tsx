import { useEffect, useRef, useState, useCallback } from 'react';
import { Button } from '@/components/ui/button';
import { Slider } from '@/components/ui/slider';
import { Play, Pause, SkipBack, SkipForward, Volume2, VolumeX } from 'lucide-react';
import { formatTime } from '@/utils/timeFormat';
import AuthContext from '@/auth/AuthContext';
import { useContext } from 'react';

interface User {
  id: number;
  username: string;
  email: string;
}

interface AuthContextType {
  user: User | null;
  authTokens: {
    access: string;
    refresh: string;
  } | null;
  loginUser: (e: React.FormEvent) => void;
  logoutUser: (e?: React.FormEvent) => void;
}

interface AudioWaveformPlayerProps {
  fileId: string;
  className?: string;
  startTime?: number;
  endTime?: number;
  totalDuration?: number;
}

export default function AudioWaveformPlayer({ 
  fileId, 
  className = "",
  startTime = 0,
  endTime,
  totalDuration
}: AudioWaveformPlayerProps) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [duration, setDuration] = useState(0);
  const [currentTime, setCurrentTime] = useState(startTime);
  const [volume, setVolume] = useState(1);
  const [isMuted, setIsMuted] = useState(false);
  const [hasUserInteracted, setHasUserInteracted] = useState(false);
  const [isInitialized, setIsInitialized] = useState(false);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animationFrameRef = useRef<number>();
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const { authTokens } = useContext(AuthContext) as AuthContextType;

  const loadAudio = useCallback(async (isInitialLoad = false) => {
    if (!authTokens?.access || !audioContextRef.current) {
      if (!isInitialLoad) {
        setError("No authentication token available");
      }
      return false;
    }

    try {
      if (!isInitialLoad) {
        setIsLoading(true);
        setError(null);
      }

      if (!audioRef.current || !audioRef.current.src) {
        const audioUrl = `/api/datafile/${fileId}/download/`;
        const response = await fetch(audioUrl, {
          headers: {
            'Authorization': `Bearer ${authTokens.access}`,
            'Accept': '*/*'  // Accept any content type
          },
          credentials: 'include'
        });
        
        if (!response.ok) {
          console.error('Response status:', response.status);
          console.error('Response headers:', Object.fromEntries(response.headers.entries()));
          
          if (response.status === 404) {
            throw new Error('Audio file not found');
          }
          if (response.status === 403) {
            throw new Error('Authentication failed');
          }
          if (response.status === 406) {
            throw new Error('Server cannot provide audio in requested format');
          }
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const blob = await response.blob();
        const objectUrl = URL.createObjectURL(blob);
        
        if (audioRef.current) {
          audioRef.current.src = objectUrl;
          audioRef.current.load();
        }
      }
      
      return true;
    } catch (error) {
      console.error('Error loading audio:', error);
      setError(error instanceof Error ? error.message : 'Error loading audio file');
      setIsLoading(false);
      return false;
    }
  }, [authTokens, fileId]);

  const drawWaveform = useCallback(() => {
    if (!canvasRef.current || !audioRef.current || !analyserRef.current) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const analyser = analyserRef.current;
    const bufferLength = analyser.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);
    analyser.getByteTimeDomainData(dataArray);

    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.lineWidth = 2;
    ctx.strokeStyle = '#4f46e5';
    ctx.beginPath();

    const sliceWidth = canvas.width / bufferLength;
    let x = 0;

    for (let i = 0; i < bufferLength; i++) {
      const v = dataArray[i] / 128.0;
      const y = v * canvas.height / 2;

      if (i === 0) {
        ctx.moveTo(x, y);
      } else {
        ctx.lineTo(x, y);
      }

      x += sliceWidth;
    }

    ctx.lineTo(canvas.width, canvas.height / 2);
    ctx.stroke();
  }, []);

  useEffect(() => {
    const audioContext = new (window.AudioContext || (window as { webkitAudioContext?: typeof AudioContext }).webkitAudioContext)();
    audioContextRef.current = audioContext;
    
    const analyser = audioContext.createAnalyser();
    analyser.fftSize = 2048;
    analyserRef.current = analyser;

    if (!audioRef.current) {
      const audio = new Audio();
      audioRef.current = audio;

      audio.addEventListener('loadedmetadata', () => {
        setDuration(endTime ? endTime - startTime : audio.duration);
        setIsLoading(false);
        if (startTime !== undefined) {
          audio.currentTime = startTime;
        }
      });

      audio.addEventListener('timeupdate', () => {
        setCurrentTime(audio.currentTime);
        if (endTime !== undefined && audio.currentTime >= endTime) {
          audio.pause();
          setIsPlaying(false);
          if (startTime !== undefined) {
            audio.currentTime = startTime;
          }
        }
      });

      audio.addEventListener('ended', () => {
        setIsPlaying(false);
        if (startTime !== undefined) {
          audio.currentTime = startTime;
        }
      });

      audio.addEventListener('error', (e) => {
        console.error('Audio error:', e);
        if (isLoading) {
          setError('Error loading audio file');
        }
        setIsLoading(false);
      });

      const handleUserInteraction = () => {
        setHasUserInteracted(true);
        if (audioContextRef.current && audioContextRef.current.state === 'suspended') {
          audioContextRef.current.resume();
        }
      };

      window.addEventListener('click', handleUserInteraction, { once: true });
      window.addEventListener('touchstart', handleUserInteraction, { once: true });
    }

    return () => {
      if (audioContextRef.current) {
        audioContextRef.current.close();
      }
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current.src = '';
      }
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, [startTime, endTime]);

  useEffect(() => {
    const initAudio = async () => {
      if (authTokens?.access && !isInitialized) {
        try {
          await loadAudio(true);
          setIsInitialized(true);
        } catch (error) {
          console.error('Error initializing audio:', error);
        }
      }
    };
    
    initAudio();
  }, [authTokens, isInitialized, loadAudio]);

  useEffect(() => {
    if (canvasRef.current && audioRef.current && !isLoading) {
      drawWaveform();
    }
  }, [currentTime, isPlaying, duration, isLoading, drawWaveform]);

  // Reset current time when start time changes
  useEffect(() => {
    if (audioRef.current && startTime !== undefined) {
      audioRef.current.currentTime = startTime;
      setCurrentTime(startTime);
    }
  }, [startTime]);

  // Update duration when end time changes
  useEffect(() => {
    if (startTime !== undefined && endTime !== undefined) {
      setDuration(endTime - startTime);
    }
  }, [startTime, endTime]);

  const togglePlayPause = async () => {
    if (!audioRef.current) return;
    
    try {
      setIsLoading(true);
      setError(null);
      
      if (!hasUserInteracted) {
        setError('Please click or tap anywhere to enable audio playback');
        setIsLoading(false);
        return;
      }
      
      if (audioContextRef.current && audioContextRef.current.state === 'suspended') {
        await audioContextRef.current.resume();
      }
      
      if (!audioRef.current.src) {
        const success = await loadAudio(false);
        if (!success) {
          setIsLoading(false);
          return;
        }
      }
      
      if (isPlaying) {
        audioRef.current.pause();
      } else {
        try {
          const playPromise = audioRef.current.play();
          if (playPromise !== undefined) {
            await playPromise;
          }
        } catch {
          throw new Error('Failed to play audio: format not supported');
        }
      }
      setIsPlaying(!isPlaying);
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Failed to play audio');
      setIsPlaying(false);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSeek = (newTime: number) => {
    if (!audioRef.current) return;
    
    // Clamp the time to the observation boundaries
    const clampedTime = Math.min(
      endTime || duration,
      Math.max(startTime || 0, newTime)
    );
    
    audioRef.current.currentTime = clampedTime;
    setCurrentTime(clampedTime);
  };

  const handleVolumeChange = (newVolume: number) => {
    if (!audioRef.current) return;
    audioRef.current.volume = newVolume;
    setVolume(newVolume);
    setIsMuted(newVolume === 0);
  };

  const toggleMute = () => {
    if (!audioRef.current) return;
    if (isMuted) {
      audioRef.current.volume = volume;
      setIsMuted(false);
    } else {
      audioRef.current.volume = 0;
      setIsMuted(true);
    }
  };

  const skipBackward = () => {
    if (!audioRef.current) return;
    const newTime = Math.max(startTime, currentTime - 5);
    audioRef.current.currentTime = newTime;
    setCurrentTime(newTime);
  };

  const skipForward = () => {
    if (!audioRef.current) return;
    const newTime = Math.min(endTime || duration, currentTime + 5);
    audioRef.current.currentTime = newTime;
    setCurrentTime(newTime);
  };

  const formatAmplitude = (value: number): string => {
    if (value < 0.01) {
      return value.toFixed(4); // Show 4 decimal places for very small values
    }
    return value.toFixed(2);
  };

  return (
    <div className={`bg-white rounded-lg shadow-sm border ${className}`}>
      <div className="p-4 space-y-4">
        {/* Observation info */}
        {startTime !== undefined && endTime !== undefined && (
          <div className="text-sm text-gray-500 flex items-center justify-between">
            <span>Observation segment: {formatTime(endTime - startTime)}</span>
            <span>Full recording: {formatTime(totalDuration || duration)}</span>
          </div>
        )}

        {/* Waveform display */}
        <div className="relative h-24 bg-gray-50 rounded-lg overflow-hidden">
          <canvas
            ref={canvasRef}
            className="w-full h-full"
            width={800}
            height={96}
          />
          {isLoading && (
            <div className="absolute inset-0 flex items-center justify-center bg-white bg-opacity-75">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
            </div>
          )}
        </div>
        
        {/* Time and volume controls */}
        <div className="flex flex-col gap-1">
          <div className="flex items-center justify-between text-sm">
            <span className="font-medium w-24">
              {formatTime(currentTime)}
            </span>
            <div className="flex-1 mx-2">
              <Slider
                value={currentTime}
                min={0}
                max={endTime || duration}
                step={0.1}
                onChange={(e) => handleSeek(parseFloat(e.target.value))}
                className="w-full"
              />
            </div>
            <span className="font-medium w-24 text-right">
              {formatTime(endTime || duration)}
            </span>
          </div>
          
          {/* Context timeline */}
          {totalDuration && (
            <div className="flex items-center gap-2 px-1 text-xs text-gray-500">
              <div className="w-16 text-left">{formatTime(0)}</div>
              <div className="flex-1 h-1 bg-gray-100 rounded relative">
                {startTime !== undefined && endTime !== undefined && (
                  <div 
                    className="absolute h-full bg-blue-200"
                    style={{
                      left: `${(startTime / totalDuration) * 100}%`,
                      width: `${((endTime - startTime) / totalDuration) * 100}%`
                    }}
                  />
                )}
                <div 
                  className="absolute h-full w-0.5 bg-red-500"
                  style={{
                    left: `${(currentTime / totalDuration) * 100}%`
                  }}
                />
              </div>
              <div className="w-16 text-right">{formatTime(totalDuration)}</div>
            </div>
          )}
        </div>
        
        {/* Playback controls */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={toggleMute}
              className="hover:bg-gray-100"
            >
              {isMuted ? (
                <VolumeX className="h-4 w-4" />
              ) : (
                <Volume2 className="h-4 w-4" />
              )}
            </Button>
            <div className="w-24">
              <Slider
                value={isMuted ? 0 : volume * 100}
                min={0}
                max={100}
                step={1}
                onChange={(e) => handleVolumeChange(parseFloat(e.target.value) / 100)}
              />
            </div>
            <span className="text-xs text-gray-500 w-16">
              {formatAmplitude(isMuted ? 0 : volume)}
            </span>
          </div>
          
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="icon"
              onClick={skipBackward}
              disabled={currentTime <= startTime}
              className="h-8 w-8"
            >
              <SkipBack className="h-4 w-4" />
            </Button>
            
            <Button
              variant="outline"
              size="icon"
              onClick={togglePlayPause}
              disabled={isLoading}
              className="h-10 w-10 rounded-full"
            >
              {isLoading ? (
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-gray-900" />
              ) : isPlaying ? (
                <Pause className="h-4 w-4" />
              ) : (
                <Play className="h-4 w-4 ml-0.5" />
              )}
            </Button>
            
            <Button
              variant="ghost"
              size="icon"
              onClick={skipForward}
              disabled={currentTime >= (endTime || duration)}
              className="h-8 w-8"
            >
              <SkipForward className="h-4 w-4" />
            </Button>
          </div>
          
          <div className="w-32" /> {/* Spacer to balance layout */}
        </div>
      </div>
      
      {error && (
        <div className="px-4 pb-4">
          <div className="text-sm text-red-600 bg-red-50 rounded-md p-2">
            {error}
          </div>
        </div>
      )}
      
      {!hasUserInteracted && (
        <div className="px-4 pb-4">
          <div className="text-sm text-blue-600 bg-blue-50 rounded-md p-2">
            Click or tap anywhere to enable audio playback
          </div>
        </div>
      )}
    </div>
  );
}