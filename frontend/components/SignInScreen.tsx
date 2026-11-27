"use client"

import { useEffect, useRef } from "react"
import Image from "next/image"
import Link from "next/link"
import { useFormStatus } from "react-dom"
import { Ghost, Mail, MapPin } from "lucide-react"
import Logo from "@/assets/logo.svg"
import { signInWithGoogle } from "@/utils/authActions"
import styles from "@/app/signin/signin.module.css"

const features = [
  { icon: MapPin, label: "Track applications" },
  { icon: Mail, label: "Auto-import from Gmail" },
  { icon: Ghost, label: "Ghost detection" },
]

function GoogleMark() {
  return (
    <svg
      width="18"
      height="18"
      viewBox="0 0 18 18"
      aria-hidden="true"
    >
      <path
        fill="#4285F4"
        d="M17.64 9.2c0-.637-.057-1.251-.164-1.84H9v3.481h4.844a4.14 4.14 0 0 1-1.796 2.716v2.259h2.908c1.702-1.567 2.684-3.875 2.684-6.615z"
      />
      <path
        fill="#34A853"
        d="M9 18c2.43 0 4.467-.806 5.956-2.18l-2.908-2.259c-.806.54-1.837.86-3.048.86-2.344 0-4.328-1.584-5.036-3.711H.957v2.332A8.997 8.997 0 0 0 9 18z"
      />
      <path
        fill="#FBBC05"
        d="M3.964 10.71A5.41 5.41 0 0 1 3.682 9c0-.593.102-1.17.282-1.71V4.958H.957A8.996 8.996 0 0 0 0 9c0 1.452.348 2.827.957 4.042l3.007-2.332z"
      />
      <path
        fill="#EA4335"
        d="M9 3.58c1.321 0 2.508.454 3.44 1.345l2.582-2.58C13.463.891 11.426 0 9 0A8.997 8.997 0 0 0 .957 4.958L3.964 7.29C4.672 5.163 6.656 3.58 9 3.58z"
      />
    </svg>
  )
}

function GoogleButton() {
  const { pending } = useFormStatus()
  return (
    <button
      type="submit"
      className={styles.google}
      disabled={pending}
      aria-busy={pending}
    >
      {pending ? <span className={styles.spinner} /> : <GoogleMark />}
      {pending ? "Continuing to Google…" : "Continue with Google"}
    </button>
  )
}

function MapField() {
  return (
    <svg
      className={styles.map}
      viewBox="0 0 1200 800"
      preserveAspectRatio="xMidYMid slice"
      aria-hidden="true"
    >
      <g
        fill="none"
        stroke="rgba(245,180,0,0.4)"
        strokeWidth="1.25"
      >
        <path d="M90 640C240 560 320 490 450 430s220-150 360-190" />
        <path d="M450 430c70 90 150 170 280 200" />
        <path d="M810 240c110-40 210-20 300-80" />
        <path d="M810 240c70 110 150 170 290 220" />
        <path d="M730 630c80-70 120-150 80-240" />
      </g>
      <g fill="#F5B400">
        <circle cx="90" cy="640" r="4.5" />
        <circle cx="450" cy="430" r="4.5" />
        <circle cx="810" cy="240" r="5" />
        <circle cx="1110" cy="160" r="4" />
        <circle cx="1100" cy="460" r="4" />
        <circle cx="730" cy="630" r="4" />
        <circle cx="810" cy="390" r="3.5" />
      </g>
    </svg>
  )
}

export default function SignInScreen({ callbackUrl }: { callbackUrl: string }) {
  const rootRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const root = rootRef.current
    if (!root) return
    const fine = window.matchMedia("(hover: hover) and (pointer: fine)")
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)")
    if (!fine.matches || reduce.matches) return

    const onMove = (event: PointerEvent) => {
      root.style.setProperty("--spot-x", `${event.clientX}px`)
      root.style.setProperty("--spot-y", `${event.clientY}px`)
    }
    window.addEventListener("pointermove", onMove, { passive: true })
    return () => window.removeEventListener("pointermove", onMove)
  }, [])

  return (
    <main
      ref={rootRef}
      className={styles.root}
    >
      <div className={styles.mesh} />
      <div className={styles.grid} />
      <MapField />
      <div className={styles.spot} />
      <section className={styles.card}>
        <div className={styles.inner}>
          <Link
            href="/"
            className={styles.logoLink}
          >
            <Image
              src={Logo}
              alt="JobMap"
              priority
              className={styles.logo}
            />
          </Link>
          <p className={styles.kicker}>Sign in</p>
          <h1 className={styles.title}>Every role, one map.</h1>
          <p className={styles.tagline}>
            Track what you applied to, and what went quiet.
          </p>
          <ul className={styles.list}>
            {features.map(({ icon: Icon, label }) => (
              <li
                key={label}
                className={styles.item}
              >
                <span className={styles.icon}>
                  <Icon
                    size={15}
                    strokeWidth={2}
                    aria-hidden="true"
                  />
                </span>
                {label}
              </li>
            ))}
          </ul>
          <form
            action={signInWithGoogle}
            className={styles.form}
          >
            <input
              type="hidden"
              name="callbackUrl"
              value={callbackUrl}
            />
            <GoogleButton />
          </form>
          <p className={styles.note}>
            Connecting Gmail to import application mail is a separate step after
            you are signed in.
          </p>
        </div>
      </section>
    </main>
  )
}
