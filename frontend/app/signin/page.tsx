import SignInScreen from "@/components/SignInScreen"
import { safeCallbackPath } from "@/utils/authPaths"

export default function SignInPage({
  searchParams,
}: {
  searchParams: { callbackUrl?: string }
}) {
  return <SignInScreen callbackUrl={safeCallbackPath(searchParams.callbackUrl)} />
}
