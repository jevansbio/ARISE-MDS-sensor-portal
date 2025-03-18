import {
	Table,
	TableBody,
	TableCell,
	TableHead,
	TableHeader,
	TableRow,
} from '@/components/ui/table';
import { AudioFile } from '@/types';
import { Button } from '@/components/ui/button';
import {
  type ColumnDef,
  flexRender,
  getCoreRowModel,
  getSortedRowModel,
  type SortingState,
  useReactTable,
} from '@tanstack/react-table';
import { TbArrowsUpDown } from 'react-icons/tb';
import { Link } from '@tanstack/react-router';
import { useSuspenseQuery } from '@tanstack/react-query';
import { audioFilesQueryOptions } from '@/api/query';
import { Route } from '.';
import { useState } from 'react';


export default function DeviceAudioFilesPage() {

  const { deviceId } = Route.useParams();
	// Define table columns for the audio files table
	const { data: audioFiles } = useSuspenseQuery(audioFilesQueryOptions(deviceId));

  const columns: ColumnDef<AudioFile>[] = [
    {
      accessorKey: 'id',
      header: ({ column }) => (
        <Button
          variant="ghost"
          onClick={() => column.toggleSorting(column.getIsSorted() === 'asc')}
          className="w-full justify-start"
        >
          ID
          <TbArrowsUpDown className="ml-2 h-4 w-4" />
        </Button>
      ),
      cell: ({ row }) => (
        <Link
          to="/devices/$deviceId/$audioFileId"
          params={{ deviceId: deviceId, audioFileId: row.original.id }}
          className="text-blue-500 hover:underline"
        >
          {row.original.id}
        </Link>
      ),
    },
    {
      accessorKey: 'config',
      header: 'Config',
    },
    {
      accessorKey: 'samplerate',
      header: ({ column }) => (
        <Button
          variant="ghost"
          onClick={() => column.toggleSorting(column.getIsSorted() === 'asc')}
          className="w-full justify-start"
        >
          Sample Rate
          <TbArrowsUpDown className="ml-2 h-4 w-4" />
        </Button>
      ),
      cell: ({ row }) => `${row.original.samplerate} Hz`,
    },
    {
      accessorKey: 'fileLength',
      header: ({ column }) => (
        <Button
          variant="ghost"
          onClick={() => column.toggleSorting(column.getIsSorted() === 'asc')}
          className="w-full justify-start"
        >
          File Length
          <TbArrowsUpDown className="ml-2 h-4 w-4" />
        </Button>
      ),
    },
    {
      accessorKey: 'fileSize',
      header: ({ column }) => (
        <Button
          variant="ghost"
          onClick={() => column.toggleSorting(column.getIsSorted() === 'asc')}
          className="w-full justify-start"
        >
          File Size (MB)
          <TbArrowsUpDown className="ml-2 h-4 w-4" />
        </Button>
      ),
      cell: ({ row }) => `${row.original.fileSize} MB`,
    },
  ];

	// Table state and instance for sorting and rendering
  const [sorting, setSorting] = useState<SortingState>([]);
  const table = useReactTable({
    data: audioFiles,
    columns,
    state: { sorting },
    onSortingChange: setSorting,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
  });

  return (
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
  );
}