import { useState, useEffect, FormEvent } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { useContext } from 'react';
import AuthContext from "@/auth/AuthContext";
import { type Observation } from '@/types';

interface AuthContextType {
  authTokens: {
    access: string;
    refresh: string;
  } | null;
  user: {
    username: string;
    email: string;
  } | null;
  loginUser: (e: FormEvent<HTMLFormElement>) => Promise<void>;
  logoutUser: () => void;
  refreshToken: () => Promise<void>;
}

interface ObservationEditModalProps {
  isOpen: boolean;
  onClose: () => void;
  observation: Observation;
  onSave: (updatedObservation: Observation) => void;
}

export default function ObservationEditModal({ isOpen, onClose, observation, onSave }: ObservationEditModalProps) {
  const [editedObservation, setEditedObservation] = useState<Observation>(observation);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { authTokens } = useContext(AuthContext) as AuthContextType;

  useEffect(() => {
    setEditedObservation(observation);
  }, [observation]);

  const handleSave = async () => {
    if (!authTokens) {
      setError('Not authenticated');
      return;
    }
    console.log('=== Starting handleSave in ObservationEditModal ===');
    console.log('Current edited observation:', editedObservation);
    console.log('Current taxon data:', editedObservation.taxon);

    if (!editedObservation) {
      setError('Missing required data for save');
      return;
    }

    if (!editedObservation.taxon?.species_name) {
      setError('Species name is required');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      // Prepare the update data with taxon information
      const updateData = {
        taxon: {
          id: editedObservation.taxon.id,
          species_name: editedObservation.taxon.species_name,
          species_common_name: editedObservation.taxon.species_common_name || ''
        },
        needs_review: editedObservation.needs_review,
        extra_data: {
          start_time: Number(editedObservation.extra_data.start_time),
          end_time: Number(editedObservation.extra_data.end_time),
          duration: Number(editedObservation.extra_data.duration),
          avg_amplitude: Number(editedObservation.extra_data.avg_amplitude),
          auto_detected: Boolean(editedObservation.extra_data.auto_detected)
        },
        data_files: observation.data_files // Preserve the original data_files
      };

      console.log('Preparing to send update data:', JSON.stringify(updateData, null, 2));
      console.log('API endpoint:', `observation/${editedObservation.id}/`);

      // Send the update to the backend
      const response = await fetch(`/api/observation/${editedObservation.id}/`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authTokens.access}`
        },
        body: JSON.stringify(updateData)
      });

      if (!response.ok) {
        let errorMessage = 'Failed to update observation';
        try {
          const contentType = response.headers.get('content-type');
          if (contentType && contentType.includes('application/json')) {
            const errorData = await response.json();
            errorMessage = errorData.detail || errorMessage;
          } else {
            if (response.status === 500) {
              errorMessage = 'Server error occurred. Please try again later.';
            } else {
              errorMessage = `Server returned status ${response.status}. Please try again.`;
            }
          }
        } catch (e) {
          console.error('Error parsing error response:', e);
        }
        throw new Error(errorMessage);
      }

      const updatedObservation = await response.json();
      console.log('Server returned updated observation:', updatedObservation);
      console.log('Taxon data in response:', updatedObservation.taxon);

      // Create a complete observation object with the taxon data
      const completeObservation = {
        ...updatedObservation,
        taxon: {
          id: updatedObservation.taxon.id,
          species_name: updatedObservation.taxon.species_name,
          species_common_name: updatedObservation.taxon.species_common_name || ''
        }
      };

      console.log('Complete observation with taxon:', completeObservation);
      console.log('Taxon details:', {
        id: completeObservation.taxon.id,
        species_name: completeObservation.taxon.species_name,
        species_common_name: completeObservation.taxon.species_common_name
      });

      console.log('Calling onSave with complete observation:', completeObservation);
      onSave(completeObservation);
      onClose();
      console.log('=== handleSave completed successfully ===');
    } catch (error) {
      console.error('Error saving observation:', error);
      setError(error instanceof Error ? error.message : 'Failed to save observation');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>Edit Observation</DialogTitle>
          <DialogDescription>
            Update the observation details below.
          </DialogDescription>
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