import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { DataFile } from "@/types";
import { Button } from "@/components/ui/button";
import {
  type ColumnDef,
  flexRender,
  getCoreRowModel,
  getSortedRowModel,
  type SortingState,
  useReactTable,
} from "@tanstack/react-table";
import { TbArrowsUpDown } from "react-icons/tb";
import { Link } from "@tanstack/react-router";
import { Route } from ".";
import { useContext, useState } from "react";
import AuthContext from "@/auth/AuthContext";
import DownloadButton from "@/components/DownloadButton/DownloadButton";
import AudioPlayer from "@/components/AudioPlayer/AudioPlayer";
import { bytesToMegabytes } from "@/utils/convertion";
import DateForm from "@/components/AudioQuality/DateForm";

export default function DeviceDataFilesPage() {
  const { siteName: site_name } = Route.useParams();
  const authContext = useContext(AuthContext) as { authTokens: { access: string } | null };
  const { authTokens } = authContext || { authTokens: null };
  const [FilteredDataFiles, setFilteredDataFiles] = useState<DataFile[]>([]);
  const [sorting, setSorting] = useState<SortingState>([]);

  const columns: ColumnDef<DataFile>[] = [
    {
      accessorKey: "id",
      header: ({ column }) => (
        <Button
          variant="ghost"
          onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
          className="w-full justify-start"
        >
          ID
          <TbArrowsUpDown className="ml-2 h-4 w-4" />
        </Button>
      ),
      cell: ({ row }) => (
        <Link
          to="/deployments/$site_name/$dataFileId"
          params={{ site_name: site_name, dataFileId: row.original.id }}
          className="text-blue-500 hover:underline"
        >
          {row.original.id}
        </Link>
      ),
    },
    {
      accessorKey: "fileName",
      header: "File Name",
      cell: ({ row }) => row.original.file_name,
    },
    {
      accessorKey: "sample_rate",
      header: ({ column }) => (
        <Button
          variant="ghost"
          onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
          className="w-full justify-start"
        >
          Sample Rate
          <TbArrowsUpDown className="ml-2 h-4 w-4" />
        </Button>
      ),
      cell: ({ row }) =>
        row.original.sample_rate ? `${row.original.sample_rate} Hz` : "-",
    },
    {
      accessorKey: "file_length",
      header: ({ column }) => (
        <Button
          variant="ghost"
          onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
          className="w-full justify-start"
        >
          File Length
          <TbArrowsUpDown className="ml-2 h-4 w-4" />
        </Button>
      ),
      cell: ({ row }) => {
        return row.original.file_length ? `${row.original.file_length}` : "-";
      },
    },
    {
      accessorKey: "file_size",
      header: ({ column }) => (
        <Button
          variant="ghost"
          onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
          className="w-full justify-start"
        >
          File Size (MB)
          <TbArrowsUpDown className="ml-2 h-4 w-4" />
        </Button>
      ),
      cell: ({ row }) => {
        const fileSize = row.original.file_size;
        return `${bytesToMegabytes(fileSize)} MB`;
      },
    },
    {
      accessorKey: "file_format",
      header: ({ column }) => (
        <Button
          variant="ghost"
          onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
          className="w-full justify-start"
        >
          File format
          <TbArrowsUpDown className="ml-2 h-4 w-4" />
        </Button>
      ),
      cell: ({ row }) => row.original.file_format,
    },
    {
      accessorKey: "quality_score",
      header: ({ column }) => (
        <Button
          variant="ghost"
          onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
          className="w-full justify-start"
        >
          Quality Score
          <TbArrowsUpDown className="ml-2 h-4 w-4" />
        </Button>
      ),
      cell: ({ row }) =>
        row.original.quality_score ? `${row.original.quality_score}/100` : "-",
    },
    {
      id: "actions",
      header: "Actions",
      cell: ({ row }) => (
        <div className="flex items-center gap-2">
          <AudioPlayer
            fileId={row.original.id.toString()}
            fileFormat={row.original.file_format}
          />
          <DownloadButton
            fileId={row.original.id.toString()}
            fileFormat={row.original.file_format}
          />
        </div>
      ),
    },
  ];

  const table = useReactTable({
    data: FilteredDataFiles,
    columns,
    state: { sorting },
    onSortingChange: setSorting,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
  });

  if (!authTokens) {
    return <p>Loading authentication...</p>;
  }

  const handleBulkQualityCheck = async () => {
    if (!authTokens?.access) return;

    try {
      // Get the deployment ID from the first data file
      const deploymentId = FilteredDataFiles[0]?.deployment;
      if (!deploymentId) {
        alert("No deployment found for this device");
        return;
      }

      // Call the bulk quality check endpoint
      const response = await fetch(
        `/api/deployment/${deploymentId}/check_quality_bulk/`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${authTokens.access}`,
          },
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(
          errorData.error || "Failed to start bulk quality check"
        );
      }

      const result = await response.json();
      alert(`Started quality check for ${result.total_files} files`);

      // Refetch data after a short delay to show updated status
      setTimeout(() => {}, 2000);
    } catch (error: unknown) {
      console.error("Error starting bulk quality check:", error);
      const errorMessage = error instanceof Error ? error.message : "Failed to start bulk quality check. Please try again.";
      alert(errorMessage);
    }
  };

  // Function to handle data received from DateForm
  const handleDataFromDateForm = (newData: DataFile[]) => {
    setFilteredDataFiles(newData); // Update the dataFiles state with the new data
  };

  return (
    <div className="container mx-auto py-10">
      {FilteredDataFiles.length > 0 && (
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-2xl font-bold pl-5">Data Files</h1>
          <Button
            onClick={handleBulkQualityCheck}
            className="bg-blue-500 text-white hover:bg-blue-600"
          >
            Check Quality for All Audio Files
          </Button>
        </div>
      )}

      <DateForm
        filteredDatafiles={handleDataFromDateForm}
        site_name={site_name}
      />

      {FilteredDataFiles.length > 0 && (
        <div className="rounded-md border m-5 shadow-md">
          <Table>
            <TableHeader>
              {table.getHeaderGroups().map((headerGroup) => (
                <TableRow key={headerGroup.id}>
                  {headerGroup.headers.map((header) => (
                    <TableHead key={header.id} className="px-0 py-0">
                      {header.isPlaceholder
                        ? null
                        : flexRender(
                            header.column.columnDef.header,
                            header.getContext()
                          )}
                    </TableHead>
                  ))}
                </TableRow>
              ))}
            </TableHeader>
            <TableBody>
              {table.getRowModel().rows.map((row) => (
                <TableRow key={row.id}>
                  {row.getVisibleCells().map((cell) => (
                    <TableCell key={cell.id} className="px-4 py-2">
                      {flexRender(
                        cell.column.columnDef.cell,
                        cell.getContext()
                      )}
                    </TableCell>
                  ))}
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      )}
    </div>
  );
}
