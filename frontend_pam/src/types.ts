export type Device = {
    id: string;
    startDate: string;
    endDate: string;
    lastUpload: string;
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

export type ModalProps = {
    isOpen: boolean;
    onClose: () => void;
    children: React.ReactNode;
};