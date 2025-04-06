import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

const formSchema = z.object({
  deployment_ID: z.string().min(1, "Deployment ID is required"),
  device_ID: z.string().min(1, "Device ID is required"),
  deployment_start: z.string().min(1, "Start date is required"),
  deployment_end: z.string().optional(),
  country: z.string().min(1, "Country is required"),
  site_name: z.string().min(1, "Site name is required"),
  latitude: z.number().min(-90).max(90).optional(),
  longitude: z.number().min(-180).max(180).optional(),
  coordinate_uncertainty: z.string().optional(),
  gps_device: z.string().optional(),
  mic_height: z.number().positive().optional(),
  mic_direction: z.string().optional(),
  habitat: z.string().min(1, "Habitat is required"),
  score: z.number().min(0).max(100).optional(),
  protocol_checklist: z.string().optional(),
  user_email: z.string().email().optional(),
  comment: z.string().optional(),
});

type FormValues = z.infer<typeof formSchema>;

export default function DeploymentForm() {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(formSchema),
  });

  const onSubmit = async (values: FormValues) => {
    try {
      const response = await fetch("/api/deployments/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(values),
      });

      if (!response.ok) {
        throw new Error("Failed to create deployment");
      }

      // Handle success (e.g., show a success message, redirect, etc.)
    } catch (error) {
      console.error("Error creating deployment:", error);
      // Handle error (e.g., show an error message)
    }
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-8">
      <div className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="deployment_ID">Deployment ID</Label>
          <Input
            id="deployment_ID"
            placeholder="Enter deployment ID"
            {...register("deployment_ID")}
          />
          {errors.deployment_ID && (
            <p className="text-sm text-red-500">{errors.deployment_ID.message}</p>
          )}
        </div>

        <div className="space-y-2">
          <Label htmlFor="device_ID">Device ID</Label>
          <Input
            id="device_ID"
            placeholder="Enter device ID"
            {...register("device_ID")}
          />
          {errors.device_ID && (
            <p className="text-sm text-red-500">{errors.device_ID.message}</p>
          )}
        </div>

        <div className="space-y-2">
          <Label htmlFor="deployment_start">Start Date</Label>
          <Input
            id="deployment_start"
            type="datetime-local"
            {...register("deployment_start")}
          />
          {errors.deployment_start && (
            <p className="text-sm text-red-500">{errors.deployment_start.message}</p>
          )}
        </div>

        <div className="space-y-2">
          <Label htmlFor="deployment_end">End Date</Label>
          <Input
            id="deployment_end"
            type="datetime-local"
            {...register("deployment_end")}
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="country">Country</Label>
          <Input
            id="country"
            placeholder="Enter country"
            {...register("country")}
          />
          {errors.country && (
            <p className="text-sm text-red-500">{errors.country.message}</p>
          )}
        </div>

        <div className="space-y-2">
          <Label htmlFor="site_name">Site Name</Label>
          <Input
            id="site_name"
            placeholder="Enter site name"
            {...register("site_name")}
          />
          {errors.site_name && (
            <p className="text-sm text-red-500">{errors.site_name.message}</p>
          )}
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="latitude">Latitude</Label>
            <Input
              id="latitude"
              type="number"
              step="any"
              placeholder="Enter latitude"
              {...register("latitude", { valueAsNumber: true })}
            />
            {errors.latitude && (
              <p className="text-sm text-red-500">{errors.latitude.message}</p>
            )}
          </div>

          <div className="space-y-2">
            <Label htmlFor="longitude">Longitude</Label>
            <Input
              id="longitude"
              type="number"
              step="any"
              placeholder="Enter longitude"
              {...register("longitude", { valueAsNumber: true })}
            />
            {errors.longitude && (
              <p className="text-sm text-red-500">{errors.longitude.message}</p>
            )}
          </div>
        </div>

        <div className="space-y-2">
          <Label htmlFor="coordinate_uncertainty">Coordinate Uncertainty</Label>
          <Input
            id="coordinate_uncertainty"
            placeholder="Enter coordinate uncertainty"
            {...register("coordinate_uncertainty")}
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="gps_device">GPS Device</Label>
          <Input
            id="gps_device"
            placeholder="Enter GPS device"
            {...register("gps_device")}
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="mic_height">Microphone Height (m)</Label>
          <Input
            id="mic_height"
            type="number"
            step="0.1"
            placeholder="Enter microphone height"
            {...register("mic_height", { valueAsNumber: true })}
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="mic_direction">Microphone Direction</Label>
          <Input
            id="mic_direction"
            placeholder="Enter microphone direction"
            {...register("mic_direction")}
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="habitat">Habitat</Label>
          <Input
            id="habitat"
            placeholder="Enter habitat"
            {...register("habitat")}
          />
          {errors.habitat && (
            <p className="text-sm text-red-500">{errors.habitat.message}</p>
          )}
        </div>

        <div className="space-y-2">
          <Label htmlFor="score">Score</Label>
          <Input
            id="score"
            type="number"
            min="0"
            max="100"
            placeholder="Enter score"
            {...register("score", { valueAsNumber: true })}
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="protocol_checklist">Protocol Checklist</Label>
          <Input
            id="protocol_checklist"
            placeholder="Enter protocol checklist"
            {...register("protocol_checklist")}
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="user_email">Email</Label>
          <Input
            id="user_email"
            type="email"
            placeholder="Enter email"
            {...register("user_email")}
          />
          {errors.user_email && (
            <p className="text-sm text-red-500">{errors.user_email.message}</p>
          )}
        </div>

        <div className="space-y-2">
          <Label htmlFor="comment">Comment</Label>
          <textarea
            id="comment"
            className="w-full p-2 border rounded"
            placeholder="Enter comment"
            {...register("comment")}
          />
        </div>
      </div>

      <Button type="submit">Create Deployment</Button>
    </form>
  );
} 