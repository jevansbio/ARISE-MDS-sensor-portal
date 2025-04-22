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

// Helper function to fetch date range
const fetchDateRange = async (token: string, site_name: string) => {
  const response = await getData(
    `datafile/date_range?site_name=${site_name}`,
    token
  );
  return response;
};

interface AuthContextType {
  user: {
    username: string;
    email: string;
  } | null;
  authTokens: {
    access: string;
    refresh: string;
  } | null;
  loginUser: (username: string, password: string) => Promise<void>;
  logoutUser: () => void;
}

interface DatafileProps {
  filteredDatafiles: (data: DataFile[]) => void;
  site_name: string;
}

const DateForm: React.FC<DatafileProps> = ({
  filteredDatafiles,
  site_name,
}) => {
  const authContext = useContext(AuthContext) as AuthContextType;
  const { authTokens } = authContext || { authTokens: null };
  
  // Query to get the date range
  const { data: dateRange } = useQuery({
    queryKey: ["dateRange", site_name],
    queryFn: () => {
      if (!authTokens?.access) {
        throw new Error('No access token available');
      }
      return fetchDateRange(authTokens.access, site_name);
    },
    enabled: !!authTokens?.access,
  });

  // State to store the start and end dates with default values from the system
  const [startDate, setStartDate] = useState<Date | undefined>(undefined);
  const [endDate, setEndDate] = useState<Date | undefined>(undefined);

  // Set default dates when dateRange is available
  useEffect(() => {
    if (dateRange?.first_date && dateRange?.last_date) {
      setStartDate(new Date(dateRange.first_date));
      setEndDate(new Date(dateRange.last_date));
    }
  }, [dateRange]);

  // TanStack Query: useQuery hook to fetch data based on the selected dates
  const { data, error, isLoading, isError } = useQuery<DataFile[]>({
    queryKey: ["datafile", startDate, endDate],
    queryFn: () => {
      if (startDate && endDate && authTokens?.access) {
        return fetchDataForDateRange(
          startDate,
          endDate,
          authTokens.access,
          site_name
        );
      }
      return Promise.resolve(null);
    },
    enabled: !!startDate && !!endDate && !!authTokens?.access,
  });

  useEffect(() => {
    if (data) {
      filteredDatafiles(data);
    }
  }, [data, filteredDatafiles]);

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
        <div className="text-gray-500 mt-2">
          Pick a timeframe to get datafiles from.
        </div>
      )}
    </div>
  );
};

export default DateForm;
