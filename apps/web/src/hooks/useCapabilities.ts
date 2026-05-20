import { useQuery } from "@tanstack/react-query";
import { api } from "../lib/api";

interface CapResp {
  role: string;
  capabilities: string[];
}

export function useCapabilities() {
  const { data } = useQuery({
    queryKey: ["capabilities"],
    queryFn: () => api<CapResp>("/auth/capabilities"),
    staleTime: 5 * 60 * 1000,
  });
  const set = new Set(data?.capabilities ?? []);
  return {
    role: data?.role,
    can: (capability: string) => set.has(capability),
  };
}
