import { useState, useEffect } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { useContext } from 'react';
import AuthContext from "@/auth/AuthContext";

interface Observation {
  id: number;
  obs_dt: string;
  taxon: {
    species_name: string;
    species_common_name: string;
    id: number;
  };
  source: string;
  needs_review: boolean;
  extra_data: {
    start_time: number;
    end_time: number;
    duration: number;
    avg_amplitude: number;
    auto_detected: boolean;
  };
}

interface ObservationEditModalProps {
  observation: Observation | null;
  isOpen: boolean;
  onClose: () => void;
  onSave: (updatedObservation: Observation) => void;
}

export default function ObservationEditModal({
  observation,
  isOpen,
  onClose,
  onSave
}: ObservationEditModalProps) {
  const [editedObservation, setEditedObservation] = useState<Observation | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { authTokens } = useContext(AuthContext) as any;

  useEffect(() => {
    if (observation) {
      console.log('Original observation data:', observation);
      
      // Handle case where taxon is just an ID
      const taxon = typeof observation.taxon === 'number' 
        ? { id: observation.taxon, species_name: '', species_common_name: '' }
        : observation.taxon || { id: 0, species_name: '', species_common_name: '' };
      
      console.log('Initialized taxon data:', taxon);
      
      // Set needs_review to true for auto-detected observations
      const isAutoDetected = observation.source === 'auto_detect' || observation.extra_data?.auto_detected;
      const newObservation = {
        ...observation,
        taxon,
        needs_review: isAutoDetected ? true : observation.needs_review
      };
      console.log('Setting edited observation to:', newObservation);
      setEditedObservation(newObservation);
      setError(null);
    }
  }, [observation]);

  if (!editedObservation) return null;

  const handleSave = async () => {
    if (!editedObservation) return;
    setIsLoading(true);
    setError(null);

    try {
      console.log('Current edited observation:', editedObservation);
      console.log('Current taxon data:', editedObservation.taxon);
      
      // Handle both cases where taxon is an object or just an ID
      const taxonId = typeof editedObservation.taxon === 'number' 
        ? editedObservation.taxon 
        : editedObservation.taxon?.id;

      if (!taxonId) {
        console.error('Missing taxon ID:', editedObservation.taxon);
        throw new Error('A valid taxon ID is required to update the observation');
      }

      // Log the data we're sending
      const updateData = {
        taxon: taxonId,
        needs_review: editedObservation.needs_review,
        extra_data: {
          ...editedObservation.extra_data,
          needs_review: editedObservation.needs_review
        }
      };
      console.log('Updating observation with data:', updateData);

      const response = await fetch(`/api/observation/${editedObservation.id}/`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authTokens.access}`
        },
        body: JSON.stringify(updateData)
      });

      if (!response.ok) {
        let errorMessage = `Failed to update observation: ${response.status} ${response.statusText}`;
        
        // Read the response body only once
        const responseText = await response.text();
        console.error('Server error response:', responseText);
        
        try {
          // Try to parse as JSON if possible
          const errorData = JSON.parse(responseText);
          if (errorData.detail) {
            errorMessage = errorData.detail;
          } else if (errorData.message) {
            errorMessage = errorData.message;
          }
        } catch (e) {
          // If not JSON, check for specific error messages
          if (responseText.includes('ImproperlyConfigured') && responseText.includes('permission')) {
            errorMessage = 'Permission error: You do not have the required permissions to edit this observation.';
          } else if (!responseText.includes('<!DOCTYPE html>')) {
            errorMessage = responseText;
          }
        }

        throw new Error(errorMessage);
      }

      const updatedObservation = await response.json();
      console.log('Successfully updated observation:', updatedObservation);

      // Create a complete observation object with the taxon data
      const completeObservation = {
        ...updatedObservation,
        taxon: {
          id: taxonId,
          species_name: editedObservation.taxon.species_name,
          species_common_name: editedObservation.taxon.species_common_name
        }
      };
      
      onSave(completeObservation);
      onClose();
    } catch (error) {
      console.error('Error updating observation:', error);
      setError(error instanceof Error ? error.message : 'Unknown error occurred');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[600px]">
        <DialogHeader>
          <DialogTitle>Edit Observation</DialogTitle>
        </DialogHeader>
        <div className="grid gap-6 py-4">
          {error && (
            <div className="bg-red-50 border border-red-400 text-red-700 px-4 py-3 rounded relative">
              <span className="block sm:inline">{error}</span>
            </div>
          )}
          
          <div className="grid grid-cols-1 gap-4">
            <div className="p-4 bg-gray-50 rounded-lg">
              <h3 className="font-medium mb-2">Observation Details</h3>
              <div className="text-sm text-gray-600">
                <div>Time: {new Date(editedObservation.obs_dt).toLocaleString()}</div>
                <div>Source: {editedObservation.source}</div>
                <div>Duration: {editedObservation.extra_data.duration.toFixed(2)}s</div>
                <div>Amplitude: {editedObservation.extra_data.avg_amplitude.toFixed(4)}</div>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 gap-4">
            <div className="space-y-4">
              <div>
                <Label htmlFor="species_name">Species Name</Label>
                <Input
                  id="species_name"
                  value={editedObservation.taxon.species_name}
                  onChange={(e) =>
                    setEditedObservation({
                      ...editedObservation,
                      taxon: { ...editedObservation.taxon, species_name: e.target.value }
                    })
                  }
                  className="mt-1"
                />
              </div>
              <div>
                <Label htmlFor="common_name">Common Name</Label>
                <Input
                  id="common_name"
                  value={editedObservation.taxon.species_common_name}
                  onChange={(e) =>
                    setEditedObservation({
                      ...editedObservation,
                      taxon: { ...editedObservation.taxon, species_common_name: e.target.value }
                    })
                  }
                  className="mt-1"
                />
              </div>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label htmlFor="start_time">Start Time (s)</Label>
              <Input
                id="start_time"
                type="number"
                value={editedObservation.extra_data.start_time}
                onChange={(e) =>
                  setEditedObservation({
                    ...editedObservation,
                    extra_data: {
                      ...editedObservation.extra_data,
                      start_time: parseFloat(e.target.value)
                    }
                  })
                }
                className="mt-1"
              />
            </div>
            <div>
              <Label htmlFor="end_time">End Time (s)</Label>
              <Input
                id="end_time"
                type="number"
                value={editedObservation.extra_data.end_time}
                onChange={(e) =>
                  setEditedObservation({
                    ...editedObservation,
                    extra_data: {
                      ...editedObservation.extra_data,
                      end_time: parseFloat(e.target.value)
                    }
                  })
                }
                className="mt-1"
              />
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Switch
              id="needs_review"
              checked={editedObservation.needs_review}
              onCheckedChange={(checked) =>
                setEditedObservation({
                  ...editedObservation,
                  needs_review: checked
                })
              }
            />
            <Label htmlFor="needs_review">
              Needs Review
            </Label>
          </div>
        </div>
        <div className="flex justify-end gap-4">
          <Button variant="outline" onClick={onClose} disabled={isLoading}>
            Cancel
          </Button>
          <Button onClick={handleSave} disabled={isLoading}>
            {isLoading ? (
              <div className="flex items-center gap-2">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                <span>Saving...</span>
              </div>
            ) : (
              'Save Changes'
            )}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
} 