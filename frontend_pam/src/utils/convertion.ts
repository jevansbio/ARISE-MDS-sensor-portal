

export function bytesToMegabytes(bytes: string, decimals: number = 2): number {
    const megabytes = Number(bytes) / (1024 * 1024);
    return Number(megabytes.toFixed(decimals));
  }