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
  deviceStatus: z.string().optional(),
  configuration: z.enum(["summer", "winter"]).optional(),
  simCardIcc: z.string().optional(),
  simCardBatch: z.string().optional(),
  sdCardSize: z.number().positive().optional(),
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
          <Label htmlFor="deviceStatus">Device Status</Label>
          <Input
            id="deviceStatus"
            placeholder="Enter device status"
            {...register("deviceStatus")}
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="configuration">Configuration</Label>
          <select
            id="configuration"
            className="w-full p-2 border rounded"
            {...register("configuration")}
          >
            <option value="">Select configuration</option>
            <option value="summer">Summer</option>
            <option value="winter">Winter</option>
          </select>
        </div>

        <div className="space-y-2">
          <Label htmlFor="simCardIcc">SIM Card ICC</Label>
          <Input
            id="simCardIcc"
            placeholder="Enter SIM card ICC"
            {...register("simCardIcc")}
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="simCardBatch">SIM Card Batch</Label>
          <Input
            id="simCardBatch"
            placeholder="Enter SIM card batch"
            {...register("simCardBatch")}
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="sdCardSize">SD Card Size (GB)</Label>
          <Input
            id="sdCardSize"
            type="number"
            placeholder="Enter SD card size in GB"
            {...register("sdCardSize", { valueAsNumber: true })}
          />
        </div>
      </div>

      <Button type="submit">Create Device</Button>
    </form>
  );
}