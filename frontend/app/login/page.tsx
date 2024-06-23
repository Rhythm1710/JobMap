import { LoginForm } from "@/components/Login"
import Logo from "@/assets/logo.svg"
import Image from "next/image"

function Login() {
  return (
    <>
      <header className="max-w-6xl mx-auto px-4 sm:px-8 py-6 mb-1 2">
        <Image
          src={Logo}
          alt="Logo"
        />
      </header>
      <LoginForm />
    </>
  )
}
export default Login
