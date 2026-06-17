let accessToken: string | null = null;

export function setAccessToken(token: string | null) {
  accessToken = token;
  if ("serviceWorker" in navigator && navigator.serviceWorker.controller) {
    navigator.serviceWorker.controller.postMessage({ type: "AUTH_TOKEN", token });
  }
}

export function getAccessToken() {
  return accessToken;
}

export async function registerAuthStreamWorker(token: string | null) {
  if (!("serviceWorker" in navigator)) {
    return;
  }
  const registration = await navigator.serviceWorker.register("/auth-stream-sw.js");
  setAccessToken(token);
  const worker = registration.active ?? registration.waiting ?? registration.installing;
  worker?.postMessage({ type: "AUTH_TOKEN", token });
  await navigator.serviceWorker.ready;
  navigator.serviceWorker.controller?.postMessage({ type: "AUTH_TOKEN", token });
}
