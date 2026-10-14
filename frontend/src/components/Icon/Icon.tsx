// Every icon the app uses, from Material Symbols Rounded. Only the icons imported here reach the
// bundle. An icon takes only its name, and filled where a filled version is imported. Its colour is
// the text colour around it, and its size is --icon-size from the parent, or 20 px.
import LeftPanelClose from '@material-symbols/svg-400/rounded/left_panel_close.svg?react'
import LeftPanelOpen from '@material-symbols/svg-400/rounded/left_panel_open.svg?react'
import CalendarToday from '@material-symbols/svg-400/rounded/calendar_today.svg?react'
import Explore from '@material-symbols/svg-400/rounded/explore.svg?react'
import Schedule from '@material-symbols/svg-400/rounded/schedule.svg?react'
import ChatBubble from '@material-symbols/svg-400/rounded/chat_bubble.svg?react'
import BorderColor from '@material-symbols/svg-400/rounded/border_color.svg?react'
import History from '@material-symbols/svg-400/rounded/history.svg?react'
import ChevronLeft from '@material-symbols/svg-400/rounded/chevron_left.svg?react'
import ChevronRight from '@material-symbols/svg-400/rounded/chevron_right.svg?react'
import KeyboardArrowDown from '@material-symbols/svg-400/rounded/keyboard_arrow_down.svg?react'
import ArrowUpward from '@material-symbols/svg-400/rounded/arrow_upward.svg?react'
import Favorite from '@material-symbols/svg-400/rounded/favorite.svg?react'
import Add from '@material-symbols/svg-400/rounded/add.svg?react'
import ViewColumn2 from '@material-symbols/svg-400/rounded/view_column_2.svg?react'
import FormatListBulleted from '@material-symbols/svg-400/rounded/format_list_bulleted.svg?react'
import Close from '@material-symbols/svg-400/rounded/close.svg?react'
import Check from '@material-symbols/svg-400/rounded/check.svg?react'
import Search from '@material-symbols/svg-400/rounded/search.svg?react'
import Error from '@material-symbols/svg-400/rounded/error.svg?react'
import Refresh from '@material-symbols/svg-400/rounded/refresh.svg?react'
import Person from '@material-symbols/svg-400/rounded/person.svg?react'
import ScanDelete from '@material-symbols/svg-400/rounded/scan_delete.svg?react'
import CloudUpload from '@material-symbols/svg-400/rounded/cloud_upload.svg?react'
import CloudOff from '@material-symbols/svg-400/rounded/cloud_off.svg?react'
import WifiOff from '@material-symbols/svg-400/rounded/wifi_off.svg?react'
import Lock from '@material-symbols/svg-400/rounded/lock.svg?react'
import LightMode from '@material-symbols/svg-400/rounded/light_mode.svg?react'
import DarkMode from '@material-symbols/svg-400/rounded/dark_mode.svg?react'
import Contrast from '@material-symbols/svg-400/rounded/contrast.svg?react'
import ArrowDownward from '@material-symbols/svg-400/rounded/arrow_downward.svg?react'
import Logout from '@material-symbols/svg-400/rounded/logout.svg?react'
import ProgressActivity from '@material-symbols/svg-400/rounded/progress_activity.svg?react'
import CheckCircle from '@material-symbols/svg-400/rounded/check_circle.svg?react'
import Help from '@material-symbols/svg-400/rounded/help.svg?react'
import Block from '@material-symbols/svg-400/rounded/block.svg?react'
import FavoriteFilled from '@material-symbols/svg-400/rounded/favorite-fill.svg?react'
import styles from './Icon.module.css'

const icons = {
  left_panel_close: LeftPanelClose,
  left_panel_open: LeftPanelOpen,
  calendar_today: CalendarToday,
  explore: Explore,
  schedule: Schedule,
  chat_bubble: ChatBubble,
  border_color: BorderColor,
  history: History,
  chevron_left: ChevronLeft,
  chevron_right: ChevronRight,
  keyboard_arrow_down: KeyboardArrowDown,
  arrow_upward: ArrowUpward,
  favorite: Favorite,
  add: Add,
  view_column_2: ViewColumn2,
  format_list_bulleted: FormatListBulleted,
  close: Close,
  check: Check,
  search: Search,
  error: Error,
  refresh: Refresh,
  person: Person,
  scan_delete: ScanDelete,
  cloud_upload: CloudUpload,
  cloud_off: CloudOff,
  wifi_off: WifiOff,
  lock: Lock,
  light_mode: LightMode,
  dark_mode: DarkMode,
  contrast: Contrast,
  arrow_downward: ArrowDownward,
  logout: Logout,
  progress_activity: ProgressActivity,
  check_circle: CheckCircle,
  help: Help,
  block: Block,
}

export type IconName = keyof typeof icons

// Only the heart has a filled version, for its "on" state
type IconProps =
  | { name: 'favorite'; filled?: boolean }
  | { name: Exclude<IconName, 'favorite'>; filled?: never }

export function Icon({ name, filled }: IconProps) {
  const Svg = filled ? FavoriteFilled : icons[name]
  return <Svg className={styles.icon} aria-hidden="true" focusable="false" />
}
