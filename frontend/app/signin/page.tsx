import Image from "next/image"
import Link from "next/link"
import Logo from "../../assets/logo.svg"
import { Button } from "@/components/ui/button"
import { signInWithGoogle } from "@/utils/authActions"
import { safeCallbackPath } from "@/utils/authPaths"

export default function SignInPage({
  searchParams,
}: {
  searchParams: { callbackUrl?: string }
}) {
  const callbackUrl = safeCallbackPath(searchParams.callbackUrl)

  return (
    <main>
      <header className="max-w-6xl mx-auto px-4 sm:px-8 py-6">
        <Link href="/">
          <Image
            src={Logo}
            alt="JobMap"
          />
        </Link>
      </header>
      <section className="max-w-6xl mx-auto px-4 py-8 sm:px-8">
        <h1 className="text-4xl font-bold text-[#F8B500] md:text-5xl">Sign in</h1>
        <p className="leading-loose max-w-md mt-4">
          Use your Google account to open JobMap. Connecting Gmail to import
          application mail is a separate step after you are signed in.
        </p>
        <form
          action={signInWithGoogle}
          className="mt-7"
        >
          <input
            type="hidden"
            name="callbackUrl"
            value={callbackUrl}
          />
          <Button
            type="submit"
            className="h-11 lg:h-10"
          >
            Sign in with Google
          </Button>
        </form>
      </section>
    </main>
  )
}
