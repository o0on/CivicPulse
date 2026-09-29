import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  stages: [
    { duration: '20s', target: 40 },
    { duration: '40s', target: 80 },
    { duration: '30s', target: 120 },
    { duration: '20s', target: 0 },
  ],
  thresholds: {
    http_req_duration: ['p(95)<1500'],
  },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';

export default function () {
  const clientIp = `10.0.${__VU % 200}.${__ITER % 200 + 1}`;
  const headers = {
    'Content-Type': 'application/json',
    'X-Forwarded-For': clientIp,
  };

  // 1. Fetch complaints list (triggers DB query)
  http.get(`${BASE_URL}/api/complaints?page=1&page_size=20`, { headers });

  // 2. Fetch Prometheus metrics (triggers DB aggregation)
  http.get(`${BASE_URL}/api/metrics`, { headers });

  // 3. Post a municipal complaint
  const payload = JSON.stringify({
    text: `Pothole on Main Road Block ${__ITER % 10 + 1} causing severe traffic backlog`,
    location: `Block ${__ITER % 10 + 1} Gulshan`,
    reporter_contact: `citizen${__VU}@example.com`,
  });

  http.post(`${BASE_URL}/api/complaints`, payload, { headers });

  sleep(0.1);
}
