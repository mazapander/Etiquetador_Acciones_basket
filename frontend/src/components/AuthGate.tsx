import { FormEvent, ReactNode, useEffect, useState } from "react";
import { Session } from "@supabase/supabase-js";

import { supabase } from "../lib/supabase";
import { setAccessToken } from "../lib/authSession";
import "./AuthGate.css";

type AuthGateProps = {
  children: ReactNode;
};

export function AuthGate({ children }: AuthGateProps) {
  const [session, setSession] = useState<Session | null>(null);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    supabase.auth.getSession().then(({ data }) => {
      setSession(data.session);
      setAccessToken(data.session?.access_token ?? null);
      setIsLoading(false);
    });

    const { data: subscription } = supabase.auth.onAuthStateChange((_event, nextSession) => {
      setSession(nextSession);
      setAccessToken(nextSession?.access_token ?? null);
    });

    return () => subscription.subscription.unsubscribe();
  }, []);

  async function handleLogin(event: FormEvent) {
    event.preventDefault();
    setIsSubmitting(true);
    setError(null);
    const result = await supabase.auth.signInWithPassword({ email, password });
    if (result.error) {
      setError(result.error.message);
    }
    setIsSubmitting(false);
  }

  async function handleLogout() {
    await supabase.auth.signOut();
    setAccessToken(null);
  }

  if (isLoading) {
    return <main className="auth-shell">Cargando sesion...</main>;
  }

  if (!session) {
    return (
      <main className="auth-shell">
        <form className="auth-card" onSubmit={handleLogin}>
          <div>
            <p className="eyebrow">Acceso privado</p>
            <h1>Etiquetador de acciones</h1>
            <p className="muted">Entra con tu usuario autorizado.</p>
          </div>
          {error && <div className="error-banner">{error}</div>}
          <label>
            Email
            <input type="email" value={email} onChange={(event) => setEmail(event.target.value)} required />
          </label>
          <label>
            Password
            <input type="password" value={password} onChange={(event) => setPassword(event.target.value)} required />
          </label>
          <button className="primary-button" type="submit" disabled={isSubmitting}>
            {isSubmitting ? "Entrando..." : "Entrar"}
          </button>
        </form>
      </main>
    );
  }

  return (
    <>
      <div className="session-pill">
        <span>{session.user.email}</span>
        <button type="button" onClick={() => void handleLogout()}>Salir</button>
      </div>
      {children}
    </>
  );
}
