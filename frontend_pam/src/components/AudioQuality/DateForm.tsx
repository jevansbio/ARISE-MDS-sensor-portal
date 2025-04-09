import { useContext, useEffect, useState } from "react";
import { DatePicker } from "../ui/DatePicker";
import { useQuery } from "@tanstack/react-query";
import AuthContext from "@/auth/AuthContext";
import { getData } from "@/utils/FetchFunctions";
import { DataFile } from "@/types";

// Helper function to format dates as MM-DD-YYYY
const formatDate = (date: Date) => {
  const month = `0${date.getMonth() + 1}`.slice(-2);
  const day = `0${date.getDate()}`.slice(-2);
  const year = date.getFullYear();
  return `${month}-${day}-${year}`;
};

// Helper function to fetch data
const fetchDataForDateRange = async (
  startDate: Date,
  endDate: Date,
  token: string,
  site_name: string
) => {
  const formattedStartDate = formatDate(startDate);
  const formattedEndDate = formatDate(endDate);

  // Using the provided getData function
  const response = await getData(
    `datafile/filter_by_date?start_date=${formattedStartDate}&end_date=${formattedEndDate}&site_name=${site_name}`,
    token
  );
  return response; // The response is already in JSON format
};

interface AuthContextType {
  user: any;
  authTokens: any;
  loginUser: (e: React.FormEvent) => void;
  logoutUser: (e?: React.FormEvent) => void;
  useAuth: () => AuthContextType;
}

interface DatafileProps {
  filteredDatafiles: (data: DataFile[]) => void; // Change to expect an array of DataFile
  site_name: string;
}

const DateForm: React.FC<DatafileProps> = ({
  filteredDatafiles,
  site_name,
}) => {
  // State to store the start and end dates
  const [startDate, setStartDate] = useState<Date | undefined>(undefined);
  const [endDate, setEndDate] = useState<Date | undefined>(undefined);

  const { authTokens } = useContext(AuthContext) as AuthContextType;

  // TanStack Query: useQuery hook to fetch data based on the selected dates
  const { data, error, isLoading, isError } = useQuery<DataFile[]>({
    queryKey: ["datafile", startDate, endDate], // Query key with the date range
    queryFn: () => {
      if (startDate && endDate && authTokens?.access) {
        return fetchDataForDateRange(
          startDate,
          endDate,
          authTokens.access,
          site_name
        );
      }
      return Promise.resolve(null); // Return null or empty response if dates are not selected or token is missing
    },
    enabled: !!startDate && !!endDate && !!authTokens?.access, // Only run the query if both dates and token are available
  });

  useEffect(() => {
    if (data) {
      filteredDatafiles(data); // Send the fetched data to the parent component
    }
  }, [data, filteredDatafiles]); // Run the effect whenever `data` or `filteredDatafiles` changes

  return (
    <div className="flex space-x-4 items-center pl-5">
      {/* Start Date Picker */}
      <DatePicker
        value={startDate}
        onChange={setStartDate}
        label="Pick start date"
      />
      <br />

      {/* End Date Picker */}
      <DatePicker value={endDate} onChange={setEndDate} label="Pick end date" />
      <br />

      {/* Error Message */}
      {isError && (
        <div className="text-red-500 mt-2">{(error as Error).message}</div>
      )}

      {/* Success Message */}
      {data && !isError && !isLoading && (
        <div className="text-green-500 mt-2">Data fetched successfully!</div>
      )}

      {/* Optional: You can add a fallback component or message to render when nothing is available */}
      {!data && !isLoading && !isError && (
        <div className="text-gray-500 mt-2">No data available yet.</div>
      )}
    </div>
  );
};

export default DateForm;
