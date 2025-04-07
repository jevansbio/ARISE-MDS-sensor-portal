import { differenceInDays } from 'date-fns';

export function formatTime(seconds: number): string {
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = Math.floor(seconds % 60);
  return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
} 

export function getPinColor (lastUpload: string | null): string {
  if (!lastUpload) return 'red'; // No upload date means red

  const lastUploadDate = new Date(lastUpload);
  const today = new Date();
  const daysSinceLastUpload = differenceInDays(today, lastUploadDate);

  return daysSinceLastUpload > 3 ? 'red' : 'green'; // red if > 3 days, green otherwise
}