import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  stages: [
    { duration: '30s', target: 50 },
    { duration: '1m', target: 200 },
    { duration: '30s', target: 0 },
  ],
  thresholds: {
    http_req_duration: ['p(95)<1000'],
  },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';

export default function () {
  // Hit stats endpoint to generate load
  const resStats = http.get(`${BASE_URL}/api/stats`);
  check(resStats, {
    'stats status is 200': (r) => r.status === 200,
  });

  // Post a new complaint
  const payload = JSON.stringify({
    description: 'There is a huge pothole on Main St. It needs fixing.',
    location: 'Main St',
    contact_email: 'test@example.com'
  });
  
  const params = {
    headers: {
      'Content-Type': 'application/json',
    },
  };

  const resComplaint = http.post(`${BASE_URL}/api/complaints`, payload, params);
  check(resComplaint, {
    'post complaint status is 200 or 201': (r) => r.status === 200 || r.status === 201,
  });

  sleep(1);
}
