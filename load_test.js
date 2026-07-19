import http from 'k6/http';
import { check } from 'k6';

export const options = {
  vus: 100,         // Number of Virtual Users
  duration: '30s'  // How long the test runs
};

export default function() {
  const url = 'http://localhost:8000/api/ping?tier=free';
  
  // Generate a random client ID between 1 and 1000
  const randomClientId = `load_tester_${Math.floor(Math.random() * 1000) + 1}`;
  
  const params = {
    headers: {
      'X-Client-Id': randomClientId,
    },
  };

  const response = http.get(url, params);
  
  check(response, {
    'is status 200 or 429': (r) => r.status === 200 || r.status === 429,
  });
}
