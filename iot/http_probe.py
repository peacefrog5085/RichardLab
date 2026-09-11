from dataclasses import dataclass
from html.parser import HTMLParser
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError


@dataclass
class HTTPProbeResult:
    url: str
    status: int | None = None
    server: str | None = None
    content_type: str | None = None
    title: str | None = None
    error: str | None = None

    def to_dict(self) -> dict:
        return {
            "url": self.url,
            "status": self.status,
            "server": self.server,
            "content_type": self.content_type,
            "title": self.title,
            "error": self.error,
        }


class _TitleParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_title = False
        self.parts: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() == "title":
            self.in_title = True

    def handle_endtag(self, tag):
        if tag.lower() == "title":
            self.in_title = False

    def handle_data(self, data):
        if self.in_title:
            self.parts.append(data)

    @property
    def title(self) -> str | None:
        value = " ".join(" ".join(self.parts).split())
        return value or None


def probe_http(
    ip: str,
    port: int = 80,
    timeout: float = 2.0,
) -> HTTPProbeResult:
    url = f"http://{ip}:{port}/"

    request = Request(
        url,
        headers={
            "User-Agent": "RichardLab-IoT-Probe/1.0",
        },
        method="GET",
    )

    try:
        with urlopen(request, timeout=timeout) as response:
            body = response.read(65536)

            parser = _TitleParser()
            try:
                parser.feed(body.decode("utf-8", errors="replace"))
            except Exception:
                pass

            return HTTPProbeResult(
                url=url,
                status=response.status,
                server=response.headers.get("Server"),
                content_type=response.headers.get("Content-Type"),
                title=parser.title,
            )

    except HTTPError as exc:
        return HTTPProbeResult(
            url=url,
            status=exc.code,
            server=exc.headers.get("Server"),
            content_type=exc.headers.get("Content-Type"),
            error=f"http_error:{exc.code}",
        )

    except (URLError, TimeoutError, OSError) as exc:
        return HTTPProbeResult(
            url=url,
            error=f"connection_error:{type(exc).__name__}",
        )
