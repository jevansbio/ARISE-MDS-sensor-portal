import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import AuthContext from "@/auth/AuthContext";
import { postData } from "@/utils/FetchFunctions";
import { useContext } from "react";

const formSchema = z.object({
  deviceId: z.string().optional(),
  country: z.string().optional(),
  site: z.string().optional(),
  date: z.string().optional(),
  time: z.string().optional(),
  latitude: z
    .string()
    .regex(
      /^-?\d{1,2}\.\d{6}$/,
      "Latitude must have 1–2 digits before the dot and exactly 6 decimal places (e.g. 45.123456)"
    )
    .optional(),
  longitude: z
    .string()
    .regex(
      /^-?\d{1,3}\.\d{6}$/,
      "Longitude must have 1–3 digits before the dot and exactly 6 decimal places (e.g. 123.123456)"
    )
    .optional(),
  coordUncertainty: z.string().optional(),
  gpsDevice: z.string().optional(),
  deploymentId: z.string().optional(),
  micHeight: z.string().optional(),
  micDirection: z.string().optional(),
  habitat: z.string().optional(),
  score: z.string().optional(),
  protocolChecklist: z.string().optional(),
  email: z.string().optional(),
  comment: z.string().optional(),
  simCardICC: z.string().optional(),
  simCardBatch: z.string().optional(),
  sdCardSize: z.string().optional(),
  configuration: z.string().optional(),
});

type FormValues = z.infer<typeof formSchema>;

interface DeviceFormProps {
  onSave: () => void;
}

export default function DeviceForm({ onSave }: DeviceFormProps) {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(formSchema),
  });

  const authContext = useContext(AuthContext) as {
    authTokens: { access: string } | null;
  };
  const token = authContext?.authTokens?.access;

  const onSubmit = async (values: FormValues) => {
    try {
      if (!token) {
        throw new Error("Authentication token is missing");
      }

      const devicePayload = {
        device_ID: values.deviceId,
        configuration: values.configuration,
        sim_card_icc: values.simCardICC,
        sim_card_batch: values.simCardBatch,
        sd_card_size: values.sdCardSize,
      };

      const deploymentPayload = {
        deployment_ID: values.deploymentId,
        start_date: values.date,
        end_date: "",
        lastUpload: "",
        folder_size: 0,
        country: values.country,
        site_name: values.site,
        latitude: values.latitude,
        longitude: values.longitude,
        coordinate_uncertainty: values.coordUncertainty,
        gps_device: values.gpsDevice,
        mic_height: values.micHeight,
        mic_direction: values.micDirection,
        habitat: values.habitat,
        score: values.score,
        protocol_checklist: values.protocolChecklist,
        user_email: values.email,
        comment: values.comment,
      };

      console.log("Device payload:", devicePayload);
      console.log("Deployment payload:", deploymentPayload);

      const deviceUrl = `devices/upsert_device/`;
      const deviceResponse = await postData(deviceUrl, token, devicePayload);
      console.log("Device response:", deviceResponse);

      const deploymentUrl = `deployment/upsert_deployment/`;
      const deploymentResponse = await postData(
        deploymentUrl,
        token,
        deploymentPayload
      );
      console.log("Deployment response:", deploymentResponse);

      if (!deviceResponse.ok || !deploymentResponse.ok) {
        throw new Error("Failed to update device or deployment info");
      }

      onSave();
    } catch (error) {
      console.error("Error updating info:", error);
    }
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-8">
      <div className="grid grid-cols-2 gap-8">
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
            <Label htmlFor="deploymentId">Deployment ID</Label>
            <Input
              id="deploymentId"
              placeholder="Enter deployment ID"
              {...register("deploymentId")}
            />
            {errors.deploymentId && (
              <p className="text-sm text-red-500">
                {errors.deploymentId.message}
              </p>
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
            <Label htmlFor="site">Site</Label>
            <Input id="site" placeholder="Enter site" {...register("site")} />
            {errors.site && (
              <p className="text-sm text-red-500">{errors.site.message}</p>
            )}
          </div>
          <div className="space-y-2">
            <Label htmlFor="date">Date</Label>
            <Input
              id="date"
              placeholder="Enter date"
              type="date"
              {...register("date")}
            />
            {errors.date && (
              <p className="text-sm text-red-500">{errors.date.message}</p>
            )}
          </div>
          <div className="space-y-2">
            <Label htmlFor="time">Time (UTC)</Label>
            <Input
              id="time"
              placeholder="Enter time"
              type="time"
              {...register("time")}
            />
            {errors.time && (
              <p className="text-sm text-red-500">{errors.time.message}</p>
            )}
          </div>
          <div className="space-y-2">
            <Label htmlFor="latitude">Latitude</Label>
            <Input
              id="latitude"
              placeholder="Enter latitude"
              type="text"
              {...register("latitude")}
            />
            {errors.latitude && (
              <p className="text-sm text-red-500">{errors.latitude.message}</p>
            )}
          </div>
          <div className="space-y-2">
            <Label htmlFor="longitude">Longitude</Label>
            <Input
              id="longitude"
              placeholder="Enter longitude"
              type="text"
              {...register("longitude")}
            />
            {errors.longitude && (
              <p className="text-sm text-red-500">{errors.longitude.message}</p>
            )}
          </div>
          <div className="space-y-2">
            <Label htmlFor="coordUncertainty">Coordinate Uncertainty</Label>
            <Input
              id="coordUncertainty"
              placeholder="Enter coordinate uncertainty"
              type="number"
              {...register("coordUncertainty")}
            />
            {errors.coordUncertainty && (
              <p className="text-sm text-red-500">
                {errors.coordUncertainty.message}
              </p>
            )}
          </div>
          <div className="space-y-2">
            <Label htmlFor="gpsDevice">GPS Device</Label>
            <Input
              id="gpsDevice"
              placeholder="Enter GPS device"
              {...register("gpsDevice")}
            />
            {errors.gpsDevice && (
              <p className="text-sm text-red-500">{errors.gpsDevice.message}</p>
            )}
          </div>
        </div>

        <div className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="micHeight">Microphone Height</Label>
            <Input
              id="micHeight"
              placeholder="Enter microphone height"
              type="number"
              {...register("micHeight")}
            />
            {errors.micHeight && (
              <p className="text-sm text-red-500">{errors.micHeight.message}</p>
            )}
          </div>
          <div className="space-y-2">
            <Label htmlFor="micDirection">Microphone Direction</Label>
            <Input
              id="micDirection"
              placeholder="Enter microphone direction"
              {...register("micDirection")}
            />
            {errors.micDirection && (
              <p className="text-sm text-red-500">
                {errors.micDirection.message}
              </p>
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
          <div className="space-y-2">
            <Label htmlFor="score">Score</Label>
            <Input
              id="score"
              placeholder="Enter score"
              type="number"
              {...register("score")}
            />
            {errors.score && (
              <p className="text-sm text-red-500">{errors.score.message}</p>
            )}
          </div>
          <div className="space-y-2">
            <Label htmlFor="protocolChecklist">Protocol Checklist</Label>
            <Input
              id="protocolChecklist"
              placeholder="Enter protocol checklist"
              {...register("protocolChecklist")}
            />
            {errors.protocolChecklist && (
              <p className="text-sm text-red-500">
                {errors.protocolChecklist.message}
              </p>
            )}
          </div>
          <div className="space-y-2">
            <Label htmlFor="email">Email</Label>
            <Input
              id="email"
              placeholder="Enter email"
              type="email"
              {...register("email")}
            />
            {errors.email && (
              <p className="text-sm text-red-500">{errors.email.message}</p>
            )}
          </div>
          <div className="space-y-2">
            <Label htmlFor="simCardICC">Sim Card ICC</Label>
            <Input
              id="simCardICC"
              placeholder="Enter Sim Card ICC"
              {...register("simCardICC")}
            />
            {errors.simCardICC && (
              <p className="text-sm text-red-500">
                {errors.simCardICC.message}
              </p>
            )}
          </div>
          <div className="space-y-2">
            <Label htmlFor="simCardBatch">SIM Card Batch</Label>
            <Input
              id="simCardBatch"
              placeholder="Enter SIM Card Batch"
              {...register("simCardBatch")}
            />
            {errors.simCardBatch && (
              <p className="text-sm text-red-500">
                {errors.simCardBatch.message}
              </p>
            )}
          </div>
          <div className="space-y-2">
            <Label htmlFor="sdCardSize">SD Card Size (GB)</Label>
            <Input
              id="sdCardSize"
              placeholder="Enter SD Card Size"
              type="number"
              {...register("sdCardSize")}
            />
            {errors.sdCardSize && (
              <p className="text-sm text-red-500">
                {errors.sdCardSize.message}
              </p>
            )}
          </div>
          <div className="space-y-2">
            <Label htmlFor="configuration">Configuration</Label>
            <Input
              id="configuration"
              placeholder="Enter configuration"
              {...register("configuration")}
            />
            {errors.configuration && (
              <p className="text-sm text-red-500">
                {errors.configuration.message}
              </p>
            )}
          </div>
        </div>
      </div>

      <div className="space-y-2">
        <Label htmlFor="comment">Comment</Label>
        <Input
          id="comment"
          placeholder="Enter comment"
          {...register("comment")}
        />
        {errors.comment && (
          <p className="text-sm text-red-500">{errors.comment.message}</p>
        )}
      </div>

      <div className="flex justify-center mt-8">
        <Button type="submit">Submit</Button>
      </div>
    </form>
  );
}
