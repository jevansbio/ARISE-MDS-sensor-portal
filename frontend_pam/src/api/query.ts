import { Device, DataFile } from "@/types";
import { queryOptions } from "@tanstack/react-query";

const API_URL = 'http://localhost:3001/devices';

const fetchDevices = async (): Promise<Device[]> => {
    const response = await fetch(API_URL);
    if (!response.ok) {
      throw new Error('Network response was not ok');
    }
    return response.json();
  };

export const devicesQueryOptions = queryOptions<Device[]>({
    queryKey: ['devices'], // The unique key for this query
    queryFn: fetchDevices, // The function to fetch data
})

const fetchDeviceById = async (id: string): Promise<Device> => {
  const response = await fetch(`${API_URL}/${id}`);
  if (!response.ok) {
    throw new Error(`Device not found (ID: ${id})`);
  }
  return response.json();
};

export const deviceQueryOptions = (deviceId: string) => queryOptions<Device>({
    queryKey: ['device', deviceId],
    queryFn: () => fetchDeviceById(deviceId),
});

const fetchAudioFiles = async (deviceId: string): Promise<DataFile[]> => {
  const responseJson = fetchDeviceById(deviceId);
  const device: Device = await responseJson;
  return device.dataFile;
}

export const audioFilesQueryOptions = (deviceId: string) => queryOptions<DataFile[]>({
    queryKey: ['audioFiles', deviceId],
    queryFn: () => fetchAudioFiles(deviceId),
});

const fetchAudioFileById = async (deviceId: string, audioFileId: string): Promise<DataFile> => {
  const responseJson = fetchDeviceById(deviceId);
  const device: Device = await responseJson;
  const audioFile = device.dataFile.find((file) => file.id === audioFileId);
  if (!audioFile) {
    throw new Error(`Audio file not found (ID: ${audioFileId})`);
  }
  return audioFile;
}

export const audioFileQueryOptions = (deviceId: string, audioFileId: string) => queryOptions<DataFile>({
    queryKey: ['audioFile', deviceId, audioFileId],
    queryFn: () => fetchAudioFileById(deviceId, audioFileId),
});

export const deviceOptions = (deviceId: string) => queryOptions({
  queryKey: ['device', deviceId],
  queryFn: () => getDevice(deviceId),
});

export const dataFileOptions = (deviceId: string, dataFileId: string) => queryOptions({
  queryKey: ['dataFile', deviceId, dataFileId],
  queryFn: () => getDataFile(deviceId, dataFileId),
});

export async function getDevices(): Promise<Device[]> {
  const response = await fetch("/api/devices");
  if (!response.ok) {
    throw new Error("Failed to fetch devices");
  }
  return response.json();
}

export async function getDevice(deviceId: string): Promise<Device> {
  const response = await fetch(`/api/devices/${deviceId}`);
  if (!response.ok) {
    throw new Error("Failed to fetch device");
  }
  return response.json();
}

export async function getDataFiles(deviceId: string): Promise<DataFile[]> {
  const device = await getDevice(deviceId);
  return device.dataFile;
}

export async function getDataFile(deviceId: string, dataFileId: string): Promise<DataFile | undefined> {
  const device = await getDevice(deviceId);
  const dataFile = device.dataFile.find((file) => file.id === dataFileId);
  if (!dataFile) {
    throw new Error("Data file not found");
  }
  return dataFile;
}