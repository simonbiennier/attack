from http.server import BaseHTTPRequestHandler, HTTPServer

hostName = "192.168.86.42"
serverPort = 80


class MyServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        with open("./wwwroot/index.html", "rb") as f:
            self.wfile.write(f.read(), "utf-8")


if __name__ == "__main__":
    httpd = HTTPServer((hostName, serverPort), MyServer)
    print(f"Server started at http://{hostName}:{serverPort}")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass

    httpd.server_close()
    print("Server stopped.")
