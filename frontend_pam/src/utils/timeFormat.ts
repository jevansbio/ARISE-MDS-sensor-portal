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

import { differenceInSeconds, differenceInMinutes, differenceInHours, differenceInDays, differenceInMonths, differenceInYears } from 'date-fns';

export function timeSinceLastUpload(lastUpload: string | null): string {
  if (!lastUpload) return '';

  const lastUploadDate = new Date(lastUpload);
  const now = new Date();

  const seconds = differenceInSeconds(now, lastUploadDate);
  if (seconds < 60) {
    return `${seconds} second${seconds === 1 ? '' : 's'}`;
  }

  const minutes = differenceInMinutes(now, lastUploadDate);
  if (minutes < 60) {
    return `${minutes} minute${minutes === 1 ? '' : 's'}`;
  }

  const hours = differenceInHours(now, lastUploadDate);
  if (hours < 24) {
    return `${hours} hour${hours === 1 ? '' : 's'}`;
  }

  const days = differenceInDays(now, lastUploadDate);
  if (days < 30) {
    return `${days} day${days === 1 ? '' : 's'}`;
  }

  const months = differenceInMonths(now, lastUploadDate);
  if (months < 12) {
    return `${months} month${months === 1 ? '' : 's'}`;
  }

  const years = differenceInYears(now, lastUploadDate);
  return `${years} year${years === 1 ? '' : 's'}`;
}
