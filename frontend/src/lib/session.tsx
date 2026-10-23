import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from "react";
import { api, auth } from "../api/client";
import type { Meta, User } from "../api/types";
import { navigate } from "./router";

interface Session {
  user: User | null;
  meta: Meta | null;
  ready: boolean;
  signIn: (email: string, password: string) => Promise<void>;
  signOut: () => void;
}

const Ctx = createContext<Session | null>(null);

export function SessionProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [meta, setMeta] = useState<Meta | null>(null);
  const [ready, setReady] = useState(false);

  const signOut = useCallback(() => {
    auth.set(null);
    setUser(null);
    navigate("/login");
  }, []);

  useEffect(() => {
    auth.onUnauthorized(() => { setUser(null); navigate("/login"); });
    if (!auth.token) { setReady(true); return; }
    Promise.all([api.me(), api.meta()])
      .then(([u, m]) => { setUser(u); setMeta(m); })
      .catch(() => auth.set(null))
      .finally(() => setReady(true));
  }, []);

  const signIn = useCallback(async (email: string, password: string) => {
    const r = await api.login(email, password);
    auth.set(r.access_token);
    setUser(r.user);
    setMeta(await api.meta());
  }, []);

  return <Ctx.Provider value={{ user, meta, ready, signIn, signOut }}>{children}</Ctx.Provider>;
}

export function useSession(): Session {
  const s = useContext(Ctx);
  if (!s) throw new Error("useSession outside SessionProvider");
  return s;
}
