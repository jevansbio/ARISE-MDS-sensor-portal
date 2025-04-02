import { useEffect, useRef, useState } from 'react';
import { Button } from '@/components/ui/button';
import { Slider } from '@/components/ui/slider';
import { FaPlay, FaPause, FaStepBackward, FaStepForward } from 'react-icons/fa';
import { formatTime } from '@/utils/timeFormat';
import AuthContext from '@/auth/AuthContext';
import { useContext } from 'react';

interface AuthContextType {
  user: any;
  authTokens: {
    access: string;
    refresh: string;
  } | null;
  loginUser: (e: React.FormEvent) => void;
  logoutUser: (e?: React.FormEvent) => void;
}

interface AudioWaveformPlayerProps {
  deviceId: string;
  fileId: string;
  fileFormat: string;
  className?: string;
}

export default function AudioWaveformPlayer({ deviceId, fileId, fileFormat, className = "" }: AudioWaveformPlayerProps) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [duration, setDuration] = useState(0);
  const [currentTime, setCurrentTime] = useState(0);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animationFrameRef = useRef<number>();
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const { authTokens } = useContext(AuthContext) as AuthContextType;

  useEffect(() => {
    const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
    audioContextRef.current = audioContext;
    
    const analyser = audioContext.createAnalyser();
    analyser.fftSize = 2048;
    analyserRef.current = analyser;

    if (!audioRef.current) {
      const audio = new Audio();
      audioRef.current = audio;

      audio.addEventListener('loadedmetadata', () => {
        setDuration(audio.duration);
        setIsLoading(false);
      });

      audio.addEventListener('timeupdate', () => {
        setCurrentTime(audio.currentTime);
      });

      audio.addEventListener('error', (e) => {
        console.error('Audio error:', e);
        if (isLoading) {
          setError('Error loading audio file');
        }
        setIsLoading(false);
      });
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
  }, []);


  useEffect(() => {
    if (authTokens?.access) {
      loadAudio(true);
    }
  }, [authTokens]);

  const loadAudio = async (isInitialLoad = false) => {
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
        const audioUrl = `/api/devices/${deviceId}/datafiles/${fileId}/download`;
        const response = await fetch(audioUrl, {
          headers: {
            'Authorization': `Bearer ${authTokens.access}`,
            'Accept': '*/*'
          }
        });
        
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const blob = await response.blob();
        const mimeType = fileFormat.toLowerCase() === 'mp3' ? 'audio/mpeg' : `audio/${fileFormat.toLowerCase()}`;
        const audioBlob = new Blob([blob], { type: mimeType });
        const objectUrl = URL.createObjectURL(audioBlob);
        
        if (audioRef.current) {
          audioRef.current.src = objectUrl;
          
          if (analyserRef.current) {
            try {
              const source = audioContextRef.current.createMediaElementSource(audioRef.current);
              source.connect(analyserRef.current);
              analyserRef.current.connect(audioContextRef.current.destination);
            } catch (error) {
              console.error('Error connecting audio to analyser:', error);
              if (!(error instanceof Error && error.message.includes('already connected'))) {
                throw error;
              }
            }
          }
          
          await audioRef.current.load();
        }
      }
      
      return true;
    } catch (error) {
      console.error('Error loading audio:', error);
      if (!isInitialLoad) {
        setError(error instanceof Error ? error.message : 'Failed to load audio');
      }
      return false;
    } finally {
      if (!isInitialLoad) {
        setIsLoading(false);
      }
    }
  };

  const togglePlayPause = async () => {
    if (!audioRef.current) return;
    
    try {
      setIsLoading(true);
      setError(null);
      
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
          await audioRef.current.play();
          startWaveformAnimation();
        } catch (playError) {
          console.error('Play error:', playError);
          throw new Error('Failed to play audio: format not supported');
        }
      }
      setIsPlaying(!isPlaying);
    } catch (error) {
      console.error('Error playing audio:', error);
      setError(error instanceof Error ? error.message : 'Failed to play audio');
      setIsPlaying(false);
    } finally {
      setIsLoading(false);
    }
  };

  const startWaveformAnimation = () => {
    if (!canvasRef.current || !analyserRef.current) return;

    const canvas = canvasRef.current;
    const analyser = analyserRef.current;
    const bufferLength = analyser.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);

    const draw = () => {
      animationFrameRef.current = requestAnimationFrame(draw);
      analyser.getByteTimeDomainData(dataArray);

      const ctx = canvas.getContext('2d');
      if (!ctx) return;

      ctx.fillStyle = 'rgb(200, 200, 200)';
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      ctx.lineWidth = 2;
      ctx.strokeStyle = 'rgb(0, 0, 0)';
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
    };

    draw();
  };

  const seek = (value: number[]) => {
    if (!audioRef.current) return;
    audioRef.current.currentTime = value[0];
    setCurrentTime(value[0]);
  };

  const stepBackward = () => {
    if (!audioRef.current) return;
    audioRef.current.currentTime = Math.max(0, audioRef.current.currentTime - 10);
  };

  const stepForward = () => {
    if (!audioRef.current) return;
    audioRef.current.currentTime = Math.min(duration, audioRef.current.currentTime + 10);
  };

  return (
    <div className={`bg-white rounded-lg shadow-md p-4 ${className}`}>
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            onClick={stepBackward}
            disabled={isLoading || currentTime <= 0}
            className="w-10 h-10 rounded-full"
          >
            <FaStepBackward className="h-4 w-4" />
          </Button>
          <Button
            variant="ghost"
            onClick={togglePlayPause}
            disabled={isLoading}
            className="w-10 h-10 rounded-full"
          >
            {isLoading ? (
              <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-gray-900" />
            ) : isPlaying ? (
              <FaPause className="h-4 w-4" />
            ) : (
              <FaPlay className="h-4 w-4" />
            )}
          </Button>
          <Button
            variant="ghost"
            onClick={stepForward}
            disabled={isLoading || currentTime >= duration}
            className="w-10 h-10 rounded-full"
          >
            <FaStepForward className="h-4 w-4" />
          </Button>
        </div>
        <div className="text-sm text-gray-600">
          {formatTime(currentTime)} / {formatTime(duration)}
        </div>
      </div>

      <div className="relative mb-4">
        <canvas
          ref={canvasRef}
          width={800}
          height={100}
          className="w-full h-24 bg-gray-100 rounded"
        />
        <Slider
          defaultValue={currentTime.toString()}
          max={duration.toString()}
          step="0.1"
          onChange={(e) => seek([parseFloat(e.target.value)])}
          className="absolute bottom-0 w-full [&::-webkit-slider-runnable-track]:h-2 [&::-webkit-slider-runnable-track]:rounded-full [&::-webkit-slider-runnable-track]:bg-gray-200 [&::-webkit-slider-runnable-track]:border [&::-webkit-slider-runnable-track]:border-gray-300 [&::-moz-range-track]:h-2 [&::-moz-range-track]:rounded-full [&::-moz-range-track]:bg-gray-200 [&::-moz-range-track]:border [&::-moz-range-track]:border-gray-300 [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-4 [&::-webkit-slider-thumb]:h-4 [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-blue-500 [&::-webkit-slider-thumb]:cursor-pointer [&::-webkit-slider-thumb]:border-2 [&::-webkit-slider-thumb]:border-white [&::-webkit-slider-thumb]:shadow-md [&::-moz-range-thumb]:appearance-none [&::-moz-range-thumb]:w-4 [&::-moz-range-thumb]:h-4 [&::-moz-range-thumb]:rounded-full [&::-moz-range-thumb]:bg-blue-500 [&::-moz-range-thumb]:cursor-pointer [&::-moz-range-thumb]:border-2 [&::-moz-range-thumb]:border-white [&::-moz-range-thumb]:shadow-md"
        />
      </div>

      {error && (
        <div className="text-red-500 text-sm mt-2">
          {error}
        </div>
      )}
    </div>
  );
} 