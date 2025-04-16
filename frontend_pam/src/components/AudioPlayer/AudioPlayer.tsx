import { Button } from "@/components/ui/button";
import { FaPlay, FaPause } from "react-icons/fa";
import { useContext, useRef, useState, useEffect } from "react";
import AuthContext from "@/auth/AuthContext";

interface AudioPlayerProps {
  fileId: string;
  fileFormat?: string;
  className?: string;
}

interface AuthContextType {
  authTokens: {
    access: string;
    refresh: string;
  } | null;
  user: {
    username: string;
    email: string;
  } | null;
  loginUser: (username: string, password: string) => Promise<void>;
  logoutUser: () => void;
  refreshToken: () => Promise<void>;
}

export default function AudioPlayer({
  fileId,
  fileFormat = "mp3",
  className = "",
}: AudioPlayerProps) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const audioUrlRef = useRef<string | null>(null);

  const authContext = useContext(AuthContext) as AuthContextType;
  const { authTokens } = authContext || { authTokens: null };

  // Reset audio when fileId changes
  useEffect(() => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.src = "";
      setIsPlaying(false);
    }
    if (audioUrlRef.current) {
      URL.revokeObjectURL(audioUrlRef.current);
      audioUrlRef.current = null;
    }
  }, [fileId]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current.src = "";
      }
      if (audioUrlRef.current) {
        URL.revokeObjectURL(audioUrlRef.current);
      }
    };
  }, []);

  const handlePlayPause = async () => {
    try {
      if (!audioRef.current?.src) {
        setIsLoading(true);
        setError(null);

        if (!audioRef.current) {
          audioRef.current = new Audio();
          audioRef.current.preload = "auto";

          audioRef.current.addEventListener("ended", () => {
            setIsPlaying(false);
            // Optional: reset the audio to start
            if (audioRef.current) {
              audioRef.current.currentTime = 0;
            }
          });

          audioRef.current.addEventListener("error", (e) => {
            const audioError = (e.currentTarget as HTMLAudioElement).error;
            console.error("Audio error:", {
              code: audioError?.code,
              message: audioError?.message,
            });
            setError(
              `Failed to play audio: ${audioError?.message || "format not supported"}`
            );
            setIsPlaying(false);
          });

          audioRef.current.addEventListener("canplay", () => {
            setIsLoading(false);
          });
        }

        try {
          const response = await fetch(`/api/datafile/${fileId}/download/`, {
            headers: {
              'Authorization': `Bearer ${authTokens?.access || ''}`,
              'Accept': '*/*'
            },
            credentials: "include",
          });

          if (!response.ok) {
            console.error('Response status:', response.status);
            console.error('Response headers:', Object.fromEntries(response.headers.entries()));
            if (response.status === 404) {
              throw new Error('Audio file not found. Please check if the file exists.');
            }
            throw new Error(`HTTP error! status: ${response.status}`);
          }

          const blob = await response.blob();

          // Use the blob's type if available, otherwise determine from file format
          const mimeType =
            blob.type ||
            (fileFormat?.toLowerCase()?.startsWith(".")
              ? `audio/${fileFormat.toLowerCase().substring(1)}`
              : `audio/${fileFormat?.toLowerCase() || 'mp3'}`);

          // Create a new blob with the correct MIME type
          const audioBlob = new Blob([blob], { type: mimeType });

          // Clean up previous URL if it exists
          if (audioUrlRef.current) {
            URL.revokeObjectURL(audioUrlRef.current);
          }

          // Create and store new URL
          audioUrlRef.current = URL.createObjectURL(audioBlob);

          audioRef.current.src = audioUrlRef.current;
          await audioRef.current.load();
        } catch (error) {
          console.error("Error fetching audio:", error);
          throw new Error(
            `Failed to fetch audio: ${error instanceof Error ? error.message : "unknown error"}`
          );
        }
      }

      if (isPlaying) {
        audioRef.current?.pause();
      } else {
        try {
          const playPromise = audioRef.current?.play();
          if (playPromise !== undefined) {
            await playPromise;
          }
        } catch (playError) {
          console.error("Play error:", playError);
          throw new Error("Failed to play audio: format not supported");
        }
      }
      setIsPlaying(!isPlaying);
    } catch (error) {
      console.error("Error playing audio:", error);
      setError(error instanceof Error ? error.message : "Failed to play audio");
      setIsPlaying(false);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className={`flex items-center gap-2 ${className}`}>
      <Button
        variant="ghost"
        onClick={handlePlayPause}
        disabled={isLoading}
        className="w-10 h-10 rounded-full flex items-center justify-center"
      >
        {isLoading ? (
          <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-gray-900" />
        ) : isPlaying ? (
          <FaPause className="h-4 w-4" />
        ) : (
          <FaPlay className="h-4 w-4" />
        )}
      </Button>
      {error && <p className="text-red-500 text-sm">{error}</p>}
    </div>
  );
}
