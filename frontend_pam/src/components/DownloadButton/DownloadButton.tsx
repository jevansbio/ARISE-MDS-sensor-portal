import { Button } from "@/components/ui/button";
import { FaDownload } from "react-icons/fa";
import { useContext } from "react";
import AuthContext from "@/auth/AuthContext";

interface DownloadButtonProps {
  fileId: string;
  fileFormat: string;
  className?: string;
}

export default function DownloadButton({
  fileId,
  fileFormat,
  className = "",
}: DownloadButtonProps) {
  const authContext = useContext(AuthContext) as any;
  const { authTokens } = authContext || { authTokens: null };

  const handleDownload = async () => {
    try {
      const response = await fetch(`/api/datafile/${fileId}/download/`, {
        headers: {
          Authorization: `Bearer ${authTokens.access}`,
        },
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => null);
        console.error("Download failed:", response.status, errorData);
        throw new Error(
          `Download failed: ${response.status} ${response.statusText}`
        );
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;

      const cleanFormat = fileFormat.toLowerCase().replace(/\./g, "");
      a.download = `audio_file_${fileId}.${cleanFormat}`;

      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error("Error downloading file:", error);
      alert("Failed to download file. Please check the console for details.");
    }
  };

  return (
    <Button
      variant="ghost"
      onClick={handleDownload}
      className={`flex items-center gap-2 ${className}`}
    >
      <FaDownload className="h-4 w-4" />
      Download
    </Button>
  );
}
