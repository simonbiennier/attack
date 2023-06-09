from http.server import BaseHTTPRequestHandler, HTTPServer
from os import curdir, sep

hostName = "192.168.86.42"
serverPort = 80


class MyServer(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/":
            self.path = "/index.html"
        try:
            sendReply = False
            if self.path.endswith(".html"):
                mimetype = "text/html"
                sendReply = True
            if self.path.endswith(".png"):
                mimetype = "image/png"
                sendReply = True
            if self.path.endswith(".ico"):
                mimetype = "image/webp"
                sendReply = True

            if sendReply:
                with open(f"{curdir}{sep}{self.path}", "rb") as f:
                    self.send_response(200)
                    self.send_header("Content-type", mimetype)
                    self.end_headers()
                    self.wfile.write(f.read())
            return
        except IOError:
            self.send_error(404, f"File Not Found: {self.path}")


if __name__ == "__main__":
    httpd = HTTPServer((hostName, serverPort), MyServer)
    print(f"Server started at http://{hostName}:{serverPort}")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass

    httpd.server_close()
    print("Server stopped.")
