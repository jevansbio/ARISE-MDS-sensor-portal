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
import { Deployment } from "@/types";
import { useQuery } from "@tanstack/react-query";
import { Link } from "@tanstack/react-router";
import { Button } from "@/components/ui/button";
import AuthContext from "@/auth/AuthContext";
import { getData } from "@/utils/FetchFunctions";
import { bytesToMegabytes } from "@/utils/convertion";
import Modal from "@/components/Modal/Modal";
import DeviceForm from "@/components/DeviceForm";

export default function DeploymentsPage() {

  const authContext = useContext(AuthContext) as any;
  const { authTokens } = authContext || { authTokens: null };
  const apiURL = "deployment/";

  const getDataFunc = async (): Promise<Deployment[]> => {
    if (!authTokens?.access) return [];
    const response_json = await getData(apiURL, authTokens.access);
  
    const deployments: Deployment[] = response_json.map((deployment: any): Deployment => ({
      deploymentId: deployment.deployment_ID,
      startDate: deployment.deployment_start,
      endDate: deployment.deployment_end,
      folder_size: deployment.folder_size,
      lastUpload: "",
      batteryLevel: 0,
      action: "",
      site_name: deployment.site_name,
      dataFile: [],
      coordinate_uncertainty: deployment.coordinate_uncertainty,
      gps_device: deployment.gps_device,
      mic_height: deployment.mic_height,
      mic_direction: deployment.mic_direction,
      habitat: deployment.habitat,
      protocol_checklist: deployment.protocol_checklist,
      score: deployment,
      comment: deployment.comment,
      user_email: deployment.user_email,
      country: deployment.country,
      longitude: deployment.longitude,
      latitude: deployment.latitude
    }));
    console.log(deployments)
    return deployments;
  };

  const { data = [] } = useQuery({
    queryKey: [apiURL],
    queryFn: getDataFunc,
    enabled: !!authTokens?.access,
  });

  const [sorting, setSorting] = useState<SortingState>([]);

  const columns: ColumnDef<Deployment>[] = [
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
          to="/deployments/$site_name"
          params={{ site_name: row.original.site_name }}
           className="text-blue-500 hover:underline"
        >
          {row.original.site_name}
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
      cell: ({ row }) => row.original.deploymentId,

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
      cell: ({ row }) => row.original.startDate,

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
      cell: ({ row }) => row.original.endDate,

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
