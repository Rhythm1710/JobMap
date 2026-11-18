import { Button } from "@/components/ui/button"
import Logo from "../assets/logo.svg"
import LandingImg from "../assets/main.svg"
import Image from "next/image"
import Link from "next/link"

export default function Home() {
  return (
    <main>
      <header className="max-w-6xl mx-auto px-4 sm:px-8 py-6">
        <Image
          src={Logo}
          alt="Logo"
        />
      </header>
      <section className="max-w-6xl mx-auto grid items-center px-4 py-8 sm:px-8 lg:h-screen lg:-mt-20 lg:grid-cols-[1fr,400px] lg:py-0">
        <div>
          <h1 className="capitalize text-4xl text-[#F8B500] md:text-7xl font-bold">
            job <span className="text-[#F8B500]">tracking</span>
          </h1>
          <p className="leading-loose max-w-md mt-10">
            Track every application in one place. Add roles yourself, or connect
            Gmail and JobMap will pull in confirmations, assessments, interviews,
            rejections, and offers.
          </p>
          <Button
            asChild
            className="mt-7 h-11 lg:h-10"
          >
            <Link href="/add-job">Get Started</Link>
          </Button>
        </div>
        <Image
          src={LandingImg}
          alt="landing"
          className="hidden lg:block max-w-xl"
        />
      </section>
    </main>
  )
}
