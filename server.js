const express = require('express');
const http = require('http');
const path = require('path');
const cors = require('cors');

const app = express();
const PORT = process.env.PORT || 3000;
const PYTHON_BACKEND_PORT = process.env.FASTAPI_PORT || 8000;
const PYTHON_BACKEND_HOST = process.env.FASTAPI_HOST || '127.0.0.1';

app.use(cors());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Serve static assets from app/static
const staticDir = path.join(__dirname, 'app', 'static');
app.use('/static', express.static(staticDir));
app.use(express.static(staticDir));

// Proxy /api requests to Python FastAPI backend
app.use('/api', (req, res) => {
  const targetUrl = `/api${req.url}`;
  
  const options = {
    hostname: PYTHON_BACKEND_HOST,
    port: PYTHON_BACKEND_PORT,
    path: targetUrl,
    method: req.method,
    headers: {
      ...req.headers,
      host: `${PYTHON_BACKEND_HOST}:${PYTHON_BACKEND_PORT}`
    }
  };

  const proxyReq = http.request(options, (proxyRes) => {
    res.writeHead(proxyRes.statusCode, proxyRes.headers);
    proxyRes.pipe(res, { end: true });
  });

  proxyReq.on('error', (err) => {
    console.error(`[Node.js Proxy Error]: Failed to reach FastAPI backend at ${PYTHON_BACKEND_HOST}:${PYTHON_BACKEND_PORT}`, err.message);
    res.status(502).json({
      error: 'FastAPI Backend Unreachable',
      message: `Ensure Python FastAPI is running on port ${PYTHON_BACKEND_PORT}. Try running: python run.py`,
      details: err.message
    });
  });

  if (req.body && Object.keys(req.body).length > 0) {
    const bodyData = JSON.stringify(req.body);
    proxyReq.setHeader('Content-Type', 'application/json');
    proxyReq.setHeader('Content-Length', Buffer.byteLength(bodyData));
    proxyReq.write(bodyData);
  }

  proxyReq.end();
});

// Fallback to index.html for SPA routing (compatible with all Express versions)
app.use((req, res) => {
  res.sendFile(path.join(staticDir, 'index.html'));
});

app.listen(PORT, () => {
  console.log('='.repeat(70));
  console.log('🚀 EduPulse AI - Student Analytics & Success Platform');
  console.log(`🌐 Node.js Web Server listening on: http://localhost:${PORT}`);
  console.log(`🔗 Proxying /api requests to FastAPI at: http://${PYTHON_BACKEND_HOST}:${PYTHON_BACKEND_PORT}`);
  console.log('='.repeat(70));
});
