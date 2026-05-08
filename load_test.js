import http from "k6/http";
import { check, sleep } from "k6";

export const options = {
  vus: 50,
  duration: "60s",
  thresholds: {
    http_req_failed: ["rate<0.01"],
    http_req_duration: ["p(95)<250"],
  },
};

const BASE_URL = __ENV.BASE_URL || "http://localhost:8000";
const SHORT_CODE = __ENV.SHORT_CODE || "REPLACE_ME";

export default function () {
  const res = http.get(`${BASE_URL}/${SHORT_CODE}`, { redirects: 0 });

  check(res, {
    "redirect status is 307": (r) => r.status === 307,
    "location header exists": (r) => Boolean(r.headers.Location),
  });

  sleep(1);
}
