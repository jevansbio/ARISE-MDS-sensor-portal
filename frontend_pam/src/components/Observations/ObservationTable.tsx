import React, { useState, useEffect } from 'react';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { Trash2, Edit2, Play } from "lucide-react";
import { formatTime } from "@/utils/timeFormat";
import AudioWaveformPlayer from "../AudioWaveformPlayer/AudioWaveformPlayer";

interface Observation {
  id: number;
  obs_dt: string;
  source: string;
  extra_data: {
    start_time?: number;
    end_time?: number;
    duration?: number;
    avg_amplitude?: number;
    auto_detected?: boolean;
  };
  taxon?: {
    species_name: string;
    species_common_name: string;
  };
}

interface ObservationTableProps {
  deviceId: string;
  fileId: string;
  fileFormat: string;
  observations: Observation[];
  onDelete: (id: number) => void;
  onEdit: (observation: Observation) => void;
}

export function ObservationTable({ 
  deviceId,
  fileId, 
  fileFormat,
  observations,
  onDelete,
  onEdit
}: ObservationTableProps) {
  const [selectedObservation, setSelectedObservation] = useState<Observation | null>(null);

  const handlePlaySegment = (observation: Observation) => {
    setSelectedObservation(observation);
  };

  return (
    <div className="space-y-4">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Time</TableHead>
            <TableHead>Duration</TableHead>
            <TableHead>Species</TableHead>
            <TableHead>Source</TableHead>
            <TableHead>Actions</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {observations.map((observation) => (
            <TableRow key={observation.id}>
              <TableCell>
                {observation.obs_dt ? new Date(observation.obs_dt).toLocaleTimeString() : 'N/A'}
              </TableCell>
              <TableCell>
                {observation.extra_data.duration ? formatTime(observation.extra_data.duration) : 'N/A'}
              </TableCell>
              <TableCell>
                {observation.taxon ? (
                  <div>
                    <div className="font-medium">{observation.taxon.species_name}</div>
                    <div className="text-sm text-gray-500">{observation.taxon.species_common_name}</div>
                  </div>
                ) : (
                  <span className="text-gray-500">Unidentified</span>
                )}
              </TableCell>
              <TableCell>
                <span className={observation.extra_data.auto_detected ? "text-blue-600" : "text-green-600"}>
                  {observation.source}
                </span>
              </TableCell>
              <TableCell>
                <div className="flex items-center gap-2">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handlePlaySegment(observation)}
                  >
                    <Play className="h-4 w-4" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => onEdit(observation)}
                  >
                    <Edit2 className="h-4 w-4" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => onDelete(observation.id)}
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>

      {selectedObservation && (
        <div className="mt-4 p-4 border rounded-lg">
          <h3 className="text-lg font-medium mb-2">Selected Segment</h3>
          <AudioWaveformPlayer
            deviceId={deviceId}
            fileId={fileId}
            fileFormat={fileFormat}
            startTime={selectedObservation.extra_data.start_time}
            endTime={selectedObservation.extra_data.end_time}
          />
        </div>
      )}
    </div>
  );
} 