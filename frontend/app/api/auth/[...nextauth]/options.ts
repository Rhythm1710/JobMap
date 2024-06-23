// import GitHubProvider from "next-auth/providers/github"
// import GoogleProvider from "next-auth/providers/google"

// export const options = {
//   providers: [
//     GitHubProvider({
//       profile(profile) {
//         console.log("Profile", profile)

//         let userRole = "Github User"
//         if (profile?.email == "itsrhythmarora17@gmail.com") {
//           userRole = "admin"
//         }
//         return {
//           ...profile,
//           id:profile.id.toString(),
//           role: userRole,
//         }
//       },
//       clientId: getEnvVariable("GOOGLE_ID"),
//       clientSecret: getEnvVariable("GOOGLE_SECRET"),
//     }),
//     GoogleProvider({
//       profile(profile) {
//         console.log("Profile", profile)

//         let userRole = "Github User"
//         if (profile?.email == "itsrhythmarora17@gmail.com") {
//           userRole = "admin"
//         }
//         return {
//           ...profile,
//           id: profile.sub,
//           role: userRole,
//         }
//       },
//       clientId: getEnvVariable("GITHUB_ID"),
//       clientSecret: getEnvVariable("GITHUB_SECRET"),
//     }),
//   ],
// //   callbacks: {
// //     async jwt({ token, user }) {
// //       if (user) token.role = user.role
// //       return token
// //     },
// //     async session({ session, token }) {
// //       if (session?.user) session.user.role = token.role
// //       return session
// //     },
// //   },
// }
// function getEnvVariable(arg0: string): string {
//     throw new Error("Function not implemented.")
// }

