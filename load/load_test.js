import http from "k6/http";
import { check, sleep } from "k6";

const BASE = __ENV.BASE_URL || "http://localhost:8000/api/v1";

export const options = {
  scenarios: {
    smoke: {
      executor: "shared-iterations",
      vus: 2,
      iterations: 10,
    },
    load: {
      executor: "ramping-vus",
      startVUs: 1,
      stages: [
        { duration: "30s", target: 20 },
        { duration: "1m", target: 20 },
        { duration: "30s", target: 0 },
      ],
      startTime: "10s",
    },
  },
  thresholds: {
    http_req_duration: ["p(95)<1000"],
    http_req_failed: ["rate<0.01"],
  },
};

export default function () {
  const health = http.get(`${BASE}/health`);
  check(health, { "health 200": (r) => r.status === 200 });

  const login = http.post(
    `${BASE}/auth/login`,
    JSON.stringify({ email: "load@testmail.dev", password: "Testpass1!" }),
    { headers: { "Content-Type": "application/json" } }
  );
  check(login, {
    "login 200": (r) => r.status === 200,
  });

  sleep(1);
}
