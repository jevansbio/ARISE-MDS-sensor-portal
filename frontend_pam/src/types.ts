export type Device = {
    id: string;
    startDate: string;
    endDate: string;
    lastUpload: string;
    batteryLevel: number;
    folder_size: string;
    action: string;
    dataFile: DataFile[];
};

export type DataFile = {
    id: string;
    config: string;
    sample_rate: number;
    file_length: string;
    file_size: string;
    file_format: string;
};

export type ModalProps = {
    isOpen: boolean;
    onClose: () => void;
    children: React.ReactNode;
};