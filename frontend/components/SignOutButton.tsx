import { Button } from "@/components/ui/button"
import { signOutToHome } from "@/utils/authActions"

export default function SignOutButton() {
  return (
    <form action={signOutToHome}>
      <Button
        type="submit"
        variant="outline"
        size="sm"
      >
        Sign out
      </Button>
    </form>
  )
}
