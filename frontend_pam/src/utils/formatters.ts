/**
 * Format a file size in bytes to a human-readable string
 * @param bytes The file size in bytes
 * @returns A formatted string (e.g., "1.5 MB", "800 KB", etc.)
 */
export function formatFileSize(bytes: number): string {
  const units = ['B', 'KB', 'MB', 'GB', 'TB'];
  let size = bytes;
  let unitIndex = 0;

  while (size >= 1024 && unitIndex < units.length - 1) {
    size /= 1024;
    unitIndex++;
  }

  return `${size.toFixed(1)} ${units[unitIndex]}`;
} 