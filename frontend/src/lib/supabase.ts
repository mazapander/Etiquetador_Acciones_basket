import { createClient } from "@supabase/supabase-js";

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL as string | undefined;
const supabasePublishableKey = import.meta.env.VITE_SUPABASE_PUBLISHABLE_KEY as string | undefined;

if (!supabaseUrl || !supabasePublishableKey) {
  // Keep the error explicit: production auth cannot work without these variables.
  // Local dev can still set AUTH_ENABLED=false in the backend but the frontend login needs Supabase config.
  console.warn("Supabase frontend variables are not configured");
}

export const supabase = createClient(supabaseUrl ?? "", supabasePublishableKey ?? "");
