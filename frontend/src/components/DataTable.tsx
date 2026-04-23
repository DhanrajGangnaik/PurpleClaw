import type { ReactNode } from 'react';

export interface DataColumn<T> {
  key: string;
  label: string;
  render: (row: T) => ReactNode;
}

interface DataTableProps<T> {
  columns: DataColumn<T>[];
  rows: T[];
  getRowKey: (row: T) => string;
  emptyText: string;
  onRowClick?: (row: T) => void;
}

export function DataTable<T>({ columns, rows, getRowKey, emptyText, onRowClick }: DataTableProps<T>) {
  return (
    <div className="overflow-hidden rounded-card border theme-surface-strong">
      <div className="overflow-x-auto">
        <table className="min-w-full">
          <thead style={{ background: 'var(--table-head)' }}>
            <tr>
              {columns.map((column) => (
                <th key={column.key} className="theme-text-faint border-b px-4 py-3 text-left text-[11px] font-semibold uppercase tracking-[0.16em]" style={{ borderColor: 'var(--border)' }}>
                  {column.label}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.length === 0 ? (
              <tr>
                <td colSpan={columns.length} className="theme-text-faint px-4 py-12 text-center text-sm">
                  {emptyText}
                </td>
              </tr>
            ) : (
              rows.map((row) => (
                <tr
                  key={getRowKey(row)}
                  onClick={onRowClick ? () => onRowClick(row) : undefined}
                  className={`border-b transition-colors duration-150 ${onRowClick ? 'cursor-pointer' : ''}`}
                  style={{ borderColor: 'var(--table-row)' }}
                  onMouseEnter={(event) => {
                    event.currentTarget.style.background = 'var(--table-hover)';
                  }}
                  onMouseLeave={(event) => {
                    event.currentTarget.style.background = 'transparent';
                  }}
                >
                  {columns.map((column) => (
                    <td key={column.key} className="theme-text-secondary px-4 py-4 text-sm align-top">
                      {column.render(row)}
                    </td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
