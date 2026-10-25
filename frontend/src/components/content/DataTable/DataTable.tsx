// A read-only table of rows and columns, such as the courses of one year. It is a real table: the
// caption sits above it as its title, and the column headers form its first row, so a screen reader
// announces the headers as the student moves between cells. (React Aria's Table is an interactive
// grid, and these tables have nothing to select or sort.) A scrollable table fills the height it is
// given and scrolls its rows inside, with its caption and headers kept in view. Its box is then a tab
// stop named by the caption, so the keyboard can scroll it too.
import { type ReactNode, type Ref, useId } from 'react'
import styles from './DataTable.module.css'

// A column that fits is as wide as its widest cell, and the other columns share the rest of the row
export type DataTableColumn = { key: string; header: string; align?: 'start' | 'end'; fit?: boolean }
export type DataTableRow = { id: string; cells: Record<string, ReactNode> }

type DataTableProps = {
  // Its title, or a skeleton in its place while a page's read is on its way
  caption: ReactNode
  // Figures at the end of the caption's line, such as a year's average and credits. Being in the
  // caption, they are part of the table's name. Only for a table that doesn't scroll: they wrap under
  // the caption in a narrow window, and a scrollable table's caption has a fixed height.
  detail?: ReactNode
  columns: DataTableColumn[]
  rows: DataTableRow[]
  // In a box with rounded corners, as Course History's years are
  outlined?: boolean
  scrollable?: boolean
  // A scrollable table's box, so a page can move focus to it
  ref?: Ref<HTMLElement>
}

// A cell's classes, from its column's alignment and whether the column fits its content
function cellClass({ align, fit }: DataTableColumn): string | undefined {
  return [align === 'end' && styles.end, fit && styles.fit].filter(Boolean).join(' ') || undefined
}

export function DataTable({ caption, detail, columns, rows, outlined = false, scrollable = false, ref }: DataTableProps) {
  const captionId = useId()
  const table = (
    <table className={outlined ? `${styles.table} ${styles.outlined}` : styles.table}>
      {/* A space between the title and its figures, so the table's name never runs them together */}
      <caption id={captionId} className={styles.caption}>
        {detail ? (
          <span className={styles.captionLine}>
            <span>{caption}</span> <span className={styles.detail}>{detail}</span>
          </span>
        ) : (
          caption
        )}
      </caption>
      <thead>
        <tr>
          {columns.map((column) => (
            <th key={column.key} scope="col" className={cellClass(column)}>
              {column.header}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {rows.map((row) => (
          <tr key={row.id}>
            {columns.map((column) => (
              <td key={column.key} className={cellClass(column)}>
                {row.cells[column.key]}
              </td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  )
  if (!scrollable) return table
  return (
    // A scrolling box must be a tab stop, or the keyboard can't scroll a table with nothing to press
    // oxlint-disable-next-line jsx-a11y/no-noninteractive-tabindex
    <section ref={ref} tabIndex={0} aria-labelledby={captionId} className={styles.scroll}>
      {table}
    </section>
  )
}
