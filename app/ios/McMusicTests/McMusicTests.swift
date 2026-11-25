import XCTest
@testable import McMusic

final class McMusicTests: XCTestCase {
    func testNormalizeAddsSchemeAndStripsTrailingSlash() {
        XCTAssertEqual(APIClient.normalize("example.com:8000/"), "http://example.com:8000")
        XCTAssertEqual(APIClient.normalize(" https://music.example.com "), "https://music.example.com")
    }

    func testRelativePathsGoThroughTheApiPrefix() throws {
        let client = APIClient(baseURL: "https://music.example.com")
        let url = try client.absoluteURL("tracks/12/stream")
        XCTAssertEqual(url.absoluteString, "https://music.example.com/api/tracks/12/stream")
    }

    func testQueryIsPreserved() throws {
        let client = APIClient(baseURL: "https://music.example.com")
        let url = try client.absoluteURL("search", query: ["q": "hello world"])
        XCTAssertEqual(url.absoluteString, "https://music.example.com/api/search?q=hello%20world")
    }

    func testTolerantJSONParsing() throws {
        let data = Data(#"{"id":"42","title":"Song","liked":true,"extra":null}"#.utf8)
        let json = try JSON(data)
        XCTAssertEqual(json["id"]?.int, 42)
        XCTAssertEqual(json.title, "Song")
        XCTAssertEqual(json["liked"]?.bool, true)
        XCTAssertTrue(json["extra"]?.isNull ?? false)
        XCTAssertNil(json["missing"])
    }

    func testTrackHelpers() throws {
        let json = try JSON(Data(#"{"id":7,"title":"T","artist":"A","cover_id":9}"#.utf8))
        XCTAssertEqual(json.trackID, 7)
        XCTAssertEqual(json.title, "T")
        XCTAssertEqual(json.artistName, "A")
        XCTAssertEqual(json.coverID, 9)
    }

    func testCoverURLUsesTheTrackCoverEndpoint() throws {
        let client = APIClient(baseURL: "https://music.example.com")
        let url = try XCTUnwrap(client.coverURL(9))
        XCTAssertEqual(url.absoluteString, "https://music.example.com/api/tracks/9/cover")
    }

    func testOutboxQueuesAndClearsReplayableWrites() {
        let suite = "McMusicTests"
        let defaults = UserDefaults(suiteName: suite)!
        defaults.removePersistentDomain(forName: suite)
        let outbox = Outbox(defaults: defaults)
        outbox.enqueue("POST", "like/7", toggle: true)
        outbox.enqueue("PUT", "settings", json: ["theme": "dusk"])
        XCTAssertEqual(outbox.count, 2)
        XCTAssertEqual(Outbox(defaults: defaults).count, 2)
        outbox.clear()
        XCTAssertEqual(outbox.count, 0)
    }

    func testAbsoluteURLAcceptsServerBuildPaths() throws {
        let client = APIClient(baseURL: "https://music.example.com")
        let url = try XCTUnwrap(URL(string: client.baseURL + "/apps/macos/mcmusic-4.0.1.dmg"))
        XCTAssertEqual(url.host, "music.example.com")
    }

    func testIconStrokeSnapsToAllowedWidths() {
        XCTAssertEqual(Lucide.nearestStroke(0.2), 1)
        XCTAssertEqual(Lucide.nearestStroke(1.3), 1.5)
        XCTAssertEqual(Lucide.nearestStroke(1.8), 2)
    }

    func testIconStrokeWidthUsesLucideDefaultAt1x() {
        // Lucide's base stroke is `size * scale / 12`; 1x is its default 2-unit
        // stroke. The `size / 6` ceiling keeps 2x from crowding small icons.
        XCTAssertEqual(Lucide.strokeWidth(1, size: 20), 20.0 / 12)
        XCTAssertEqual(Lucide.strokeWidth(1.5, size: 20), 20.0 / 8)
        XCTAssertEqual(Lucide.strokeWidth(2, size: 32), 32.0 / 6)
        XCTAssertEqual(Lucide.strokeWidth(2, size: 52), 52.0 / 6)
        XCTAssertEqual(Lucide.strokeWidth(1, size: 48), 4)
    }

    func testOnlyCirclesAndRectsAreFillable() {
        XCTAssertTrue(Lucide.Primitive.circle(12, 12, 9).isFillable)
        XCTAssertTrue(Lucide.Primitive.rect(3, 4, 18, 13, 2).isFillable)
        XCTAssertFalse(Lucide.Primitive.path("M7 4.5 L19 12 L7 19.5 Z").isFillable)
    }
}
