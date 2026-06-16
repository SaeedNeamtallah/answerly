"use client";

import { type ReactNode, useMemo, useState } from "react";
import {
  flexRender,
  getCoreRowModel,
  getFilteredRowModel,
  getPaginationRowModel,
  getSortedRowModel,
  type ColumnDef,
  type SortingState,
  useReactTable,
} from "@tanstack/react-table";

import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { DataTablePagination } from "@/components/shared/DataTablePagination";
import { DataTableToolbar } from "@/components/shared/DataTableToolbar";
import { cn } from "@/lib/utils/cn";

type LegacyTableProps = {
  columns: string[];
  rows: ReactNode[][];
  empty?: ReactNode;
  caption?: string;
  searchPlaceholder?: never;
};

type TanStackTableProps<TData> = {
  data: TData[];
  columnDefs: ColumnDef<TData, unknown>[];
  empty?: ReactNode;
  caption?: string;
  searchPlaceholder?: string;
  pageSize?: number;
};

type DataTableProps<TData> = LegacyTableProps | TanStackTableProps<TData>;

function isTanStackTable<TData>(props: DataTableProps<TData>): props is TanStackTableProps<TData> {
  return "data" in props && "columnDefs" in props;
}

export function DataTable<TData>(props: DataTableProps<TData>) {
  if (!isTanStackTable(props)) {
    if (props.rows.length === 0 && props.empty) {
      return <>{props.empty}</>;
    }

    return (
      <div className="overflow-hidden rounded-xl border border-border bg-card shadow-sm">
        <Table>
          {props.caption ? <caption className="sr-only">{props.caption}</caption> : null}
          <TableHeader>
            <TableRow className="bg-muted/40">
              {props.columns.map((column) => (
                <TableHead key={column}>{column}</TableHead>
              ))}
            </TableRow>
          </TableHeader>
          <TableBody>
            {props.rows.map((row, index) => (
              <TableRow key={index}>
                {row.map((cell, cellIndex) => (
                  <TableCell key={`${index}-${cellIndex}`}>{cell}</TableCell>
                ))}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    );
  }

  return <InteractiveDataTable {...props} />;
}

function InteractiveDataTable<TData>({
  data,
  columnDefs,
  empty,
  caption,
  searchPlaceholder,
  pageSize = 10,
}: TanStackTableProps<TData>) {
  const [sorting, setSorting] = useState<SortingState>([]);
  const [globalFilter, setGlobalFilter] = useState("");
  const columns = useMemo(() => columnDefs, [columnDefs]);

  // eslint-disable-next-line react-hooks/incompatible-library -- TanStack Table returns function-bearing state by design.
  const table = useReactTable({
    data,
    columns,
    state: {
      sorting,
      globalFilter,
    },
    initialState: {
      pagination: {
        pageSize,
      },
    },
    onSortingChange: setSorting,
    onGlobalFilterChange: setGlobalFilter,
    getCoreRowModel: getCoreRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
  });

  if (data.length === 0 && empty) {
    return <>{empty}</>;
  }

  const rows = table.getRowModel().rows;

  return (
    <div className="overflow-hidden rounded-xl border border-border bg-card shadow-sm">
      <DataTableToolbar
        search={globalFilter}
        onSearchChange={setGlobalFilter}
        searchPlaceholder={searchPlaceholder}
        resultLabel={`${table.getFilteredRowModel().rows.length} records`}
      />
      <div className="overflow-x-auto">
        <Table>
          {caption ? <caption className="sr-only">{caption}</caption> : null}
          <TableHeader>
            {table.getHeaderGroups().map((headerGroup) => (
              <TableRow key={headerGroup.id} className="bg-muted/40">
                {headerGroup.headers.map((header) => (
                  <TableHead
                    key={header.id}
                    className={cn(header.column.getCanSort() && "cursor-pointer select-none")}
                    onClick={header.column.getToggleSortingHandler()}
                  >
                    {header.isPlaceholder ? null : flexRender(header.column.columnDef.header, header.getContext())}
                    {header.column.getIsSorted() === "asc" ? " ASC" : null}
                    {header.column.getIsSorted() === "desc" ? " DESC" : null}
                  </TableHead>
                ))}
              </TableRow>
            ))}
          </TableHeader>
          <TableBody>
            {rows.length > 0 ? (
              rows.map((row) => (
                <TableRow key={row.id}>
                  {row.getVisibleCells().map((cell) => (
                    <TableCell key={cell.id}>{flexRender(cell.column.columnDef.cell, cell.getContext())}</TableCell>
                  ))}
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell colSpan={columnDefs.length} className="h-28 text-center text-muted-foreground">
                  No results match your search.
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>
      <DataTablePagination
        pageIndex={table.getState().pagination.pageIndex}
        pageCount={table.getPageCount()}
        canPreviousPage={table.getCanPreviousPage()}
        canNextPage={table.getCanNextPage()}
        onPreviousPage={() => table.previousPage()}
        onNextPage={() => table.nextPage()}
        itemLabel={`Showing ${rows.length} of ${table.getFilteredRowModel().rows.length} records`}
      />
    </div>
  );
}
