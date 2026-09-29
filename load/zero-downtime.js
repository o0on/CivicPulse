import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  scenarios: {
    continuous_traffic: {
      executor: 'constant-arrival-rate',
      rate: 30, // 30 requests per second
      timeUnit: '1s',
      duration: '45s',
      preAllocatedVUs: 15,
      maxVUs: 50,
    },
  },
  thresholds: {
    http_req_failed: ['rate==0'], // Zero failed requests allowed (100% success)
    http_req_duration: ['p(99)<500'], // 99% under 500ms
  },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';

export default function () {
  const res = http.get(`${BASE_URL}/health`);
  check(res, {
    'status is 200': (r) => r.status === 200,
  });
}
