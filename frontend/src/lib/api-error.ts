import axios from "axios";

/**
 * User-facing message for a failed API call.
 * Backend `detail` is shown only for client errors (4xx), where it is a
 * validation message meant for the user. Server and network failures get a
 * plain-language message instead of raw exception text.
 */
export function apiErrorMessage(err: unknown, fallback = "Something went wrong. Please try again."): string {
  if (!axios.isAxiosError(err)) return fallback;
  const status = err.response?.status;
  if (!err.response) return "Can't reach the server. Check your connection and try again.";
  if (status && status >= 400 && status < 500) {
    const detail = err.response.data?.detail;
    if (typeof detail === "string" && detail) return detail;
    if (Array.isArray(detail)) {
      const msgs = detail.map((d) => (typeof d?.msg === "string" ? d.msg : "")).filter(Boolean);
      if (msgs.length) return msgs.join("; ");
    }
    return fallback;
  }
  return "The server ran into a problem. Please try again shortly.";
}
