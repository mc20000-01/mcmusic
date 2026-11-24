import AVFoundation
import Combine
import Foundation
import MediaPlayer
import UIKit

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
    @Published var shuffle = false {
        didSet { persistQueue() }
    }
    @Published var repeatMode = 0 { // 0 off, 1 all, 2 one
        didSet { persistQueue() }
    }
    @Published var autoplay = true {
        didSet { persistQueue() }
    }
    @Published private(set) var sleepMinutes = 0
    @Published private(set) var sleepRemaining = 0

    var current: JSON? { queue.indices.contains(index) ? queue[index] : nil }
    var currentTitle: String { current?.first("title", "name", "song")?.string ?? "Nothing playing" }
    var currentArtist: String { current?.first("artist", "artist_name", "author")?.string ?? "" }
    var currentTrackID: Int? {
        guard let current, let value = Self.id(current) else { return nil }
        return Int(value)
    }

    private struct QueueSnapshot: Codable {
        let tracks: String
        let index: Int
        let position: Double
        let repeatMode: Int
        let shuffle: Bool
        let autoplay: Bool
        let savedAt: TimeInterval
    }

    private let client: APIClient
    private let streamPath: (JSON) -> String?
    private var player: AVPlayer?
    private var timeObserver: Any?
    private var endObserver: NSObjectProtocol?
    private var statusObservation: NSKeyValueObservation?
    private var loadToken = UUID()
    private var cache: [String: URL] = [:]
    private var pendingSeek: Double?
    private var radioLoading = false
    private var sleepTimer: Timer?
    private var sleepFinishedAt: Date?
    private static let snapshotKey = "mcmusic.queue.v1"

    static let cacheDir: URL = {
        let url = FileManager.default.urls(for: .cachesDirectory, in: .userDomainMask)[0]
            .appendingPathComponent("mcmusic-audio", isDirectory: true)
        try? FileManager.default.createDirectory(at: url, withIntermediateDirectories: true)
        return url
    }()

    static func audioCacheBytes() -> Int64 {
        let files = (try? FileManager.default.contentsOfDirectory(at: cacheDir, includingPropertiesForKeys: [.fileSizeKey])) ?? []
        return files.reduce(Int64(0)) { total, url in
            let size = (try? url.resourceValues(forKeys: [.fileSizeKey]).fileSize) ?? 0
            return total + Int64(size)
        }
    }

    static func clearAudioCache() {
        let files = (try? FileManager.default.contentsOfDirectory(at: cacheDir, includingPropertiesForKeys: nil)) ?? []
        for url in files { try? FileManager.default.removeItem(at: url) }
    }

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
        guard endObserver == nil else { return }
        endObserver = NotificationCenter.default.addObserver(
            forName: .AVPlayerItemDidPlayToEndTime, object: nil, queue: .main
        ) { [weak self] _ in
            Task { @MainActor in self?.itemDidFinish() }
        }
    }

    private func configureRemoteCommands() {
        let center = MPRemoteCommandCenter.shared()
        center.playCommand.addTarget { [weak self] _ in
            Task { @MainActor in self?.resumePlayback() }
            return .success
        }
        center.pauseCommand.addTarget { [weak self] _ in
            Task { @MainActor in self?.pausePlayback() }
            return .success
        }
        center.togglePlayPauseCommand.addTarget { [weak self] _ in
            Task { @MainActor in self?.toggle() }
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
        center.changePlaybackPositionCommand.addTarget { [weak self] event in
            guard let event = event as? MPChangePlaybackPositionCommandEvent else { return .commandFailed }
            Task { @MainActor in self?.seek(to: event.positionTime) }
            return .success
        }
    }

    // MARK: - queue control

    func play(track: JSON, from tracks: [JSON]? = nil) async {
        if let tracks { queue = tracks }
        if queue.isEmpty { queue = [track] }
        if let position = queue.firstIndex(where: { Self.id($0) == Self.id(track) }) {
            index = position
        }
        persistQueue()
        await loadCurrent()
    }

    func playQueue(_ tracks: [JSON], at position: Int = 0) async {
        queue = tracks
        index = tracks.isEmpty ? 0 : min(max(position, 0), tracks.count - 1)
        persistQueue()
        await loadCurrent()
    }

    func clear() {
        queue = []
        index = 0
        player = nil
        statusObservation = nil
        isPlaying = false
        progress = 0
        duration = 0
        pendingSeek = nil
        cancelSleepTimer()
        UserDefaults.standard.removeObject(forKey: Self.snapshotKey)
        MPNowPlayingInfoCenter.default().nowPlayingInfo = nil
    }

    func append(_ tracks: [JSON], playNext: Bool = false) {
        guard !tracks.isEmpty else { return }
        if playNext {
            queue.insert(contentsOf: tracks, at: min(index + 1, queue.count))
        } else {
            queue.append(contentsOf: tracks)
        }
        persistQueue()
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
        persistQueue()
    }

    func move(from source: Int, to destination: Int) {
        guard queue.indices.contains(source), queue.indices.contains(destination) else { return }
        let item = queue.remove(at: source)
        queue.insert(item, at: destination)
        if source == index { index = destination }
        else if source < index && destination >= index { index -= 1 }
        else if source > index && destination <= index { index += 1 }
        persistQueue()
    }

    // MARK: - transport

    func toggle() {
        if isPlaying { pausePlayback() } else { resumePlayback() }
    }

    func pausePlayback() {
        player?.pause()
        isPlaying = false
        updateNowPlaying()
    }

    func resumePlayback() {
        guard let player else {
            Task { await loadCurrent() }
            return
        }
        player.play()
        isPlaying = true
        updateNowPlaying()
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
            pausePlayback()
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
        persistQueue()
    }

    private var currentTime: Double { player?.currentTime().seconds ?? 0 }

    private func loadCurrent() async {
        guard let track = current, let path = streamPath(track) else { return }
        let token = UUID()
        loadToken = token
        isPlaying = false
        progress = 0
        duration = 0
        pendingSeek = nil

        let id = Self.id(track) ?? UUID().uuidString
        let file = Self.cacheDir.appendingPathComponent("\(id).mp3")
        do {
            if !FileManager.default.fileExists(atPath: file.path) {
                try await client.download(to: file, from: path)
            }
            guard token == loadToken else { return }
            let item = AVPlayerItem(url: file)
            let newPlayer = AVPlayer(playerItem: item)
            newPlayer.volume = volume
            if let observer = timeObserver {
                self.player?.removeTimeObserver(observer)
            }
            timeObserver = newPlayer.addPeriodicTimeObserver(
                forInterval: CMTime(seconds: 0.5, preferredTimescale: 600), queue: .main
            ) { [weak self] time in
                Task { @MainActor in
                    guard let self else { return }
                    self.progress = time.seconds
                    if let duration = newPlayer.currentItem?.duration.seconds, duration.isFinite {
                        self.duration = duration
                        if let target = self.pendingSeek, target > 0 {
                            self.pendingSeek = nil
                            self.seek(to: target)
                        }
                    }
                }
            }
            statusObservation = newPlayer.observe(\.timeControlStatus, options: [.new]) { [weak self] player, _ in
                Task { @MainActor in
                    self?.isPlaying = player.timeControlStatus == .playing
                    self?.updateNowPlaying()
                }
            }
            self.player = newPlayer
            updateNowPlaying()
            newPlayer.play()
        } catch {
            isPlaying = false
        }
    }

    private func itemDidFinish() {
        if let id = currentTrackID { Task { await client.reportPlay(id, completed: true) } }
        if repeatMode == 2 {
            seek(to: 0)
            player?.play()
        } else if autoplay && repeatMode == 0 && index >= queue.count - 1,
                  let id = currentTrackID {
            Task { await refillRadio(trackID: id) }
        } else {
            next()
        }
    }

    /// Web/Android behaviour: append at most five unseen tracks only when a
    /// queue ends naturally with repeat off. Manual Next never calls this.
    private func refillRadio(trackID: Int) async {
        guard !radioLoading else { return }
        radioLoading = true
        defer { radioLoading = false }
        do {
            let songs = try await client.radio(trackID)
            let existing = Set(queue.compactMap { Self.id($0) })
            let additions = songs.filter { !existing.contains(Self.id($0) ?? UUID().uuidString) }
            if additions.isEmpty {
                next()
                return
            }
            append(Array(additions.prefix(5)))
            next()
        } catch {
            next()
        }
    }

    // MARK: - sleep timer

    func setSleepTimer(minutes: Int) {
        sleepTimer?.invalidate()
        sleepTimer = nil
        sleepFinishedAt = nil
        sleepMinutes = minutes
        sleepRemaining = minutes * 60
        guard minutes > 0 else { return }
        sleepFinishedAt = Date().addingTimeInterval(Double(minutes * 60))
        sleepTimer = Timer.scheduledTimer(withTimeInterval: 1, repeats: true) { [weak self] _ in
            Task { @MainActor [weak self] in
                guard let self, let end = self.sleepFinishedAt else { return }
                let left = Int(max(0, end.timeIntervalSinceNow))
                self.sleepRemaining = left
                if left <= 0 {
                    self.pausePlayback()
                    self.cancelSleepTimer()
                    self.sleepMinutes = 0
                }
            }
        }
    }

    func cancelSleepTimer() {
        sleepTimer?.invalidate()
        sleepTimer = nil
        sleepFinishedAt = nil
        sleepMinutes = 0
        sleepRemaining = 0
    }

    // MARK: - settings and session restore

    func applySettings(_ values: JSON?) {
        if let value = values?["autoplay"]?.bool { autoplay = value }
        if let value = values?["volume"]?.double { volume = Float(value) }
    }

    func restoreSnapshot() async {
        guard let data = UserDefaults.standard.data(forKey: Self.snapshotKey),
              let snapshot = try? JSONDecoder().decode(QueueSnapshot.self, from: data),
              Date().timeIntervalSince1970 - snapshot.savedAt < 7 * 86400,
              let raw = snapshot.tracks.data(using: .utf8),
              let object = try? JSONSerialization.jsonObject(with: raw),
              let items = object as? [Any],
              !items.isEmpty else { return }
        queue = items.map { JSON($0) }
        index = min(max(snapshot.index, 0), queue.count - 1)
        repeatMode = snapshot.repeatMode
        shuffle = snapshot.shuffle
        autoplay = snapshot.autoplay
        // Positions older than thirty minutes are stale; keep the queue but
        // start the restored track from the beginning.
        let age = Date().timeIntervalSince1970 - snapshot.savedAt
        pendingSeek = age < 30 * 60 ? snapshot.position : nil
        await loadCurrent()
    }

    func persistQueue() {
        let tracks = queue.map { $0.anyValue }
        guard let data = try? JSONSerialization.data(withJSONObject: tracks),
              let text = String(data: data, encoding: .utf8) else { return }
        let snapshot = QueueSnapshot(
            tracks: text,
            index: index,
            position: progress,
            repeatMode: repeatMode,
            shuffle: shuffle,
            autoplay: autoplay,
            savedAt: Date().timeIntervalSince1970
        )
        guard let encoded = try? JSONEncoder().encode(snapshot) else { return }
        UserDefaults.standard.set(encoded, forKey: Self.snapshotKey)
    }

    // MARK: - now playing

    private func updateNowPlaying() {
        guard let track = current else {
            MPNowPlayingInfoCenter.default().nowPlayingInfo = nil
            return
        }
        var info: [String: Any] = [
            MPMediaItemPropertyTitle: currentTitle,
            MPMediaItemPropertyArtist: currentArtist,
            MPNowPlayingInfoPropertyElapsedPlaybackTime: progress,
            MPNowPlayingInfoPropertyPlaybackRate: isPlaying ? 1.0 : 0.0
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
