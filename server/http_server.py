from http.server import SimpleHTTPRequestHandler, HTTPServer
from os import curdir, sep

hostName = "192.168.86.42"


class MyServer(SimpleHTTPRequestHandler):
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
                mimetype = "image/x-icon"
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
    http = HTTPServer((hostName, 80), MyServer)

    try:
        http.serve_forever()
    except KeyboardInterrupt:
        pass

    http.server_close()
    print("Server stopped.")
