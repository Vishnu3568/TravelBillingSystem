const http = require('http');

const data = JSON.stringify({
  contextType: "GLOBAL",
  aggregatedData: {
    totalRevenue: 100000,
    topCompanies: [
      { "name": "Ashapura", "revenue": 40000 }
    ],
    recentBills: []
  },
  userQuery: "Which company generated highest revenue?"
});

const options = {
  hostname: 'localhost',
  port: 9001,
  path: '/api/ai/chat-assistant',
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Content-Length': data.length
  }
};

const req = http.request(options, (res) => {
  let body = '';
  res.on('data', (chunk) => body += chunk);
  res.on('end', () => {
    console.log('Response:', body);
  });
});

req.on('error', (e) => {
  console.error(`problem with request: ${e.message}`);
});

req.write(data);
req.end();
