export type Device = {
    id: string;
    project: string;
    startDate: string;
    endDate: string;
    lastUpload: string;
    batteryLevel: number;
    folderSize: string;
    action: string;
    audioFiles: AudioFile[];
};

export type AudioFile = {
    id: string;
    config: string;
    samplerate: number;
    fileLength: string;
    fileSize: number;
};