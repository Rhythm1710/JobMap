import LinksDropdown from "./LinksDropdown"
import { UserButton } from "@clerk/nextjs"
import ThemeToggle from "./ThemeToggle"

function Navbar() {
  return (
    <nav className="bg-muted flex items-center justify-between px-3 py-2 sm:px-16 sm:py-4 lg:px-24">
      <div>
        <LinksDropdown />
      </div>
      <div className="flex items-center gap-x-2 sm:gap-x-4 max-sm:[&_button]:h-11 max-sm:[&_button]:w-11">
        <ThemeToggle />
        <UserButton afterSignOutUrl="/" />
      </div>
    </nav>
  )
}
export default Navbar
