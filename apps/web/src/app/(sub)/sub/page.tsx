import { redirect } from "next/navigation";

export default function SubRootPage() {
  redirect("/sub/dashboard");
}
