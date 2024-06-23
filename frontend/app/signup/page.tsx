import Logo from "@/assets/logo.svg"
import Image from "next/image"
import { SignupForm } from "@/components/Signup"

function Signup() {
  return (
    <>
      <header className="max-w-6xl mx-auto px-4 sm:px-8 py-6 mb-12">
        <Image
          src={Logo}
          alt="Logo"
        />
      </header>
      <SignupForm />
    </>
  )
}
export default Signup
