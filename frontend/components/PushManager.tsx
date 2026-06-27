"use client";

import { useEffect, useState, useCallback } from "react";
import { Bell, BellOff, Loader2 } from "lucide-react";
import { getStoredSession, onAuthChange } from "@/lib/auth";
import {
  getNotificationPrefs,
  updateNotificationPrefs,
  getVapidPublicKey,
  subscribePush,
  unsubscribePush,
} from "@/lib/api";

function urlBase64ToUint8Array(base64String: string): Uint8Array {
  const padding = "=".repeat((4 - (base64String.length % 4)) % 4);
  const base64 = (base64String + padding).replace(/-/g, "+").replace(/_/g, "/");
  const rawData = window.atob(base64);
  const outputArray = new Uint8Array(rawData.length);
  for (let i = 0; i < rawData.length; ++i) {
    outputArray[i] = rawData.charCodeAt(i);
  }
  return outputArray;
}

export function PushManager() {
  const [enabled, setEnabled] = useState(false);
  const [loading, setLoading] = useState(true);
  const [supported, setSupported] = useState(false);
  const [session, setSession] = useState(getStoredSession());

  useEffect(() => {
    setSupported("serviceWorker" in navigator && "PushManager" in window && "Notification" in window);
  }, []);

  useEffect(() => {
    const unsubscribe = onAuthChange(() => {
      setSession(getStoredSession());
    });
    return unsubscribe;
  }, []);

  useEffect(() => {
    if (!session) {
      setEnabled(false);
      setLoading(false);
      return;
    }
    let active = true;
    getNotificationPrefs()
      .then((prefs) => {
        if (!active) return;
        setEnabled(prefs.notifications_enabled);
      })
      .catch(() => {})
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [session]);

  const toggle = useCallback(async () => {
    if (!session) return;
    const newState = !enabled;
    setEnabled(newState);

    try {
      await updateNotificationPrefs({ notifications_enabled: newState });

      if (newState && Notification.permission !== "granted") {
        const permission = await Notification.requestPermission();
        if (permission !== "granted") {
          setEnabled(false);
          await updateNotificationPrefs({ notifications_enabled: false });
          return;
        }
      }

      if (newState && supported) {
        const registration = await navigator.serviceWorker.ready;
        const existing = await registration.pushManager.getSubscription();
        if (existing) {
          const subJson = existing.toJSON();
          if (subJson.endpoint) {
            await subscribePush({
              endpoint: subJson.endpoint,
              p256dh: subJson.keys?.p256dh ?? "",
              auth: subJson.keys?.auth ?? "",
            });
          }
          return;
        }

        const keyResponse = await getVapidPublicKey();
        if (!keyResponse.publicKey) return;

        const subscription = await registration.pushManager.subscribe({
          userVisibleOnly: true,
          applicationServerKey: urlBase64ToUint8Array(keyResponse.publicKey),
        });

        const subJson = subscription.toJSON();
        if (subJson.endpoint) {
          await subscribePush({
            endpoint: subJson.endpoint,
            p256dh: subJson.keys?.p256dh ?? "",
            auth: subJson.keys?.auth ?? "",
          });
        }
      } else if (!newState && supported) {
        const registration = await navigator.serviceWorker.ready;
        const existing = await registration.pushManager.getSubscription();
        if (existing) {
          const subJson = existing.toJSON();
          if (subJson.endpoint) {
            await unsubscribePush({
              endpoint: subJson.endpoint,
              p256dh: subJson.keys?.p256dh ?? "",
              auth: subJson.keys?.auth ?? "",
            });
          }
          await existing.unsubscribe();
        }
      }
    } catch {
      setEnabled(!newState);
      await updateNotificationPrefs({ notifications_enabled: !newState });
    }
  }, [enabled, session, supported]);

  if (!session) return null;
  if (loading) {
    return (
      <button
        disabled
        className="inline-flex shrink-0 items-center gap-2 whitespace-nowrap rounded-full border border-[rgba(255,255,255,0.10)] bg-[rgba(255,255,255,0.05)] px-4 py-2 text-sm text-mindmirror-secondary"
      >
        <Loader2 className="h-4 w-4 animate-spin" />
      </button>
    );
  }

  return (
    <button
      onClick={toggle}
      title={enabled ? "Notifications on" : "Notifications off"}
      className={`inline-flex shrink-0 items-center gap-2 whitespace-nowrap rounded-full border px-4 py-2 text-sm transition-colors duration-200 ease-out ${
        enabled
          ? "border-[rgba(124,58,237,0.3)] bg-[rgba(124,58,237,0.1)] text-mindmirror-primary hover:border-[rgba(124,58,237,0.5)]"
          : "border-[rgba(255,255,255,0.10)] bg-[rgba(255,255,255,0.05)] text-mindmirror-secondary hover:border-[rgba(255,255,255,0.35)]"
      }`}
    >
      {enabled ? <Bell className="h-4 w-4" /> : <BellOff className="h-4 w-4" />}
      <span className="hidden sm:inline">{enabled ? "Notifications on" : "Notifications off"}</span>
    </button>
  );
}
