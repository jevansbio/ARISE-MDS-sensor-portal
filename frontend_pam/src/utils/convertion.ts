

export function bytesToMegabytes(bytes: number, decimals: number = 2): number {
    const megabytes = Number(bytes) / (1024 * 1024);
    return Number(megabytes.toFixed(decimals));
  }