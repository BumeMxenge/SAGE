// A read-only table of rows and columns, such as the courses of one year. It is a real table: the
// caption sits above it as its title, and the column headers form its first row, so a screen reader
// announces the headers as the student moves between cells. (React Aria's Table is an interactive
// grid, and these tables have nothing to select or sort.)
import type { ReactNode } from 'react'
import styles from './DataTable.module.css'

export type DataTableColumn = { key: string; header: string; align?: 'start' | 'end' }
export type DataTableRow = { id: string; cells: Record<string, ReactNode> }

type DataTableProps = {
  caption: string
  columns: DataTableColumn[]
  rows: DataTableRow[]
}

export function DataTable({ caption, columns, rows }: DataTableProps) {
  return (
    <table className={styles.table}>
      <caption className={styles.caption}>{caption}</caption>
      <thead>
        <tr>
          {columns.map((column) => (
            <th key={column.key} scope="col" className={column.align === 'end' ? styles.end : undefined}>
              {column.header}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {rows.map((row) => (
          <tr key={row.id}>
            {columns.map((column) => (
              <td key={column.key} className={column.align === 'end' ? styles.end : undefined}>
                {row.cells[column.key]}
              </td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  )
}
