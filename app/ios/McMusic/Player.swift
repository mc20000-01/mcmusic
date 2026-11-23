import AVFoundation
import Combine
import Foundation
import MediaPlayer

/// Native playback engine. Tracks are downloaded with the signed-in session
/// and played from a local file, which avoids AVFoundation's lack of access to
/// URLSession's cookie jar and gives the same instant-seek cache as the Qt and
/// Android clients.
@MainActor
final class Player: NSObject, ObservableObject {
    @Published private(set) var queue: [JSON] = []
    @Published private(set) var index = 0
    @Published private(set) var isPlaying = false
    @Published private(set) var progress: Double = 0
    @Published private(set) var duration: Double = 0
    @Published var volume: Float = 1 {
        didSet { player?.volume = volume }
    }
    @Published var shuffle = false
    @Published var repeatMode = 0 // 0 off, 1 all, 2 one

    var current: JSON? { queue.indices.contains(index) ? queue[index] : nil }
    var currentTitle: String { current?.first("title", "name", "song")?.string ?? "Nothing playing" }
    var currentArtist: String { current?.first("artist", "artist_name", "author")?.string ?? "" }

    private let client: APIClient
    private let streamPath: (JSON) -> String?
    private var player: AVPlayer?
    private var timeObserver: Any?
    private var endObserver: NSObjectProtocol?
    private var playingObserver: NSObjectProtocol?
    private var loadToken = UUID()
    private var cache: [String: URL] = [:]

    private static let cacheDir: URL = {
        let url = FileManager.default.urls(for: .cachesDirectory, in: .userDomainMask)[0]
            .appendingPathComponent("mcmusic-audio", isDirectory: true)
        try? FileManager.default.createDirectory(at: url, withIntermediateDirectories: true)
        return url
    }()

    init(client: APIClient = .shared,
         streamPath: @escaping (JSON) -> String? = { track in
             guard let id = track.first("id", "yt_id", "track_id")?.string else { return nil }
             return "tracks/\(id)/stream"
         }) {
        self.client = client
        self.streamPath = streamPath
        super.init()
        configureAudioSession()
        observePlayer()
        configureRemoteCommands()
    }

    private func configureAudioSession() {
        try? AVAudioSession.sharedInstance().setCategory(.playback, mode: .default, options: [])
        try? AVAudioSession.sharedInstance().setActive(true)
    }

    private func observePlayer() {
        endObserver = NotificationCenter.default.addObserver(
            forName: .AVPlayerItemDidPlayToEndTime, object: nil, queue: .main
        ) { [weak self] _ in
            Task { @MainActor in self?.itemDidFinish() }
        }
        playingObserver = player?.observe(\.timeControlStatus, options: [.new]) { [weak self] player, _ in
            Task { @MainActor in self?.isPlaying = player.timeControlStatus == .playing }
        }
    }

    private func configureRemoteCommands() {
        let center = MPRemoteCommandCenter.shared()
        center.playCommand.addTarget { [weak self] _ in
            Task { @MainActor in self?.player?.play() }
            return .success
        }
        center.pauseCommand.addTarget { [weak self] _ in
            Task { @MainActor in self?.player?.pause() }
            return .success
        }
        center.nextTrackCommand.addTarget { [weak self] _ in
            Task { @MainActor in self?.next() }
            return .success
        }
        center.previousTrackCommand.addTarget { [weak self] _ in
            Task { @MainActor in self?.previous() }
            return .success
        }
    }

    func play(track: JSON, from tracks: [JSON]? = nil) async {
        if let tracks { queue = tracks }
        if queue.isEmpty { queue = [track] }
        if let position = queue.firstIndex(where: { Self.id($0) == Self.id(track) }) {
            index = position
        }
        await loadCurrent()
    }

    func playQueue(_ tracks: [JSON], at position: Int = 0) async {
        queue = tracks
        index = min(max(position, 0), tracks.count - 1)
        await loadCurrent()
    }

    func clear() {
        queue = []
        index = 0
        player = nil
        isPlaying = false
        MPNowPlayingInfoCenter.default().nowPlayingInfo = nil
    }

    func append(_ tracks: [JSON], playNext: Bool = false) {
        if playNext {
            queue.insert(contentsOf: tracks, at: min(index + 1, queue.count))
        } else {
            queue.append(contentsOf: tracks)
        }
    }

    func remove(at offset: Int) {
        guard queue.indices.contains(offset) else { return }
        queue.remove(at: offset)
        if offset < index { index -= 1 }
        if queue.isEmpty {
            player = nil
            isPlaying = false
        } else if offset == index {
            index = min(index, queue.count - 1)
            Task { await loadCurrent() }
        }
    }

    func move(from source: Int, to destination: Int) {
        guard queue.indices.contains(source), queue.indices.contains(destination) else { return }
        let item = queue.remove(at: source)
        queue.insert(item, at: destination)
        if source == index { index = destination }
        else if source < index && destination >= index { index -= 1 }
        else if source > index && destination <= index { index += 1 }
    }

    func toggle() {
        guard let player else { return }
        if player.timeControlStatus == .playing { player.pause() }
        else { player.play() }
    }

    func next() {
        if shuffle && queue.count > 1 {
            var candidate = index
            while candidate == index { candidate = Int.random(in: 0..<queue.count) }
            index = candidate
        } else if index + 1 < queue.count {
            index += 1
        } else if repeatMode == 1 && !queue.isEmpty {
            index = 0
        } else {
            player?.pause()
            isPlaying = false
            return
        }
        Task { await loadCurrent() }
    }

    func previous() {
        if currentTime > 3 {
            seek(to: 0)
            return
        }
        if index > 0 { index -= 1 }
        else if repeatMode == 1 && !queue.isEmpty { index = queue.count - 1 }
        Task { await loadCurrent() }
    }

    func seek(to seconds: Double) {
        guard let player, duration > 0 else { return }
        let time = CMTime(seconds: min(max(seconds, 0), duration), preferredTimescale: 600)
        player.seek(to: time)
        progress = time.seconds
    }

    private var currentTime: Double { player?.currentTime().seconds ?? 0 }

    private func loadCurrent() async {
        guard let track = current, let path = streamPath(track) else { return }
        let token = UUID()
        loadToken = token
        isPlaying = false
        progress = 0
        duration = 0

        let id = Self.id(track) ?? UUID().uuidString
        let file = Self.cacheDir.appendingPathComponent("\(id).mp3")
        do {
            if !FileManager.default.fileExists(atPath: file.path) {
                try await client.download(to: file, from: path)
            }
            guard token == loadToken else { return }
            let item = AVPlayerItem(url: file)
            let player = AVPlayer(playerItem: item)
            player.volume = volume
            if let observer = timeObserver {
                self.player?.removeTimeObserver(observer)
            }
            timeObserver = player.addPeriodicTimeObserver(
                forInterval: CMTime(seconds: 0.5, preferredTimescale: 600), queue: .main
            ) { [weak self] time in
                Task { @MainActor in
                    self?.progress = time.seconds
                    if let duration = player.currentItem?.duration.seconds, duration.isFinite {
                        self?.duration = duration
                    }
                }
            }
            self.player = player
            observePlayer()
            updateNowPlaying()
            player.play()
        } catch {
            isPlaying = false
        }
    }

    private func itemDidFinish() {
        if repeatMode == 2 {
            seek(to: 0)
            player?.play()
        } else {
            next()
        }
    }

    private func updateNowPlaying() {
        guard let track = current else { return }
        var info: [AnyHashable: Any] = [
            MPMediaItemPropertyTitle: currentTitle,
            MPMediaItemPropertyArtist: currentArtist,
            MPNowPlayingInfoPropertyElapsedPlaybackTime: progress,
            MPNowPlayingInfoPropertyPlaybackRate: 1.0
        ]
        if duration > 0 { info[MPMediaItemPropertyPlaybackDuration] = duration }
        if let url = client.artworkURL(track.first("cover", "art", "image")?.string),
           let data = try? Data(contentsOf: url), let image = UIImage(data: data) {
            info[MPMediaItemPropertyArtwork] = MPMediaItemArtwork(boundsSize: image.size) { _ in image }
        }
        MPNowPlayingInfoCenter.default().nowPlayingInfo = info
    }

    static func id(_ track: JSON) -> String? {
        track.first("id", "yt_id", "track_id", "song_id")?.string
    }
}
