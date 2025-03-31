import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

const formSchema = z.object({
  deviceId: z.string().min(1, "Device ID is required"),
  name: z.string().min(1, "Name is required"),
  model: z.string().min(1, "Model is required"),
  country: z.string().min(1, "Country is required"),
  siteName: z.string().min(1, "Site name is required"),
  habitat: z.string().min(1, "Habitat is required"),
});

type FormValues = z.infer<typeof formSchema>;

export default function DeviceForm() {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(formSchema),
  });

  const onSubmit = async (values: FormValues) => {
    try {
      const response = await fetch("/api/devices/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(values),
      });

      if (!response.ok) {
        throw new Error("Failed to create device");
      }

      // Handle success (e.g., show a success message, redirect, etc.)
    } catch (error) {
      console.error("Error creating device:", error);
      // Handle error (e.g., show an error message)
    }
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-8">
      <div className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="deviceId">Device ID</Label>
          <Input
            id="deviceId"
            placeholder="Enter device ID"
            {...register("deviceId")}
          />
          {errors.deviceId && (
            <p className="text-sm text-red-500">{errors.deviceId.message}</p>
          )}
        </div>

        <div className="space-y-2">
          <Label htmlFor="name">Name</Label>
          <Input
            id="name"
            placeholder="Enter device name"
            {...register("name")}
          />
          {errors.name && (
            <p className="text-sm text-red-500">{errors.name.message}</p>
          )}
        </div>

        <div className="space-y-2">
          <Label htmlFor="model">Model</Label>
          <Input
            id="model"
            placeholder="Enter device model"
            {...register("model")}
          />
          {errors.model && (
            <p className="text-sm text-red-500">{errors.model.message}</p>
          )}
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
          <Label htmlFor="siteName">Site Name</Label>
          <Input
            id="siteName"
            placeholder="Enter site name"
            {...register("siteName")}
          />
          {errors.siteName && (
            <p className="text-sm text-red-500">{errors.siteName.message}</p>
          )}
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
      </div>

      <Button type="submit">Create Device</Button>
    </form>
  );
}