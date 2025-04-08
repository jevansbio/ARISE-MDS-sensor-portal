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
import { useQuery } from "@tanstack/react-query";
import { Route } from ".";
import { useContext, useState } from "react";
import AuthContext from "@/auth/AuthContext";
import { getData } from "@/utils/FetchFunctions";
import DownloadButton from "@/components/DownloadButton/DownloadButton";
import AudioPlayer from "@/components/AudioPlayer/AudioPlayer";
import { bytesToMegabytes } from "@/utils/convertion";


export default function DeviceDataFilesPage() {
  const { siteName } = Route.useParams();

  const authContext = useContext(AuthContext) as any;
  const { authTokens } = authContext || { authTokens: null };

  if (!authTokens) {
    return <p>Loading authentication...</p>;
  }

  const apiURL = `devices/${siteName}/datafiles`;

  const getDataFunc = async (): Promise<DataFile[]> => {
    if (!authTokens?.access) return [];
    const response_json = await getData(apiURL, authTokens.access);
  
    const dataFiles: DataFile[] = response_json.map((dataFile: any):DataFile => ({
      id: dataFile.id,
      deployment: dataFile.deployment,
      fileName: dataFile.file_name,
      fileFormat: dataFile.file_format,
      fileSize: dataFile.file_size,
      fileType: dataFile.file_type,
      path: dataFile.path,
      localPath: dataFile.local_path,
      uploadDt: dataFile.upload_dt,
      recordingDt: dataFile.recording_dt,
      config: dataFile.config,
      sampleRate: dataFile.sample_rate,
      fileLength: dataFile.file_length,
      qualityScore: dataFile.quality_score,
      qualityIssues: dataFile.quality_issues || [],
      qualityCheckDt: dataFile.quality_check_dt,
      qualityCheckStatus: dataFile.quality_check_status,
      extraData: dataFile.extra_data,
      thumbUrl: dataFile.thumb_url,
      localStorage: dataFile.local_storage,
      archived: dataFile.archived,
      favourite: dataFile.is_favourite
    }));

    return dataFiles;
  };

  const {
    data: dataFiles = []
  } = useQuery({
    queryKey: [apiURL],
    queryFn: getDataFunc,
    enabled: !!authTokens?.access,
  });

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
          to="/deployments/$deviceId/$dataFileId"
          params={{ deviceId: deviceId, dataFileId: row.original.id }}
          className="text-blue-500 hover:underline"
        >
          {row.original.id}
        </Link>
      ),
    },
    {
      accessorKey: "fileName",
      header: "File Name",
    },
    {
      accessorKey: "config",
      header: "Config",
    },
    {
      accessorKey: "sampleRate",
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
      cell: ({ row }) => row.original.sampleRate ? `${row.original.sampleRate} Hz` : '-',
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
      cell: ({ row }) => `${bytesToMegabytes(row.original.fileSize)} MB`,   
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
      cell: ({ row }) => row.original.fileFormat,
    },
    {
      accessorKey: "qualityScore",
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
      cell: ({ row }) => row.original.qualityScore ? `${row.original.qualityScore}/100` : '-',
    },
    {
      id: "actions",
      header: "Actions",
      cell: ({ row }) => (
        <div className="flex items-center gap-2">
          <AudioPlayer
            deviceId={deviceId}
            fileId={row.original.id}
            fileFormat={row.original.fileFormat}
          />
          <DownloadButton
            deviceId={deviceId}
            fileId={row.original.id}
            fileFormat={row.original.fileFormat}
          />
        </div>
      ),
    },
  ];

  // Table state and instance for sorting and rendering
  const [sorting, setSorting] = useState<SortingState>([]);
  const table = useReactTable({
    data: dataFiles,
    columns,
    state: { sorting },
    onSortingChange: setSorting,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
  });

  return (
    <div className="container mx-auto py-10">
      <h1 className="text-2xl font-bold mb-6">Data Files</h1>
    
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
                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                  </TableCell>
                ))}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
