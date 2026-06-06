import http from "k6/http";
import { check, sleep } from "k6";

const baseUrl = __ENV.BASE_URL || "http://localhost:8080";
const targetPath = __ENV.TARGET_PATH || "/api/demo/cpu";
const durationMs = __ENV.CPU_DURATION_MS || "350";
const smokeTest = String(__ENV.SMOKE_TEST || "false").toLowerCase() === "true";

export const options = {
  scenarios: smokeTest
    ? {
        smoke: {
          executor: "shared-iterations",
          vus: 1,
          iterations: 1,
          maxDuration: "30s",
        },
      }
    : {
        hpa_scale_out: {
          executor: "ramping-vus",
          stages: [
            { duration: "1m", target: 20 },
            { duration: "4m", target: 60 },
            { duration: "2m", target: 60 },
            { duration: "2m", target: 0 },
          ],
          gracefulRampDown: "20s",
        },
      },
  thresholds: {
    http_req_failed: ["rate<0.05"],
    http_req_duration: ["p(95)<2500"],
  },
};

export default function () {
  const response = http.get(`${baseUrl}${targetPath}?duration_ms=${durationMs}`, {
    tags: {
      endpoint: "hpa-cpu-demo",
    },
  });

  check(response, {
    "status is 200": (res) => res.status === 200,
    "hpa demo response": (res) => {
      try {
        return res.json("purpose") === "hpa-demo";
      } catch {
        return false;
      }
    },
  });

  sleep(0.2);
}
