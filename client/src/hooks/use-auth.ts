import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";

type User = {
  email: string;
  full_name?: string;
  role?: string;
  is_active?: boolean;
  is_blocked?: boolean;
  created_at?: string;
  last_login?: string;
  firstName?: string;
  lastName?: string;
  profileImageUrl?: string;
};

const TOKEN_KEY = "access_token";
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "";

async function fetchUser(): Promise<User | null> {
  const token = localStorage.getItem(TOKEN_KEY);
  if (!token) return null;

  const response = await fetch(`${API_BASE_URL}/api/auth/me`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (response.status === 401) {
    localStorage.removeItem(TOKEN_KEY);
    return null;
  }

  if (!response.ok) {
    throw new Error(`${response.status}: ${response.statusText}`);
  }

  return response.json();
}

async function logout(): Promise<void> {
  localStorage.removeItem(TOKEN_KEY);
}

export function useAuth() {
  const queryClient = useQueryClient();
  const { data: user, isLoading } = useQuery<User | null>({
    queryKey: ["/api/auth/me"],
    queryFn: fetchUser,
    retry: false,
    staleTime: 1000 * 60 * 5, // 5 minutes
  });

  const logoutMutation = useMutation({
    mutationFn: logout,
    onSuccess: () => {
      queryClient.setQueryData(["/api/auth/me"], null);
    },
  });

  return {
    user,
    isLoading,
    isAuthenticated: !!user,
    logout: logoutMutation.mutate,
    isLoggingOut: logoutMutation.isPending,
  };
}
