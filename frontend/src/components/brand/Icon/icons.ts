// Every icon the prototypes draw, as its closest Material Symbols Rounded icon (from Google, through
// the @material-symbols/svg-400 package). Only the icons imported here reach the bundle. Each entry
// says where the prototypes use it (planner, onboarding, error sheet, loading sheet), so an icon with
// no use there doesn't belong here.
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
import Info from '@material-symbols/svg-400/rounded/info.svg?react'
import ArrowDownward from '@material-symbols/svg-400/rounded/arrow_downward.svg?react'
import Difference from '@material-symbols/svg-400/rounded/difference.svg?react'
import FavoriteFilled from '@material-symbols/svg-400/rounded/favorite-fill.svg?react'
export const icons = {
  // Planner: Collapse Panel on the open sidebar, and Open Sidebar on the logo of the collapsed one
  dock_to_right: DockToRight,
  // Planner: the Plan nav item and rail button, Calendar in the view toggle, and the empty term
  // ("No courses this term") in the plan and compare views. Error and loading sheets: the same nav.
  calendar_today: CalendarToday,
  // Planner: the Explore Electives nav item and rail button. Error sheet: the same nav.
  explore: Explore,
  // Planner: the Course History nav item and rail button. Error sheet: the same nav, and the tile of
  // "Electives catalogue busy".
  schedule: Schedule,
  // Planner: the assistant's header, Open Assistant on its rail, and each row of Chat History.
  // Error and loading sheets: the same header and rail.
  chat_bubble: ChatBubble,
  // Planner: New Chat in the assistant's header
  border_color: BorderColor,
  // Planner: Chat History in the assistant's header
  history: History,
  // Planner: Back beside the questionnaire's title
  chevron_left: ChevronLeft,
  // Planner: Collapse Assistant
  chevron_right: ChevronRight,
  // Planner: the plan switcher. Error sheet: the switcher in "Offline".
  keyboard_arrow_down: KeyboardArrowDown,
  // Planner: Send in the chat box. Error sheet: the same, idle.
  arrow_upward: ArrowUpward,
  // Planner: Favourite on each elective card. Error sheet: the card in "Favourite didn't save".
  favorite: Favorite,
  // Planner: Create Registration Plan on the empty plan. Onboarding: Add a Course in the review step.
  add: Add,
  // Planner: Compare. Error sheet: Compare in "Offline".
  view_column_2: ViewColumn2,
  // Planner: Course List in the view toggle, and the empty term in list view and compare.
  // Loading sheet: the view toggle.
  format_list_bulleted: FormatListBulleted,
  // Planner: Done Comparing. Onboarding: Remove File, Remove Course, the course picker's Close and
  // Clear Search. Error sheet: a failed step, and the toast's close.
  close: Close,
  // Planner: a chosen questionnaire chip. Onboarding: Account Created's tick, and the review step's
  // checkbox tick, which the prototype draws in CSS (approved difference 2). Error sheet: a done step.
  check: Check,
  // Planner: the electives search. Error sheet: the search in "Electives catalogue busy".
  // Loading sheet: the electives search.
  search: Search,
  // Error sheet: "Sign-in didn't complete", "Course history didn't save", "Saved plan won't load"
  // and "Assistant reply failed"
  error: ErrorCircle,
  // Error sheet: Retry in "Upload interrupted" and "Assistant reply failed", and Refresh in
  // "Course history out of date"
  refresh: Refresh,
  // Error sheet: the tile of "Account can't use SAGE". Planner: the avatar when Microsoft gave no name
  // (approved difference 14).
  person: Person,
  // Error sheet: the tile of "Transcript belongs to someone else"
  scan_delete: ScanDelete,
  // Onboarding: the upload drop zone
  cloud_upload: CloudUpload,
  // Onboarding: the drop zone when the transcript can't be read
  cloud_off: CloudOff,
  // Error sheet: the "Offline" banner
  wifi_off: WifiOff,
  // Error sheet: the "Session expired" dialog
  lock: Lock,
  // Onboarding: each note the transcript's reading sends with it, on the review step (new design,
  // approved difference 12)
  info: Info,
  // Onboarding: the first sign-in highlight, between the two clashing classes and the two that work
  arrow_downward: ArrowDownward,
  // Planner: a course only one of two compared plans has, on its blocks and its row (new design,
  // approved difference 12)
  difference: Difference,
}

export type IconName = keyof typeof icons

// Only the heart has a filled version: a favourite that is on, in the planner
export const filledFavorite = FavoriteFilled
