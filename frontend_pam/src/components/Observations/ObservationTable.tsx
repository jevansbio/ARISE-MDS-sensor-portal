import React, { useState } from 'react';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { Trash2, Edit2, Play, Pause, Volume2 } from "lucide-react";
import { formatTime } from "@/utils/timeFormat";
import AudioWaveformPlayer from "../AudioWaveformPlayer/AudioWaveformPlayer";
import { Badge } from "@/components/ui/badge";
import { type Observation } from '@/types';

interface ObservationTableProps {
  deviceId: string;
  fileId: string;
  fileFormat: string;
  fileDuration: number;
  observations: Observation[];
  onDelete: (id: number) => void;
  onEdit: (observation: Observation) => void;
}

export function ObservationTable({ 
  deviceId,
  fileId, 
  fileFormat,
  fileDuration,
  observations,
  onDelete,
  onEdit
}: ObservationTableProps) {
  const [selectedObservation, setSelectedObservation] = useState<Observation | null>(null);
  const [expandedObservation, setExpandedObservation] = useState<number | null>(null);

  const handlePlaySegment = (observation: Observation) => {
    if (selectedObservation?.id === observation.id) {
      setSelectedObservation(null);
      setExpandedObservation(null);
    } else {
      setSelectedObservation(observation);
      setExpandedObservation(observation.id);
    }
  };

  const getSourceBadgeStyle = (source: string, autoDetected: boolean | undefined, needsReview: boolean | undefined) => {
    if (autoDetected) {
      return needsReview 
        ? "bg-yellow-100 text-yellow-800 hover:bg-yellow-200" 
        : "bg-blue-100 text-blue-800 hover:bg-blue-200";
    }
    return "bg-green-100 text-green-800 hover:bg-green-200";
  };

  return (
    <div className="space-y-4 bg-white rounded-lg shadow">
      <Table>
        <TableHeader className="bg-gray-50">
          <TableRow>
            <TableHead className="w-[180px]">Time</TableHead>
            <TableHead className="w-[100px]">Duration</TableHead>
            <TableHead>Species</TableHead>
            <TableHead className="w-[120px]">Source</TableHead>
            <TableHead className="w-[140px]">Actions</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {observations.map((observation) => (
            <React.Fragment key={observation.id}>
              <TableRow 
                className={expandedObservation === observation.id ? 'bg-gray-50' : ''}
                onClick={() => handlePlaySegment(observation)}
                style={{ cursor: 'pointer' }}
              >
                <TableCell>
                  <div className="flex flex-col">
                    <span className="font-medium">
                      {observation.obs_dt ? new Date(observation.obs_dt).toLocaleTimeString() : 'N/A'}
                    </span>
                    <span className="text-sm text-gray-500">
                      {observation.extra_data.start_time ? `Start: ${formatTime(observation.extra_data.start_time)}` : ''}
                    </span>
                  </div>
                </TableCell>
                <TableCell>
                  <span className="font-medium">
                    {observation.extra_data.duration ? formatTime(observation.extra_data.duration) : 'N/A'}
                  </span>
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
                  <Badge 
                    className={getSourceBadgeStyle(
                      observation.source, 
                      observation.extra_data.auto_detected,
                      observation.extra_data.needs_review
                    )}
                  >
                    {observation.source}
                    {observation.extra_data.needs_review && (
                      <span className="ml-1 text-xs">(Review)</span>
                    )}
                  </Badge>
                </TableCell>
                <TableCell>
                  <div className="flex items-center gap-2">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={(e) => {
                        e.stopPropagation();
                        handlePlaySegment(observation);
                      }}
                      className={selectedObservation?.id === observation.id ? 'bg-blue-100' : ''}
                    >
                      {selectedObservation?.id === observation.id ? (
                        <Pause className="h-4 w-4" />
                      ) : (
                        <Play className="h-4 w-4" />
                      )}
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={(e) => {
                        e.stopPropagation();
                        onEdit(observation);
                      }}
                    >
                      <Edit2 className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={(e) => {
                        e.stopPropagation();
                        onDelete(observation.id);
                      }}
                      className="hover:bg-red-100 hover:text-red-600"
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </TableCell>
              </TableRow>
              {expandedObservation === observation.id && (
                <TableRow>
                  <TableCell colSpan={5} className="p-4 bg-gray-50">
                    <div className="rounded-lg overflow-hidden">
                      <AudioWaveformPlayer
                        deviceId={deviceId}
                        fileId={fileId}
                        fileFormat={fileFormat}
                        startTime={observation.extra_data.start_time}
                        endTime={observation.extra_data.end_time}
                        totalDuration={fileDuration}
                        className="bg-white"
                      />
                    </div>
                  </TableCell>
                </TableRow>
              )}
            </React.Fragment>
          ))}
        </TableBody>
      </Table>
    </div>
  );
} 