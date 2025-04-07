import { useContext, useState } from "react";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  type ColumnDef,
  flexRender,
  getCoreRowModel,
  getSortedRowModel,
  type SortingState,
  useReactTable,
} from "@tanstack/react-table";
import { TbArrowsUpDown } from "react-icons/tb";
import { Device } from "@/types";
import { useQuery } from "@tanstack/react-query";
import { Link } from "@tanstack/react-router";
import { Button } from "@/components/ui/button";
import AuthContext from "@/auth/AuthContext";
import { getData } from "@/utils/FetchFunctions";
import { bytesToMegabytes } from "@/utils/convertion";
import Modal from "@/components/Modal/Modal";
import DeviceForm from "@/components/DeviceForm";

export default function DeploymentsPage() {
  // const { data } = useSuspenseQuery(devicesQueryOptions);

  const authContext = useContext(AuthContext) as any;
  const { authTokens } = authContext || { authTokens: null };
  const apiURL = "devices/";

  const getDataFunc = async (): Promise<Device[]> => {
    if (!authTokens?.access) return [];
    const response_json = await getData(apiURL, authTokens.access);
  
    const devices: Device[] = response_json.map((device: any): Device => ({
      id: device.device_ID,
      startDate: device.start_date,
      endDate: device.end_date,
      folder_size: device.folder_size,
      lastUpload: "",
      batteryLevel: 0,
      action: "",
      site: device.site_name,
      dataFile: []
    }));
  
    return devices;
  };

  const { data = [] } = useQuery({
    queryKey: [apiURL],
    queryFn: getDataFunc,
    enabled: !!authTokens?.access,
  });

  const [sorting, setSorting] = useState<SortingState>([]);

  const columns: ColumnDef<Device>[] = [
    {
      accessorKey: "site",
      header: ({ column }) => (
        <Button
          variant="ghost"
          onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
          className="w-full justify-start"
        >
          Site
          <TbArrowsUpDown className="ml-2 h-4 w-4" />
        </Button>
      ),
      cell: ({ row }) => (
        <Link
          to="/deployments/$deviceId"
          params={{ deviceId: row.original.id }}
           className="text-blue-500 hover:underline"
        >
          {row.original.site}
        </Link>
      ),
    },
    {
      accessorKey: "id",
      header: ({ column }) => (
        <Button
          variant="ghost"
          onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
          className="w-full justify-start"
        >
          Device
          <TbArrowsUpDown className="ml-2 h-4 w-4" />
        </Button>
      ),
      cell: ({ row }) => row.original.id,

    },
    {
      accessorKey: "startDate",
      header: ({ column }) => (
        <Button
          variant="ghost"
          onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
          className="w-full justify-start"
        >
          Start Date
          <TbArrowsUpDown className="ml-2 h-4 w-4" />
        </Button>
      ),
    },
    {
      accessorKey: "endDate",
      header: ({ column }) => (
        <Button
          variant="ghost"
          onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
          className="w-full justify-start"
        >
          End Date
          <TbArrowsUpDown className="ml-2 h-4 w-4" />
        </Button>
      ),
    },
    {
      accessorKey: "lastUpload",
      header: ({ column }) => (
        <Button
          variant="ghost"
          onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
          className="w-full justify-start"
        >
          Last Upload
          <TbArrowsUpDown className="ml-2 h-4 w-4" />
        </Button>
      ),
    },
    {
      accessorKey: "folderSize",
      header: ({ column }) => (
        <Button
          variant="ghost"
          onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
          className="w-full justify-start"
        >
          Folder Size
          <TbArrowsUpDown className="ml-2 h-4 w-4" />
        </Button>
      ),
      cell: ({ row }) => `${bytesToMegabytes(row.original.folder_size)} MB`,    
    },
  ];

  const table = useReactTable({
    data: data,
    columns,
    state: {
      sorting,
    },
    onSortingChange: setSorting,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
  });

    const [isModalOpen, setIsModalOpen] = useState(false);

    const openModal = () => setIsModalOpen(true);
    const closeModal = () => setIsModalOpen(false);
  
    const handleSave = () => {
      closeModal();
    };
  

  return (
    <div>
    <button onClick={openModal} className="bg-green-900 text-white py-2 px-8 rounded-lg hover:bg-green-700 transition-all block w-30 ml-auto mr-4 my-4">
      Add info
    </button>
   
    <Modal isOpen={isModalOpen} onClose={closeModal}>
      <DeviceForm onSave={handleSave} />
    </Modal>

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
