// An icon from Material Symbols Rounded (see icons.ts). It takes only its name, and filled where a
// filled version exists. Its colour is the text colour around it, and its size is --icon-size from
// the parent, or 20 px.
import { filledFavorite, type IconName, icons } from './icons.ts'
import styles from './Icon.module.css'

// Every icon but favorite, the only one with a filled version. A component that draws its icon one way
// takes one of these.
export type PlainIconName = Exclude<IconName, 'favorite'>

type IconProps =
  | { name: 'favorite'; filled?: boolean }
  | { name: PlainIconName; filled?: never }

export function Icon({ name, filled }: IconProps) {
  const Svg = filled ? filledFavorite : icons[name]
  return <Svg className={styles.icon} aria-hidden="true" focusable="false" />
}
