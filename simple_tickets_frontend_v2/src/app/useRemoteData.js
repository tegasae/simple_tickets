import { useEffect, useState } from "react";

export function useRemoteData(key, load) {
  const [attempt, setAttempt] = useState(0);
  const [result, setResult] = useState({ phase: "idle" });
  useEffect(() => {
    const controller = new AbortController();
    load(controller.signal).then(
      (data) => {
        if (!controller.signal.aborted) setResult({ key, attempt, phase: "ready", data });
      },
      (error) => {
        if (!controller.signal.aborted) setResult({ key, attempt, phase: "error", error });
      },
    );
    return () => controller.abort();
  }, [key, attempt, load]);

  return {
    ...(result.key === key && result.attempt === attempt ? result : { phase: "loading" }),
    reload: () => setAttempt((value) => value + 1),
  };
}
