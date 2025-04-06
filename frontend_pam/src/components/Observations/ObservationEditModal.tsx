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
  const { authTokens } = useContext(AuthContext) as any;

  useEffect(() => {
    if (observation) {
      // Always set needs_review to true for auto-detected observations
      const defaultNeedsReview = observation.source === 'auto_detect' || observation.extra_data?.auto_detected;
      setEditedObservation({
        ...observation,
        needs_review: defaultNeedsReview
      });
    }
  }, [observation]);

  if (!editedObservation) return null;

  const handleSave = async () => {
    try {
      const response = await fetch(`/api/observation/${editedObservation.id}/`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authTokens.access}`
        },
        body: JSON.stringify({
          taxon: {
            species_name: editedObservation.taxon.species_name,
            species_common_name: editedObservation.taxon.species_common_name
          },
          needs_review: editedObservation.needs_review,
          extra_data: editedObservation.extra_data
        })
      });

      if (!response.ok) {
        throw new Error('Failed to update observation');
      }

      const updatedObservation = await response.json();
      onSave(updatedObservation);
      onClose();
    } catch (error) {
      console.error('Error updating observation:', error);
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[600px]">
        <DialogHeader>
          <DialogTitle>Edit Observation</DialogTitle>
        </DialogHeader>
        <div className="grid gap-6 py-4">
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
          <Button variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <Button onClick={handleSave}>Save Changes</Button>
        </div>
      </DialogContent>
    </Dialog>
  );
} 