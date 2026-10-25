import http from "node:http";

const server = http.createServer((req, res) => {
  const options = {
    hostname: "127.0.0.1",
    port: 5174,
    path: req.url,
    method: req.method,
    headers: { ...req.headers, host: "localhost:5174" },
  };

  const proxyReq = http.request(options, (proxyRes) => {
    res.writeHead(proxyRes.statusCode || 200, proxyRes.headers);
    proxyRes.pipe(res, { end: true });
  });

  proxyReq.on("error", (err) => {
    res.writeHead(502, { "Content-Type": "text/plain" });
    res.end(`Proxy to port 5174 error: ${err.message}`);
  });

  req.pipe(proxyReq, { end: true });
});

server.on("upgrade", (req, socket, head) => {
  const proxySocket = http.request({
    hostname: "127.0.0.1",
    port: 5174,
    path: req.url,
    method: req.method,
    headers: { ...req.headers, host: "localhost:5174" },
  });

  proxySocket.on("upgrade", (proxyRes, upstreamSocket, upstreamHead) => {
    socket.write(`HTTP/${req.httpVersion} 101 Switching Protocols\r\n` +
      Object.entries(proxyRes.headers).map(([k, v]) => `${k}: ${v}`).join("\r\n") +
      "\r\n\r\n");
    upstreamSocket.pipe(socket);
    socket.pipe(upstreamSocket);
  });

  proxySocket.on("error", () => {
    socket.destroy();
  });

  proxySocket.end();
});

server.listen(5173, "127.0.0.1", () => {
  console.log("Port 5173 proxy to 5174 ready with HMR websocket support.");
});
