// Every icon the prototypes draw, as its closest Material Symbols Rounded icon (from Google, through
// the @material-symbols/svg-400 package). Only the icons imported here reach the bundle.
// dock_to_right is the empty panel: it collapses the open sidebar, and opens it again from the logo.
import DockToRight from '@material-symbols/svg-400/rounded/dock_to_right.svg?react'
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
import ErrorCircle from '@material-symbols/svg-400/rounded/error.svg?react'
import Refresh from '@material-symbols/svg-400/rounded/refresh.svg?react'
import Person from '@material-symbols/svg-400/rounded/person.svg?react'
import ScanDelete from '@material-symbols/svg-400/rounded/scan_delete.svg?react'
import CloudUpload from '@material-symbols/svg-400/rounded/cloud_upload.svg?react'
import CloudOff from '@material-symbols/svg-400/rounded/cloud_off.svg?react'
import WifiOff from '@material-symbols/svg-400/rounded/wifi_off.svg?react'
import Lock from '@material-symbols/svg-400/rounded/lock.svg?react'
import LightMode from '@material-symbols/svg-400/rounded/light_mode.svg?react'
import DarkMode from '@material-symbols/svg-400/rounded/dark_mode.svg?react'
import ArrowDownward from '@material-symbols/svg-400/rounded/arrow_downward.svg?react'
import FavoriteFilled from '@material-symbols/svg-400/rounded/favorite-fill.svg?react'
export const icons = {
  dock_to_right: DockToRight,
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
  error: ErrorCircle,
  refresh: Refresh,
  person: Person,
  scan_delete: ScanDelete,
  cloud_upload: CloudUpload,
  cloud_off: CloudOff,
  wifi_off: WifiOff,
  lock: Lock,
  light_mode: LightMode,
  dark_mode: DarkMode,
  arrow_downward: ArrowDownward,
}

export type IconName = keyof typeof icons

// For the review page, which shows every icon
export const iconNames = Object.keys(icons) as IconName[]

// Only the heart has a filled version, for its "on" state
export const filledFavorite = FavoriteFilled
