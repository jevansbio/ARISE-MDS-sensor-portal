import { useForm } from "@tanstack/react-form";

interface DeviceFormProps {
  onSave: () => void;
}

function DeviceForm({ onSave }: DeviceFormProps) {
  const form = useForm({
    defaultValues: {
      country: "",
      site: "",
      date: "",
      time: "",
      latitude: "",
      longitude: "",
      coordUncertainty: "",
      gpsDevice: "",
      deviceId: "",
      deploymentId: "",
      micHeight: "",
      micDirection: "",
      habitat: "",
      score: "",
      protocolChecklist: "",
      email: "",
      comment: "",
    },
    onSubmit: async (values) => {
      console.log(values);
      if (onSave) {
         onSave(); 
      }
   },
  });

  const fieldsConfig = [
    { name: "country", label: "Country", type: "text" },
    { name: "site", label: "Site", type: "text" },
    { name: "date", label: "Date", type: "date" },
    { name: "time", label: "Time (UTC)", type: "time" },
    { name: "latitude", label: "Latitude", type: "text" },
    { name: "longitude", label: "Longitude", type: "text" },
    {
      name: "coordUncertainty",
      label: "Coordinate Uncertainty",
      type: "number",
    },
    { name: "gpsDevice", label: "GPS device", type: "text" },
    { name: "deviceId", label: "Device ID", type: "text" },
    { name: "deploymentId", label: "Deployment ID", type: "text" },
    { name: "micHeight", label: "Microphone Height", type: "number" },
    { name: "micDirection", label: "Microphone Direction", type: "text" },
    { name: "habitat", label: "Habitat", type: "text" },
    { name: "score", label: "Score", type: "number" },
    { name: "protocolChecklist", label: "Protocol Checklist", type: "text" },
    { name: "email", label: "Adresse e-mail", type: "email" },
    { name: "comment", label: "Comment", type: "text" },
  ] as const;

  return (
    <form
      onSubmit={form.handleSubmit}
    >
    
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "1fr 1fr",
          gap: "1rem",
          marginBottom: "1rem",
        }}
      >
        {fieldsConfig.map((fieldConfig) => (
          <form.Field
            key={fieldConfig.name}
            name={fieldConfig.name}
            children={(field) => (
              <div
                className={`flex flex-col my-2 ${fieldConfig.name === "comment" ? "col-span-2" : ""} text-sm md:text-base lg:text-lg`}
              >
                <label htmlFor={fieldConfig.name}>{fieldConfig.label}:</label>
                <input
                  className={`border border-gray-300 rounded w-full p-2`}
                  id={fieldConfig.name}
                  type={fieldConfig.type}
                  value={field.state.value}
                  onChange={(e) => {
                    let value = e.target.value;
                    if (
                      fieldConfig.name === "latitude" ||
                      fieldConfig.name === "longitude"
                    ) {
                      value = value.replace(/,/g, ".");
                      const regex = /^\d*\.?\d{0,5}$/;
                      if (!regex.test(value)) return;
                    }

                    field.handleChange(value);
                  }}
                />
              </div>
            )}
          />
        ))}
      </div>

      
     
    <div className="text-center mt-6">
      <button type="submit" className="bg-green-900 text-white py-2 px-8 rounded-lg hover:bg-green-700 transition-all block mx-auto w-80">
          Save
      </button>
    </div>

    </form>
     
  );
}

export default DeviceForm;


