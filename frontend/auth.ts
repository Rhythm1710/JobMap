import NextAuth, { type DefaultSession } from "next-auth"
import Google from "next-auth/providers/google"
import { stableUserId } from "@/utils/identity"

declare module "next-auth" {
  interface Session {
    user: {
      id: string
    } & DefaultSession["user"]
  }
}

// Env is read when a request runs. Importing this module with AUTH_* unset must not throw,
// including during `next build`.
export const { handlers, auth, signIn, signOut } = NextAuth({
  providers: [
    Google({
      authorization: {
        params: {
          // Sign-in only. Gmail connect requests gmail.readonly on its own client flow.
          scope: "openid email profile",
          prompt: "select_account",
        },
      },
    }),
  ],
  session: { strategy: "jwt" },
  // Vercel sets VERCEL=1, which Auth.js already trusts. This also covers `next build`
  // and any non-Vercel host so AUTH_TRUST_HOST is optional.
  trustHost: true,
  pages: {
    signIn: "/signin",
  },
  callbacks: {
    jwt({ token, account, profile }) {
      const userId = stableUserId({
        providerAccountId: account?.providerAccountId,
        profileSub: profile?.sub,
      })
      if (userId) token.sub = userId
      return token
    },
    session({ session, token }) {
      if (session.user && token.sub) session.user.id = token.sub
      return session
    },
  },
})
