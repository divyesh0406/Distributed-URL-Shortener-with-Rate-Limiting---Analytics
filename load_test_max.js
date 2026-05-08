import http from "k6/http";
import { check } from "k6";

export const options = {
  vus: Number(__ENV.VUS || 200),
  duration: __ENV.DURATION || "60s",
  thresholds: {
    http_req_failed: ["rate<0.01"],
    http_req_duration: ["p(95)<1000"],
  },
};

const BASE_URL = __ENV.BASE_URL || "http://localhost:8000";
const SHORT_CODE = __ENV.SHORT_CODE;

if (!SHORT_CODE) {
  throw new Error("Set SHORT_CODE to a valid short code before running k6.");
}

export default function () {
  const res = http.get(`${BASE_URL}/${SHORT_CODE}`, { redirects: 0 });

  check(res, {
    "redirect status is 307": (r) => r.status === 307,
    "location header exists": (r) => Boolean(r.headers.Location),
  });
}
